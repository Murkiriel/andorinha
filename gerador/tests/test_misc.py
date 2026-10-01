"""Itens pequenos: espaço em disco, etapas do generate.py, limpeza da saída anterior, registro da geração."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

GENERATOR_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GENERATOR_DIR))
from andorinha import catalog, config, builder, packing, run_record  # noqa: E402
from andorinha.packing import Package  # noqa: E402

GB = 1_000_000_000


class DiskSpaceTest(unittest.TestCase):
    def test_low_space_stops_immediately(self):
        with self.assertRaises(RuntimeError) as ctx:
            builder.check_disk_space(Path("."), minimum=25 * GB, free=10 * GB)
        self.assertIn("25", str(ctx.exception))

    def test_enough_space_passes(self):
        builder.check_disk_space(Path("."), minimum=25 * GB, free=30 * GB)

    def test_default_minimum_comes_from_config(self):
        self.assertEqual(25 * GB, config.MIN_FREE_DISK_BYTES)


class StagesTest(unittest.TestCase):
    def setUp(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("generate", GENERATOR_DIR / "generate.py")
        self.script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.script)

    def test_from_catalog_does_not_validate(self):
        self.assertFalse(self.script.should_validate("catalog"))

    def test_other_stages_validate(self):
        for stage in ("osm", "tiles", "packages", "validate"):
            self.assertTrue(self.script.should_validate(stage), stage)


class CleanOutputTest(unittest.TestCase):
    def test_removes_previous_packages_and_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            for name in ("andorinha-base.tar.gz", "andorinha-GO.tar.gz", "catalogo.json", "pacotes.json", "outro.txt"):
                (dist / name).write_text("x")
            packing.clean_output(dist)
            self.assertEqual(["outro.txt"], sorted(p.name for p in dist.iterdir()))


class SizeTest(unittest.TestCase):
    def test_size_attribute_and_bytes_key_in_catalog(self):
        p = Package(name="GO", file="andorinha-GO.tar.gz", size=1234, sha256="a" * 64, tiles=1, bytes_tiles=2,
                    bbox=[-20.0, -54.0, -12.0, -45.0], bbox_tiles=[-20.0, -54.0, -12.0, -45.0])
        self.assertFalse(hasattr(p, "bytes"))  # não esconde mais o tipo bytes do Python
        osm = {"timestamp": "2026-09-29T00:59:51Z", "md5": "c" * 32, "url": "u"}
        cat = catalog.build_catalog("2026-09-30-cccccccc", osm, {"base": p, "GO": p}, generator_commit="abc1234")
        self.assertEqual(1234, cat["states"]["GO"]["bytes"])
        self.assertNotIn("size", cat["states"]["GO"])


class ReadmeCompatibilityTest(unittest.TestCase):
    """A seção "Compatibilidade" do README da raiz é o que quem usa os pacotes lê antes de escolher o motor."""

    def setUp(self):
        import re

        readme = (config.REPO / "README.md").read_text(encoding="utf-8")
        self.section = readme.split("## Compatibilidade", 1)[1].split("\n## ", 1)[0]
        self.versions = set(re.findall(r"\b3\.\d+\.\d+\b", self.section))

    def test_says_the_generator_version_and_no_other(self):
        """Trocar VALHALLA_VERSION sem mexer no README deixaria o README mandando usar o motor errado."""
        self.assertEqual({config.VALHALLA_VERSION}, self.versions)

    def test_tells_users_to_check_the_version_of_a_generation(self):
        """O formato do tile muda entre versões: quem lê uma geração de outra versão não consegue rotear."""
        self.assertIn("`valhalla_version`", self.section)
        self.assertIn("recuse", self.section)

    def test_points_to_what_the_next_version_waits_for(self):
        self.assertIn("gerador/PENDENCIAS.md", self.section)


class RunRecorderTest(unittest.TestCase):
    def test_saves_stages_disk_peak_and_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "a.bin").write_bytes(b"x" * 5000)
            recorder = run_record.RunRecorder(folder, interval=0.01)
            with recorder.stage("packages"):
                (folder / "b.bin").write_bytes(b"y" * 7000)
            recorder.save(folder / "geracao.json", "ok")
            data = json.loads((folder / "geracao.json").read_text(encoding="utf-8"))
        self.assertEqual("ok", data["result"])
        self.assertEqual(["packages"], [e["stage"] for e in data["stages"]])
        self.assertGreaterEqual(data["stages"][0]["minutes"], 0)
        self.assertGreaterEqual(data["peak_disk_gb"], 12000 / GB)

    def test_failed_stage_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            recorder = run_record.RunRecorder(Path(tmp), interval=0.01)
            with self.assertRaises(ValueError):
                with recorder.stage("tiles"):
                    raise ValueError("caiu")
            recorder.save(Path(tmp) / "geracao.json", "failed: caiu")
            data = json.loads((Path(tmp) / "geracao.json").read_text(encoding="utf-8"))
        self.assertEqual("failed", data["stages"][0]["status"])
        self.assertEqual("failed: caiu", data["result"])


if __name__ == "__main__":
    unittest.main()
