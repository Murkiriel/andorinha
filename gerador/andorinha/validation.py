"""Confere que os pacotes funcionam como vão ser usados: numa pasta que começa só com a base, extrai as UFs de
cada rota de teste e compara a rota com a do Brasil inteiro. Se faltar tile num pacote, a rota muda ou falha.

O foco é a moto: 30 rotas com o costing `motorcycle`, com a config de quem usa os pacotes (engine.routing_config):
- uma dentro de cada UF (27): da capital a uma cidade da mesma UF, 30 a 150 km, com SÓ base + aquela UF;
- entre UFs vizinhas (GO/DF, SP/RJ);
- uma longa que só tem os pacotes da origem e do destino (Porto Alegre -> Fortaleza: o meio vem só da base).

Os outros perfis que o README promete (carro, bicicleta, a pé) têm uma rota curta cada, com SÓ base + uma UF: o
grafo é o mesmo, e essa rota prova que o perfil também roteia com os pacotes separados.

A base é extraída uma vez. Os pacotes de UF só têm os níveis 1 e 2 e a base só o nível 0, então entre uma rota e
outra basta apagar as pastas 1/ e 2/ para voltar à base pura.
"""
from __future__ import annotations

import gc
import json
import shutil
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from . import engine

# Tolerância entre a rota com os pacotes e a com o Brasil inteiro. A longa, sem as UFs do meio, poderia escolher
# outro caminho pelas rodovias da base (na primeira geração deu a mesma rota); as demais têm de dar a mesma.
DEFAULT_TOLERANCE = 0.001


@dataclass(frozen=True)
class RouteCheck:
    name: str
    points: Tuple[Tuple[float, float], ...]
    packages: Tuple[str, ...]
    tolerance: float = DEFAULT_TOLERANCE
    costing: str = "motorcycle"  # o perfil do Valhalla


def _within_state(state: str, capital: str, city: str, a: Tuple[float, float], b: Tuple[float, float]) -> RouteCheck:
    return RouteCheck(f"{state}: {capital} -> {city}", (a, b), (state,))


# Centro das cidades (lat, lon). O teste de unidade confere que cada ponto cai na UF pela malha do IBGE.
STATE_ROUTES: List[RouteCheck] = [
    _within_state("AC", "Rio Branco", "Senador Guiomard", (-9.9747, -67.8100), (-10.1497, -67.7361)),
    _within_state("AL", "Maceió", "Marechal Deodoro", (-9.6658, -35.7353), (-9.7101, -35.8950)),
    _within_state("AM", "Manaus", "Presidente Figueiredo", (-3.1190, -60.0217), (-2.0480, -60.0240)),
    _within_state("AP", "Macapá", "Santana", (0.0349, -51.0694), (-0.0583, -51.1817)),
    _within_state("BA", "Salvador", "Feira de Santana", (-12.9714, -38.5014), (-12.2664, -38.9663)),
    _within_state("CE", "Fortaleza", "Maranguape", (-3.7319, -38.5267), (-3.8900, -38.6850)),
    _within_state("DF", "Rodoviária", "Aeroporto", (-15.7942, -47.8825), (-15.8697, -47.9208)),
    _within_state("ES", "Vitória", "Guarapari", (-20.3155, -40.3128), (-20.6770, -40.5093)),
    _within_state("GO", "Goiânia", "Anápolis", (-16.6869, -49.2648), (-16.3281, -48.9534)),
    _within_state("MA", "São Luís", "São José de Ribamar", (-2.5307, -44.3068), (-2.5619, -44.0542)),
    _within_state("MG", "Belo Horizonte", "Sete Lagoas", (-19.9167, -43.9345), (-19.4658, -44.2467)),
    _within_state("MS", "Campo Grande", "Sidrolândia", (-20.4697, -54.6201), (-20.9302, -54.9692)),
    _within_state("MT", "Cuiabá", "Chapada dos Guimarães", (-15.6014, -56.0979), (-15.4608, -55.7497)),
    _within_state("PA", "Belém", "Castanhal", (-1.4558, -48.4902), (-1.2939, -47.9261)),
    _within_state("PB", "João Pessoa", "Campina Grande", (-7.1195, -34.8450), (-7.2307, -35.8811)),
    _within_state("PE", "Recife", "Caruaru", (-8.0476, -34.8770), (-8.2760, -35.9819)),
    _within_state("PI", "Teresina", "Altos", (-5.0920, -42.8038), (-5.0379, -42.4613)),
    _within_state("PR", "Curitiba", "Ponta Grossa", (-25.4284, -49.2733), (-25.0950, -50.1619)),
    _within_state("RJ", "Rio de Janeiro", "Petrópolis", (-22.9068, -43.1729), (-22.5050, -43.1789)),
    _within_state("RN", "Natal", "São José de Mipibu", (-5.7945, -35.2110), (-6.0748, -35.2371)),
    _within_state("RO", "Porto Velho", "Candeias do Jamari", (-8.7612, -63.9004), (-8.7907, -63.7005)),
    _within_state("RR", "Boa Vista", "Mucajaí", (2.8235, -60.6758), (2.4399, -60.9097)),
    _within_state("RS", "Porto Alegre", "Novo Hamburgo", (-30.0346, -51.2177), (-29.6783, -51.1309)),
    _within_state("SC", "Florianópolis", "Itajaí", (-27.5954, -48.5480), (-26.9101, -48.6705)),
    _within_state("SE", "Aracaju", "Itabaiana", (-10.9472, -37.0731), (-10.6850, -37.4253)),
    _within_state("SP", "São Paulo", "Campinas", (-23.5505, -46.6333), (-22.9099, -47.0626)),
    _within_state("TO", "Palmas", "Porto Nacional", (-10.2491, -48.3243), (-10.7081, -48.4172)),
]

