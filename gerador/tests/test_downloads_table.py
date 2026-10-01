"""A tabela "Baixar por estado" do README, gerada pelo publish.py a partir do catálogo."""
import sys
import unicodedata
import unittest
from pathlib import Path

GENERATOR_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GENERATOR_DIR))
from andorinha import config, publishing  # noqa: E402


def sample_catalog():
    def package(file, size):
        return {"file": file, "bytes": size, "sha256": "a" * 64, "tiles": 1, "bytes_tiles": 1,
                "bbox": [0, 0, 1, 1], "bbox_tiles": [0, 0, 1, 1]}
    states = {state: {"name": name, **package(f"andorinha-{state}.tar.gz", 10_000_000 + i)}
              for i, (state, name) in enumerate(sorted(config.STATES.items()))}
    return {"build_id": "2026-09-30-cb859dc3", "valhalla_version": "3.6.3",
            "osm": {"timestamp": "2026-09-29T00:59:51Z"},
            "release_url": "https://github.com/Murkiriel/andorinha/releases/download/2026-09-30-cb859dc3/",
            "base": package("andorinha-base.tar.gz", 62_212_390), "states": states}


class TableTest(unittest.TestCase):
    def test_one_row_per_package_with_release_link(self):
        table = publishing.downloads_table(sample_catalog())
        lines = [line for line in table.splitlines() if line.startswith("| ") and "andorinha-" in line]
        self.assertEqual(28, len(lines))
        self.assertIn("(https://github.com/Murkiriel/andorinha/releases/download/2026-09-30-cb859dc3/"
                      "andorinha-GO.tar.gz)", table)

    def test_base_first_then_states_by_name(self):
        lines = [line for line in publishing.downloads_table(sample_catalog()).splitlines() if "andorinha-" in line]
        self.assertIn("andorinha-base.tar.gz", lines[0])
        names = [line.split("|")[1].strip() for line in lines[1:]]
        # Ordem de gente, sem considerar acento: Pará, Paraíba, Paraná (o sorted() puro poria "Pará" depois).
        strip_accents = lambda n: unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()  # noqa: E731
        self.assertEqual(sorted(names, key=strip_accents), names)
        self.assertIn("Acre (AC)", names[0])
        self.assertLess(names.index("Pará (PA)"), names.index("Paraíba (PB)"))

    def test_size_in_mb_and_generation_in_text(self):
        table = publishing.downloads_table(sample_catalog())
        self.assertIn("62,2 MB", table)
        self.assertIn("2026-09-30-cb859dc3", table)
        self.assertIn("2026-09-29", table)
        self.assertIn("3.6.3", table)


class ReadmeTest(unittest.TestCase):
    def test_replaces_only_between_markers(self):
        text = "antes\n<!-- downloads:start -->\nvelho\n<!-- downloads:end -->\ndepois\n"
        updated = publishing.update_readme(text, "TABELA")
        self.assertEqual("antes\n<!-- downloads:start -->\nTABELA\n<!-- downloads:end -->\ndepois\n", updated)
        self.assertEqual(updated, publishing.update_readme(updated, "TABELA"))  # rodar de novo não muda nada

    def test_missing_markers_is_error(self):
        with self.assertRaises(ValueError):
            publishing.update_readme("sem marcadores\n", "TABELA")

    def test_root_readme_has_markers(self):
        text = (config.REPO / "README.md").read_text(encoding="utf-8")
        publishing.update_readme(text, publishing.downloads_table(sample_catalog()))  # não levanta


if __name__ == "__main__":
    unittest.main()
