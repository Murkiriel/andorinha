"""Fusos horários nos tiles: o banco que o `valhalla_build_tiles` lê em `mjolnir.timezone`.

Com ele, cada nó do grafo leva o fuso de onde fica, e uma rota pedida com `date_time` (hora de partida ou de chegada)
responde com a hora de cada ponto e o fuso (`time_zone_name`, `time_zone_offset`). Sem ele, a rota sai, mas sem hora
nem fuso. Quem usa os pacotes não precisa de arquivo nenhum a mais: o fuso vai dentro dos tiles.

O banco é o do formato que o Valhalla espera (tabela `tz_world`, coluna `TZID` e geometria `geom` com índice espacial,
num SQLite com SpatiaLite), montado aqui só com as 16 zonas do Brasil, tiradas da release fixada do
timezone-boundary-builder (a mesma fonte do `valhalla_build_timezones`, que monta o banco do mundo inteiro, ~120 MB).
O Brasil inteiro dá poucos MB. Fora das 16 zonas, um nó fica sem fuso (vias de países vizinhos na borda do extrato).

O SpatiaLite vem do `mod_spatialite` do sistema (no Ubuntu do Actions, o pacote `libsqlite3-mod-spatialite`); a
variável ANDORINHA_SPATIALITE aponta outro arquivo (no Windows, o `mod_spatialite.dll` da gaia-gis).
"""
from __future__ import annotations

import json
import os
import sqlite3
import zipfile
from pathlib import Path
from typing import Iterable, List, Tuple, Union

from . import config, net

BRAZIL_TZIDS = frozenset({
    "America/Araguaina", "America/Bahia", "America/Belem", "America/Boa_Vista", "America/Campo_Grande",
    "America/Cuiaba", "America/Eirunepe", "America/Fortaleza", "America/Maceio", "America/Manaus",
    "America/Noronha", "America/Porto_Velho", "America/Recife", "America/Rio_Branco", "America/Santarem",
    "America/Sao_Paulo",
})


def brazil_features(geojson: dict) -> List[Tuple[str, dict]]:
    """[(tzid, geometria GeoJSON)] das zonas do Brasil, na ordem do arquivo."""
    return [(f["properties"]["tzid"], f["geometry"]) for f in geojson["features"]
            if f["properties"].get("tzid") in BRAZIL_TZIDS]


def connect(path: Union[str, Path]) -> sqlite3.Connection:
    """Conexão SQLite com o SpatiaLite carregado."""
    extension = os.environ.get("ANDORINHA_SPATIALITE", "mod_spatialite")
    folder = os.path.dirname(extension)
    if folder:
        os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(folder)
    db = sqlite3.connect(str(path))
    db.enable_load_extension(True)
    db.load_extension(extension)
    return db


def _wkt(geometry: Union[str, dict]) -> str:
    if isinstance(geometry, str):
        return geometry
    from shapely.geometry import shape
    return shape(geometry).wkt


def write_db(features: Iterable[Tuple[str, Union[str, dict]]], dest: Path) -> Path:
    """Grava o banco `tz_world` em `dest` (apaga o que houver): (tzid, geometria em WKT ou GeoJSON)."""
    if dest.exists():
        dest.unlink()
    db = connect(dest)
    try:
        db.execute("SELECT InitSpatialMetadata(1)")
        db.execute("CREATE TABLE tz_world (PK_UID INTEGER PRIMARY KEY AUTOINCREMENT, TZID TEXT)")
        db.execute("SELECT AddGeometryColumn('tz_world', 'geom', 4326, 'MULTIPOLYGON', 'XY')")
        db.executemany("INSERT INTO tz_world (TZID, geom) VALUES (?, CastToMultiPolygon(GeomFromText(?, 4326)))",
                       [(tzid, _wkt(geometry)) for tzid, geometry in features])
        db.execute("SELECT CreateSpatialIndex('tz_world', 'geom')")
        db.commit()
    finally:
        db.close()
    return dest


def build(dest: Path) -> Path:
    """Baixa (uma vez por release) as zonas do timezone-boundary-builder e grava o banco só do Brasil em `dest`."""
    url = config.TIMEZONE_URL.format(release=config.TIMEZONE_RELEASE)
    archive = config.RAW / f"timezones-with-oceans-{config.TIMEZONE_RELEASE}.geojson.zip"
    if not archive.exists():
        config.RAW.mkdir(parents=True, exist_ok=True)
        net.download(url, archive)
    with zipfile.ZipFile(archive) as z:
        name = next(n for n in z.namelist() if n.endswith((".json", ".geojson")))
        features = brazil_features(json.loads(z.read(name)))
    if {tzid for tzid, _ in features} != BRAZIL_TZIDS:
        raise RuntimeError(f"zonas do Brasil faltando em {url}: {sorted(BRAZIL_TZIDS - {t for t, _ in features})}")
    write_db(features, dest)
    print(f"[fusos] {len(features)} zonas do Brasil ({config.TIMEZONE_RELEASE}) -> {dest.name}, "
          f"{dest.stat().st_size / 1e6:.1f} MB")
    return dest
