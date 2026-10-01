"""Divide os tiles do Brasil em pacotes: um pacote base com as rodovias e um por UF com o resto.

- **base**: todos os tiles do nível 0 (motorway, trunk, primary). É pequeno e permite rotas longas entre estados
  mesmo sem os pacotes das UFs do meio do caminho: longe da origem e do destino, o Valhalla só usa esse nível.
- **UF**: os tiles dos níveis 1 e 2 que tocam o polígono da UF (com a margem de config.MARGEM_UF_GRAUS). Tile na
  divisa entra nas duas UFs; o arquivo é o mesmo nos dois pacotes.

Os tiles de um pacote apontam para os dos vizinhos, então todos os pacotes instalados juntos precisam ser da mesma
geração (o `build_id` do catálogo). Cada pacote é um .tar.gz com os caminhos relativos à pasta de tiles: basta
extrair todos na mesma pasta e apontar o `mjolnir.tile_dir` do Valhalla para ela.
"""
from __future__ import annotations

import gzip
import io
import json
import math
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import config
from .tiles import Tile, list_tiles
from .util import file_hash


def state_polygons(mesh: Path) -> Dict[str, object]:
    """{UF: geometria shapely} da malha do IBGE."""
    from shapely.geometry import shape

    gj = json.loads(mesh.read_text(encoding="utf-8"))
    out = {}
    for ft in gj["features"]:
        state = config.IBGE_STATE_CODES.get(str(ft["properties"].get("codarea")))
        if state:
            out[state] = shape(ft["geometry"])
    missing = set(config.STATES) - set(out)
    if missing:
        raise RuntimeError(f"malha do IBGE sem as UFs {sorted(missing)}")
    return out


def distribute(tiles: List[Tile], polygons: Dict[str, object],
               margin: float) -> Tuple[Dict[str, List[Tile]], List[Tile]]:
    """({'base': [...], 'GO': [...], ...}, tiles que não tocam nenhuma UF). O nível 0 vai inteiro para a base."""
    from shapely.geometry import box
    from shapely.prepared import prep

    areas = {state: prep(geom.buffer(margin)) for state, geom in polygons.items()}
    packages: Dict[str, List[Tile]] = {"base": []}
    outside: List[Tile] = []
    for t in tiles:
        if t.level == 0:
            packages["base"].append(t)
            continue
        square = box(*t.bbox())
        states = [state for state, area in areas.items() if area.intersects(square)]
        if not states:
            outside.append(t)
        for state in states:
            packages.setdefault(state, []).append(t)
    return packages, outside


@dataclass
class Package:
    """Retângulos em [lat mín, lon mín, lat máx, lon máx], a ordem do catálogo do Pardal.

    `bbox`: o da área que o pacote atende (o polígono da UF no IBGE; o Brasil, na base): é o que se usa para
    escolher o que baixar. `bbox_tiles`: o dos tiles do pacote. Em geral é maior (os tiles de 1° e 4° passam da
    divisa), mas não sempre: onde a UF não tem via, não há tile (a ilha da Trindade estende o bbox do ES e o da base
    até -29,29 de longitude; o extremo norte de AP, PA e RR também fica além dos tiles)."""
    name: str
    file: str
    size: int  # bytes do .tar.gz (no catálogo, a chave continua `bytes`)
    sha256: str
    tiles: int
    bytes_tiles: int
    bbox: List[float] = field(default_factory=list)
    bbox_tiles: List[float] = field(default_factory=list)


def _bbox_tiles(tiles: List[Tile]) -> List[float]:
    boxes = [t.bbox() for t in tiles]
    return [round(min(c[1] for c in boxes), 2), round(min(c[0] for c in boxes), 2),
            round(max(c[3] for c in boxes), 2), round(max(c[2] for c in boxes), 2)]


def polygon_bbox(geometry) -> List[float]:
    """Retângulo de uma geometria shapely, arredondado para fora em 2 casas (nunca menor que a geometria)."""
    lon0, lat0, lon1, lat1 = geometry.bounds
    return [math.floor(lat0 * 100) / 100, math.floor(lon0 * 100) / 100,
            math.ceil(lat1 * 100) / 100, math.ceil(lon1 * 100) / 100]


def write_package(name: str, tiles: List[Tile], tiles_dir: Path, dest: Path,
                  bbox: Optional[List[float]] = None) -> Package:
    """Grava o .tar.gz de um pacote, de forma reproduzível (ordem fixa, datas zeradas): o mesmo conjunto de tiles
    gera sempre o mesmo arquivo, byte a byte (o gzip não guarda nome nem data)."""
    tiles = sorted(tiles)
    bytes_tiles = 0
    with open(dest, "wb") as raw_file:
        with gzip.GzipFile(filename="", fileobj=raw_file, mode="wb", compresslevel=6, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w", format=tarfile.USTAR_FORMAT) as tar:
                for t in tiles:
                    data = (tiles_dir / t.path()).read_bytes()
                    bytes_tiles += len(data)
                    info = tarfile.TarInfo(t.path())
                    info.size = len(data)
                    info.mtime = 0
                    info.mode = 0o644
                    tar.addfile(info, io.BytesIO(data))
    tiles_box = _bbox_tiles(tiles)
    return Package(name, dest.name, dest.stat().st_size, file_hash(dest), len(tiles), bytes_tiles,
                   bbox if bbox is not None else tiles_box, tiles_box)


def clean_output(output: Path) -> None:
    """Apaga os pacotes, o pacotes.json e o catalogo.json da geração anterior: nada dela fica misturado com a nova."""
    for old in [*output.glob("andorinha-*.tar.gz"), output / "pacotes.json", output / "catalogo.json"]:
        if old.exists():
            old.unlink()


def generate(tiles_dir: Path, mesh: Path, output: Path) -> Dict[str, Package]:
    """Divide e grava todos os pacotes em `output`. Falha se algum passar do limite do GitHub Releases."""
    output.mkdir(parents=True, exist_ok=True)
    from shapely.ops import unary_union

    tiles = [t for t, _ in list_tiles(tiles_dir)]
    polygons = state_polygons(mesh)
    packages, outside = distribute(tiles, polygons, config.STATE_MARGIN_DEG)
    boxes = {state: polygon_bbox(geom) for state, geom in polygons.items()}
    boxes["base"] = polygon_bbox(unary_union(list(polygons.values())))
    if outside:
        # Sobra do recorte do extrato além da margem (vias de países vizinhos, ilhas oceânicas fora da malha).
        print(f"[pacotes] {len(outside)} tiles fora de todas as UFs ficam de fora (ex.: {outside[0].path()})")
    out: Dict[str, Package] = {}
    for name in ["base"] + sorted(k for k in packages if k != "base"):
        p = write_package(name, packages[name], tiles_dir, output / f"andorinha-{name}.tar.gz", boxes[name])
        if p.size >= config.MAX_ASSET_BYTES:
            raise RuntimeError(f"pacote {name} tem {p.size / 1e9:.2f} GB, acima do limite do GitHub Releases")
        print(f"[pacotes] {name:>4}: {p.tiles:5d} tiles, {p.bytes_tiles / 1e6:7.1f} MB -> {p.size / 1e6:7.1f} MB")
        out[name] = p
    return out
