"""Contrato do catalogo.json. Mudar uma chave aqui quebra quem consome os pacotes."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

GENERATOR_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GENERATOR_DIR))
from andorinha import catalog, config, engine  # noqa: E402
from andorinha.packing import Package, polygon_bbox  # noqa: E402

TOP_LEVEL_KEYS = {"schema", "build_id", "built_at", "valhalla_version", "generator_commit", "required_config", "osm",
                  "release_url", "attribution", "timezones", "base", "states"}
PACKAGE_KEYS = {"file", "bytes", "sha256", "tiles", "bytes_tiles", "bbox", "bbox_tiles"}
MD5 = "cb859dc31c5fb8459735f0cd273d2c4f"
OSM = {"path": "brazil-latest.osm.pbf", "url": "https://exemplo/brazil-latest.osm.pbf",
       "timestamp": "2026-09-29T00:59:51Z", "md5": MD5, "size": 123}


def package(name, bbox, bbox_tiles):
    return Package(name=name, file=f"andorinha-{name}.tar.zst", size=1000, sha256="a" * 64, tiles=10,
                   bytes_tiles=3000, bbox=bbox, bbox_tiles=bbox_tiles)


def fake_catalog():
    packages = {"base": package("base", [-33.75, -73.99, 5.27, -34.79], [-36.0, -76.0, 8.0, -32.0]),
                "DF": package("DF", [-16.05, -48.29, -15.5, -47.31], [-17.0, -49.0, -15.0, -47.0]),
                "GO": package("GO", [-19.5, -53.25, -12.4, -45.91], [-20.0, -54.0, -12.0, -45.0])}
    build_id = catalog.build_id("2026-09-30", MD5)
    return catalog.build_catalog(build_id, OSM, packages, generator_commit="abc1234")


def readme_keys():
    """(chaves de topo, chaves de pacote) listadas no bloco de código da seção `catalogo.json` do README da raiz."""
    text = (GENERATOR_DIR.parent / "README.md").read_text(encoding="utf-8")
    section = text.split("## `catalogo.json`", 1)[1]
    chunk = section.split("```", 2)[1]
    top_level, package_keys_ = set(), set()
    for line in chunk.splitlines():
        m = re.match(r"^( *)([a-z_0-9]+)\s", line + " ")
        if m:
            (package_keys_ if m.group(1) else top_level).add(m.group(2))
    return top_level, package_keys_


class ContractTest(unittest.TestCase):
    def test_top_level_keys(self):
        self.assertEqual(TOP_LEVEL_KEYS, set(fake_catalog()))

    def test_keys_of_each_package(self):
        cat = fake_catalog()
        self.assertEqual(PACKAGE_KEYS, set(cat["base"]))
        for state, entry in cat["states"].items():
            self.assertEqual(PACKAGE_KEYS | {"name"}, set(entry), state)
            self.assertEqual(config.STATES[state], entry["name"])

    def test_types(self):
        cat = fake_catalog()
        self.assertIsInstance(cat["schema"], int)
        for key in ("build_id", "built_at", "valhalla_version", "generator_commit", "release_url", "attribution"):
            self.assertIsInstance(cat[key], str, key)
        self.assertEqual({"timestamp", "md5", "url"}, set(cat["osm"]))
        for entry in [cat["base"], *cat["states"].values()]:
            for key in ("bytes", "tiles", "bytes_tiles"):
                self.assertIsInstance(entry[key], int)
            for key in ("bbox", "bbox_tiles"):
                self.assertEqual(4, len(entry[key]))
            # Desde 2026-10-05 o pacote é só o .tar.zst (houve uma geração com os dois e a chave `zstd`).
            self.assertTrue(entry["file"].endswith(".tar.zst"))

    def test_build_id_has_date_and_extract_md5(self):
        self.assertEqual("2026-09-30-cb859dc3", catalog.build_id("2026-09-30", MD5))
        self.assertRegex(fake_catalog()["build_id"], r"^\d{4}-\d{2}-\d{2}-[0-9a-f]{8}$")
        # Mesmo dia, outro extrato: outro id (pacotes das duas gerações não podem se misturar).
        self.assertNotEqual(catalog.build_id("2026-09-30", MD5), catalog.build_id("2026-09-30", "f" * 32))

    def test_release_url_uses_build_id(self):
        cat = fake_catalog()
        self.assertTrue(cat["release_url"].endswith(f"/releases/download/{cat['build_id']}/"))

    def test_required_config_matches_validation(self):
        cat = fake_catalog()
        self.assertEqual(engine.REQUIRED_CONFIG, cat["required_config"])
        self.assertIs(False, cat["required_config"]["loki.use_connectivity"])
        self.assertEqual(5_000_000, cat["required_config"]["service_limits.motorcycle.max_distance"])

    def test_well_formed_rectangles(self):
        # Não vale "bbox dentro de bbox_tiles": nos dados reais, onde a UF não tem via não há tile (ilha da Trindade
        # no ES e na base, extremo norte de AP, PA e RR), e o bbox da UF passa do dos tiles.
        cat = fake_catalog()
        for entry in [cat["base"], *cat["states"].values()]:
            for key in ("bbox", "bbox_tiles"):
                s, w, n, e = entry[key]
                self.assertTrue(-90 <= s < n <= 90 and -180 <= w < e <= 180, (key, entry[key]))

    def test_generator_commit_from_checkout(self):
        self.assertRegex(catalog.git_commit_hash(), r"^([0-9a-f]{7,}|desconhecido)$")

    def test_save_and_load_roundtrip(self):
        cat = fake_catalog()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "catalogo.json"
            catalog.save(cat, dest)
            self.assertEqual(cat, json.loads(dest.read_text(encoding="utf-8")))

    def test_readme_documents_all_keys(self):
        top_level, package_keys_ = readme_keys()
        self.assertEqual(TOP_LEVEL_KEYS, top_level)
        self.assertEqual(PACKAGE_KEYS | {"name"}, package_keys_)


class BboxTest(unittest.TestCase):
    def test_polygon_bbox_in_pardal_order(self):
        try:
            from shapely.geometry import box
        except ImportError:
            self.skipTest("shapely não instalado")
        # box(lon mín, lat mín, lon máx, lat máx) -> [lat mín, lon mín, lat máx, lon máx], 2 casas ARREDONDADAS PARA
        # FORA: o retângulo nunca fica menor que o polígono, então um ponto na borda da UF nunca fica fora do bbox dela.
        self.assertEqual([-16.06, -48.29, -15.49, -47.3], polygon_bbox(box(-48.2861, -16.0502, -47.3079, -15.4999)))


if __name__ == "__main__":
    unittest.main()
