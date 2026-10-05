"""O catalogo.json: o índice que quem usa os pacotes lê para saber o que baixar, de onde e como conferir.

    {
      "schema": 1,
      "build_id": "2026-09-30-cb859dc3",    data + 8 primeiros do md5 do extrato; ids diferentes não se misturam
      "built_at": "2026-09-30T12:00:00Z",
      "valhalla_version": "3.6.3",          o motor que lê estes tiles tem de ser desta versão
      "generator_commit": "2d3c2f6",        commit do gerador que produziu a geração
      "required_config": {"loki.use_connectivity": false, ...},    ajustes obrigatórios na config de quem usa
      "osm": {"timestamp": ..., "md5": ..., "url": ...},
      "release_url": "https://github.com/Murkiriel/andorinha/releases/download/2026-09-30-cb859dc3/",
      "attribution": "...",
      "timezones": {"release": "2026d", "tzids": [...]},   fusos dentro dos tiles (as zonas do Brasil)
      "base": {"file", "bytes", "sha256", "tiles", "bytes_tiles", "bbox", "bbox_tiles"},
      "states": {"GO": {"name": "Goiás", ...os mesmos campos}, ...}
    }

`bbox` = [lat mín, lon mín, lat máx, lon máx] da área que o pacote atende (polígono da UF no IBGE; o Brasil, na
base), a mesma ordem do catálogo do Pardal; `bbox_tiles` = o dos tiles do pacote (em geral maior; menor onde a
UF não tem via, como ilhas oceânicas).
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from . import config, engine, timezones
from .packing import Package

SCHEMA = 1


def _entry(p: Package) -> dict:
    d = asdict(p)
    d.pop("name")
    d["bytes"] = d.pop("size")
    return d


def timezones_entry() -> dict:
    """De onde vêm os fusos dos tiles: a release do timezone-boundary-builder e as zonas incluídas (as do Brasil).
    Rota com `date_time` só responde com hora e fuso onde o nó tem uma dessas zonas."""
    return {"release": config.TIMEZONE_RELEASE, "tzids": sorted(timezones.BRAZIL_TZIDS)}


def build_id(data: str, extract_md5: str) -> str:
    """'2026-09-30' + md5 do extrato -> '2026-09-30-cb859dc3'. Dois mapas diferentes nunca dão o mesmo id, nem no
    mesmo dia; o mesmo extrato gerado de novo dá (e o publish.py barra release repetida)."""
    return f"{data}-{extract_md5[:8]}"


def git_commit_hash() -> str:
    """Hash curto do commit do repositório, ou 'desconhecido' fora de um checkout do git."""
    try:
        r = subprocess.run(["git", "-C", str(config.REPO), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return "desconhecido"
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "desconhecido"


def build_catalog(build_id: str, osm: Dict[str, object], packages: Dict[str, Package],
                  generator_commit: Optional[str] = None) -> dict:
    return {
        "schema": SCHEMA,
        "build_id": build_id,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "valhalla_version": config.VALHALLA_VERSION,
        "generator_commit": generator_commit or git_commit_hash(),
        "required_config": dict(engine.REQUIRED_CONFIG),
        "osm": {"timestamp": osm["timestamp"], "md5": osm["md5"], "url": osm["url"]},
        "release_url": config.RELEASE_URL.format(tag=build_id),
        "attribution": config.ATTRIBUTION,
        "timezones": timezones_entry(),
        "base": _entry(packages["base"]),
        "states": {state: {"name": config.STATES[state], **_entry(packages[state])}
                   for state in sorted(packages) if state != "base"},
    }


def save(sample_catalog: dict, dest: Path) -> None:
    dest.write_text(json.dumps(sample_catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
