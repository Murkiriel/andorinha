import sys
import tempfile
import unittest
from pathlib import Path

GENERATOR_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GENERATOR_DIR))
if (GENERATOR_DIR / ".pylib").exists():
    sys.path.insert(0, str(GENERATOR_DIR / ".pylib"))
from andorinha import config, engine  # noqa: E402


class VersionTest(unittest.TestCase):
    def test_pinned_version_passes(self):
        engine.check_version(config.VALHALLA_VERSION)
        engine.check_version(config.VALHALLA_VERSION + ".post1")  # sufixo de empacotamento do PyPI

    def test_other_version_is_rejected(self):
        with self.assertRaises(RuntimeError) as ctx:
            engine.check_version("3.8.3")
        self.assertIn(config.VALHALLA_VERSION, str(ctx.exception))

    def test_unknown_version_is_rejected(self):
        with self.assertRaises(RuntimeError):
            engine.check_version("?")

    def test_similar_version_does_not_pass(self):
        # "3.6.30" começa com "3.6.3", mas é outra versão.
        with self.assertRaises(RuntimeError):
            engine.check_version(config.VALHALLA_VERSION + "0")


class RoutingConfigTest(unittest.TestCase):
    def test_config_for_package_users(self):
        with tempfile.TemporaryDirectory() as tmp:  # o get_config do pyvalhalla exige que a pasta exista
            folder = Path(tmp) / "tiles"
            folder.mkdir()
            try:
                cfg = engine.routing_config(folder)
            except ImportError:
                self.skipTest("pyvalhalla não instalado")
        self.assertIs(False, cfg["loki"]["use_connectivity"])
        self.assertEqual(5_000_000, cfg["service_limits"]["motorcycle"]["max_distance"])
        self.assertEqual("", cfg["mjolnir"]["tile_extract"])
        self.assertTrue(cfg["mjolnir"]["tile_dir"].endswith("tiles"))


if __name__ == "__main__":
    unittest.main()
