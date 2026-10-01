"""Gera uma geração completa do Andorinha em data/dist/: pacotes .tar.gz e catalogo.json.

    python generate.py                      # tudo: extrato, tiles, pacotes, validação e catálogo
    python generate.py --from packages      # reaproveita os tiles de data/build/ (ex.: depois de mudar a divisão)
    python generate.py --from validate      # só valida e remonta o catálogo sobre os pacotes já gerados

Etapas, em ordem: osm (baixa o extrato se houver versão nova), tiles (Valhalla), packages (divide por UF),
validate (rotas de teste com os pacotes), catalog. Depois, `python scripts/publish.py` publica.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# Pythons sem venv (ex.: a distribuição "embeddable" do Windows) podem instalar as dependências com
# `pip install --target .pylib -r requirements.txt`; esta pasta entra no caminho de import se existir.
if (HERE / ".pylib").exists():
    sys.path.insert(0, str(HERE / ".pylib"))

from andorinha import sources, catalog, config, builder, packing, run_record, validation  # noqa: E402
from andorinha.packing import Package  # noqa: E402

STAGES = ["osm", "tiles", "packages", "validate", "catalog"]


def should_validate(from_stage: str) -> bool:
    """`--from catalog` só remonta o catálogo sobre pacotes já validados; as demais etapas validam."""
    return STAGES.index(from_stage) <= STAGES.index("validate")


def _utf8_output() -> None:
    # Log redirecionado para arquivo sai na codificação do Windows (cp1252) e os acentos quebram; UTF-8 sempre.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _generate(from_stage: str, recorder: run_record.RunRecorder) -> str:
    start = STAGES.index(from_stage)
    osm_meta_file = config.RAW / "brazil-latest.meta.json"
    with recorder.stage("osm"):
        osm = sources.osm_extract() if start <= 0 else json.loads(osm_meta_file.read_text(encoding="utf-8"))
    with recorder.stage("tiles"):
        tiles_dir = builder.build(Path(osm["path"])) if start <= 1 else config.BUILD / "valhalla_tiles"

    packages_file = config.DIST / "pacotes.json"
    with recorder.stage("packages"):
        if start <= 2:
            packing.clean_output(config.DIST)
            generated = packing.generate(tiles_dir, sources.ibge_mesh(), config.DIST)
            packages_file.write_text(json.dumps({k: vars(v) for k, v in generated.items()}, indent=2), encoding="utf-8")
        else:
            generated = {k: Package(**v) for k, v in json.loads(packages_file.read_text(encoding="utf-8")).items()}

    if should_validate(from_stage):
        with recorder.stage("validate"):
            problems = validation.validate(tiles_dir, config.DIST, {k: p.file for k, p in generated.items()})
        if problems:
            print("\n[gerar] A VALIDAÇÃO FALHOU; o catálogo não foi montado:")
            for p in problems:
                print("  -", p)
            raise SystemExit(1)
    else:
        print("[gerar] AVISO: --from catalog não valida os pacotes; o catálogo sai sobre a validação anterior")

    with recorder.stage("catalog"):
        build_id = catalog.build_id(datetime.now(timezone.utc).strftime("%Y-%m-%d"), osm["md5"])
        cat = catalog.build_catalog(build_id, osm, generated)
        catalog.save(cat, config.DIST / "catalogo.json")
    total = sum(p.size for p in generated.values())
    return f"geração {build_id}: {len(generated)} pacotes, {total / 1e9:.2f} GB compactados"


def main() -> None:
    _utf8_output()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="from_stage", choices=STAGES, default="osm",
                    help="começa nesta etapa, reaproveitando as anteriores")
    args = ap.parse_args()

    config.DIST.mkdir(parents=True, exist_ok=True)
    marker = config.DIST / config.IN_PROGRESS_MARKER
    marker.write_text(datetime.now(timezone.utc).isoformat())
    recorder = run_record.RunRecorder(config.DATA)
    result = "failed"
    try:
        summary = _generate(args.from_stage, recorder)
        result = "ok"
    except SystemExit:
        result = "failed: validation"
        raise
    except BaseException as e:
        result = f"failed: {e.__class__.__name__}: {e}"
        raise
    finally:
        recorder.save(config.DIST / "geracao.json", result)
    minutes = sum(e["minutes"] for e in recorder.stages)
    print(f"\n[gerar] {summary}, em {minutes:.1f} min; pico de disco em data/: {recorder.peak / 1e9:.1f} GB "
          f"(detalhes em data/dist/geracao.json)")
    marker.unlink()


if __name__ == "__main__":
    main()
