"""Roda o Valhalla sobre o extrato: banco de fronteiras e tiles (a config e os executáveis vêm de engine.py)."""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from . import config, engine


def check_disk_space(folder: Path, minimum: int = config.MIN_FREE_DISK_BYTES, free: Optional[int] = None) -> None:
    """Para na hora se a unidade de `folder` não tem `minimum` bytes livres (`free` injetável nos testes)."""
    if free is None:
        folder.mkdir(parents=True, exist_ok=True)
        free = shutil.disk_usage(folder).free
    if free < minimum:
        raise RuntimeError(f"só {free / 1e9:.1f} GB livres na unidade de {folder}; o build precisa de "
                           f"{minimum / 1e9:.0f} GB (extrato, intermediários do Valhalla, tiles e pacotes)")


def build(pbf: Path) -> Path:
    """Gera data/build/valhalla_tiles/ do zero e devolve a pasta. Logs em data/build/*.log."""
    check_disk_space(config.DATA)
    bin_dir, env = engine.executables()
    config.BUILD.mkdir(parents=True, exist_ok=True)
    tiles_dir = config.BUILD / "valhalla_tiles"
    if tiles_dir.exists():
        shutil.rmtree(tiles_dir)
    tiles_dir.mkdir()
    admins = config.BUILD / "admins.sqlite"
    if admins.exists():
        admins.unlink()
    config_file = config.BUILD / "valhalla_build.json"
    config_file.write_text(json.dumps(engine.config_build(tiles_dir, admins), indent=2))

    for name, extra in (("valhalla_build_admins", []), ("valhalla_build_tiles", ["-j", str(config.THREADS)])):
        t0 = time.time()
        log = config.BUILD / f"{name}.log"
        print(f"[valhalla] {name}... (log em {log.name})")
        with open(log, "w", encoding="utf-8") as f:
            r = subprocess.run([engine.exe(bin_dir, name), "-c", str(config_file), *extra, str(pbf)],
                               env=env, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            raise RuntimeError(f"{name} saiu com código {r.returncode:#x}; veja {log}")
        print(f"[valhalla] {name}: {(time.time() - t0) / 60:.1f} min")
    return tiles_dir
