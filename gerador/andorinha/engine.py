"""O Valhalla (pacote pyvalhalla): o único módulo que o importa.

Toda importação confere a versão contra config.VALHALLA_VERSION, porque o formato do tile muda entre versões: gerar
ou validar com outra versão daria pacotes que o motor de quem os usa não lê, ou uma validação que não prova nada.

Duas configs:
- `config_build`: a do `valhalla_build_tiles` (o que entra no grafo).
- `routing_config`: a de quem USA os pacotes, com os dois ajustes que eles exigem. A validação roteia com ela, e o
  README manda quem usa os pacotes fazer o mesmo.

Os executáveis do pyvalhalla são chamados direto, com as bibliotecas do pacote no PATH: há distribuições do Python
para Windows que ignoram PYTHONPATH, e o `python -m valhalla` do pacote não acharia o módulo.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Tuple

from . import config

# Maior rota de moto aceita, em metros. O padrão do Valhalla recusa rota de moto acima de 500 km.
MAX_MOTORCYCLE_DISTANCE_M = 5_000_000

# Ajustes obrigatórios na config do Valhalla de quem roteia sobre os pacotes (chave pontuada -> valor). Fonte única:
# `routing_config` aplica exatamente isto, e o catálogo publica isto em `required_config` para quem usa os pacotes.
# - loki.use_connectivity: a checagem prévia de conectividade olha só as vias locais (nível 2); sem os estados do
#   meio do caminho, declara origem e destino "em regiões desconectadas" e nem tenta a rota. Desligada, base + RS + CE
#   dá exatamente a rota de Porto Alegre a Fortaleza do Brasil inteiro (4.242 km).
# - service_limits.motorcycle.max_distance: viagem de moto passa de 500 km.
REQUIRED_CONFIG = {
    "loki.use_connectivity": False,
    "service_limits.motorcycle.max_distance": MAX_MOTORCYCLE_DISTANCE_M,
}


def check_version(version: str) -> None:
    """Recusa qualquer versão que não seja config.VALHALLA_VERSION (aceita sufixo de empacotamento, ex. '.post1')."""
    pinned = config.VALHALLA_VERSION
    if version != pinned and not version.startswith(pinned + ".post"):
        raise RuntimeError(f"pyvalhalla {version} instalado, mas o gerador está fixado em {pinned}: "
                           f"pip install pyvalhalla=={pinned}")


def import_valhalla():
    """O módulo `valhalla`, já com a versão conferida."""
    import valhalla

    check_version(str(getattr(valhalla, "__version__", "?")))
    return valhalla


def executables() -> Tuple[Path, Dict[str, str]]:
    """(pasta dos executáveis, ambiente com as bibliotecas do pacote no PATH)."""
    package = Path(import_valhalla().__file__).resolve().parent
    env = dict(os.environ)
    libs = package.parent / "pyvalhalla.libs"
    if libs.exists():
        env["PATH"] = str(libs) + os.pathsep + env.get("PATH", "")
    return package / "bin", env


def exe(bin_dir: Path, name: str) -> str:
    for candidate in (bin_dir / name, bin_dir / (name + ".exe")):
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(f"{name} não encontrado em {bin_dir}")


def config_build(tiles_dir: Path, admins: Path) -> dict:
    """A config do build. Sem trânsito, fusos horários, transporte público e pontos de referência: o pacote é só o
    grafo de rotas. Sem `default_speeds_config`: as velocidades vêm do `maxspeed` do OSM e das regras por tipo de via
    do próprio Valhalla (uma tabela de velocidades por densidade deixou a cidade com metade da velocidade real num
    teste no DF, ver gerador/README.md)."""
    cfg = import_valhalla().get_config(tile_extract="", tile_dir=str(tiles_dir), verbose=True)
    cfg["mjolnir"].update(traffic_extract="", timezone="", transit_dir="", landmarks="", admin=str(admins),
                          concurrency=config.THREADS)
    return cfg


def routing_config(tiles_dir: Path) -> dict:
    """A config de quem roteia sobre uma pasta com pacotes extraídos (base + UFs)."""
    cfg = import_valhalla().get_config(tile_extract="", tile_dir=str(tiles_dir))
    cfg["mjolnir"]["traffic_extract"] = ""
    for key, value in REQUIRED_CONFIG.items():
        *path, last = key.split(".")
        target = cfg
        for part in path:
            target = target[part]
        target[last] = value
    return cfg


def actor(tiles_dir: Path):
    """Um `valhalla.Actor` pronto para rotear sobre a pasta, com `routing_config`."""
    return import_valhalla().Actor(routing_config(tiles_dir))