# Uma rota por perfil além da moto, todas dentro de uma UF só.
PROFILE_ROUTES: List[RouteCheck] = [
    RouteCheck("carro, GO: Goiânia -> Anápolis", ((-16.6869, -49.2648), (-16.3281, -48.9534)), ("GO",),
               costing="auto"),
    RouteCheck("bicicleta, RJ: Centro -> Copacabana", ((-22.9068, -43.1729), (-22.9711, -43.1822)), ("RJ",),
               costing="bicycle"),
    RouteCheck("a pé, SP: Sé -> Avenida Paulista", ((-23.5505, -46.6333), (-23.5614, -46.6559)), ("SP",),
               costing="pedestrian"),
]

ROUTES: List[RouteCheck] = STATE_ROUTES + [
    RouteCheck("Goiânia -> Brasília", ((-16.6869, -49.2648), (-15.7939, -47.8828)), ("GO", "DF")),
    RouteCheck("São Paulo -> Rio de Janeiro", ((-23.5505, -46.6333), (-22.9068, -43.1729)), ("SP", "RJ")),
    RouteCheck("Porto Alegre -> Fortaleza, só origem e destino", ((-30.0346, -51.2177), (-3.7319, -38.5267)),
               ("RS", "CE"), tolerance=0.05),
] + PROFILE_ROUTES


def missing_packages(routes: List[RouteCheck], files: Dict[str, str]) -> List[str]:
    """Um problema por rota que precisa de um pacote que não foi gerado (em vez de um KeyError no meio)."""
    out = []
    for route in routes:
        for name in ("base",) + route.packages:
            if name not in files:
                out.append(f"{route.name}: falta o pacote {name}")
    return out


def request(route: RouteCheck) -> dict:
    """A requisição de rota do Valhalla para uma rota de teste, com o perfil dela."""
    return {"locations": [{"lat": la, "lon": lo} for la, lo in route.points], "costing": route.costing,
            "directions_options": {"units": "kilometers"}}


def _km(tiles_dir: Path, route: RouteCheck) -> float:
    return json.loads(engine.actor(tiles_dir).route(json.dumps(request(route))))["trip"]["summary"]["length"]


def _extract(package: Path, dest: Path) -> None:
    with tarfile.open(package, "r:gz") as tar:
        tar.extractall(dest, filter="data")


def _reset_to_base(folder: Path) -> None:
    # No Windows, o Valhalla mantém os tiles mapeados enquanto o ator existir: solta antes de apagar.
    gc.collect()
    for level in ("1", "2"):
        shutil.rmtree(folder / level, ignore_errors=True)


def validate(brazil_tiles: Path, packages_dir: Path, files: Dict[str, str],
             routes: List[RouteCheck] = ROUTES) -> List[str]:
    """Roda as rotas de teste. Devolve os problemas encontrados (vazio = tudo certo)."""
    problems = missing_packages(routes, files)
    if problems:
        return problems
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="andorinha-validar-") as tmp:
        folder = Path(tmp)
        _extract(packages_dir / files["base"], folder)
        for route in routes:
            try:
                km_brazil = _km(brazil_tiles, route)
            except RuntimeError as e:
                problems.append(f"{route.name}: sem rota nem com o Brasil inteiro ({e})")
                continue
            for name in route.packages:
                _extract(packages_dir / files[name], folder)
            try:
                km_packages = _km(folder, route)
            except RuntimeError as e:
                problems.append(f"{route.name}: sem rota com {('base',) + route.packages} ({e})")
                continue
            finally:
                _reset_to_base(folder)
            difference = abs(km_packages - km_brazil) / km_brazil
            status = "ok" if difference <= route.tolerance else "DIFERENTE"
            print(f"[validar] {status:>9}  {route.name}: {km_packages:.1f} km com os pacotes, "
                  f"{km_brazil:.1f} km com o Brasil")
            if difference > route.tolerance:
                problems.append(f"{route.name}: {km_packages:.1f} km com os pacotes contra "
                                f"{km_brazil:.1f} km com o Brasil")
        gc.collect()
    print(f"[validar] {len(routes)} rotas em {(time.time() - t0) / 60:.1f} min")
    return problems
