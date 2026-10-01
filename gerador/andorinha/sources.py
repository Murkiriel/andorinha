"""Downloads: o extrato do Brasil no OpenStreetMap e a malha das UFs do IBGE.

O extrato só é baixado de novo quando o openstreetmap.fr tem versão mais nova (md5 publicado ao lado do arquivo);
depois do download, o md5 é conferido. A Geofabrik não é usada: a partir de algumas redes o download dela entra em
redirecionamento sem fim, e ela só recorta o Brasil por macrorregião.

O openstreetmap.fr troca o extrato uma vez por dia (por volta de 01:00 UTC). Se a troca acontece durante o download
(~25 min), o arquivo baixado é o novo e o md5 lido antes é o velho: nesse caso o md5 e a data são lidos de novo e, se
mudaram, a versão nova é baixada uma vez. Se não mudaram, o arquivo veio corrompido e a geração para.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from . import config, net
from .util import file_hash

# Espera base entre tentativas, em segundos (multiplicada pelo número da tentativa). Os testes zeram.
RETRY_DELAY = 10


def _published() -> Tuple[str, str]:
    """(timestamp, md5) do extrato publicado agora."""
    state = dict(line.split("=", 1) for line in net.fetch_text(config.OSM_STATE_URL, delay=RETRY_DELAY).splitlines()
                 if "=" in line)
    timestamp = state["timestamp"].replace("\\:", ":")
    md5 = net.fetch_text(config.OSM_MD5_URL, delay=RETRY_DELAY).split()[0]
    return timestamp, md5


def _local_matches(pbf: Path, local_meta: Path, md5: str) -> bool:
    """O extrato local é o publicado? Confia no .meta.json só se o tamanho também bater; senão confere pelo md5."""
    if not pbf.exists():
        return False
    if local_meta.exists():
        meta = json.loads(local_meta.read_text(encoding="utf-8"))
        if meta.get("md5") == md5 and meta.get("size") == pbf.stat().st_size:
            return True
    return file_hash(pbf, "md5") == md5  # extrato copiado à mão, meta antigo ou arquivo mexido


def osm_extract() -> Dict[str, object]:
    """Garante data/raw/brazil-latest.osm.pbf na versão mais nova. Devolve {path, url, timestamp, md5, size}."""
    config.RAW.mkdir(parents=True, exist_ok=True)
    pbf = config.RAW / "brazil-latest.osm.pbf"
    local_meta = config.RAW / "brazil-latest.meta.json"

    timestamp, md5 = _published()
    if _local_matches(pbf, local_meta, md5):
        print(f"[osm] extrato local já é o mais novo ({timestamp})")
    else:
        for attempt in (1, 2):
            print(f"[osm] baixando o extrato de {timestamp}...")
            net.download(config.OSM_PBF_URL, pbf, identity=md5, delay=RETRY_DELAY)
            local = file_hash(pbf, "md5")
            if local == md5:
                break
            timestamp_now, md5_now = _published()
            if attempt == 1 and md5_now != md5:
                print(f"[osm] o extrato foi atualizado durante o download ({timestamp_now}); baixando a versão nova")
                timestamp, md5 = timestamp_now, md5_now
                continue
            pbf.unlink()
            raise RuntimeError(f"md5 do extrato não confere: {local} != {md5_now} publicado")
        print(f"[osm] {pbf.stat().st_size / 1e9:.2f} GB, md5 confere")
    meta = {"path": str(pbf), "url": config.OSM_PBF_URL, "timestamp": timestamp, "md5": md5,
            "size": pbf.stat().st_size}
    local_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def mesh_problem(path: Path) -> Optional[str]:
    """O que há de errado com o arquivo da malha das UFs, ou None se é um GeoJSON com as 27 UFs.

    Uma API pode responder 200 com uma página de erro; sem esta conferência ela seria gravada e quebraria todas as
    gerações seguintes até alguém apagar o arquivo à mão."""
    try:
        gj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return f"não é JSON ({e.__class__.__name__})"
    features = gj.get("features") if isinstance(gj, dict) else None
    if not isinstance(features, list):
        return "sem a lista `features`"
    codes = {str((f.get("properties") or {}).get("codarea")) for f in features if isinstance(f, dict)}
    missing = sorted(state for code, state in config.IBGE_STATE_CODES.items() if code not in codes)
    return f"faltam as UFs {', '.join(missing)}" if missing else None


def ibge_mesh() -> Path:
    """Garante data/raw/ibge_malha_uf.json (GeoJSON das 27 UFs, código IBGE em `codarea`), sempre conferido."""
    config.RAW.mkdir(parents=True, exist_ok=True)
    dest = config.RAW / "ibge_malha_uf.json"
    if dest.exists():
        problem = mesh_problem(dest)
        if problem is None:
            return dest
        print(f"[ibge] malha guardada inválida ({problem}); baixando de novo")
        dest.unlink()
    updated = dest.with_name(dest.name + ".novo")
    print("[ibge] baixando a malha das UFs...")
    net.download(config.IBGE_MESH_URL, updated, delay=RETRY_DELAY)
    problem = mesh_problem(updated)
    if problem is not None:
        updated.unlink()
        raise RuntimeError(f"a malha do IBGE veio inválida ({problem}): {config.IBGE_MESH_URL}")
    updated.replace(dest)
    return dest
