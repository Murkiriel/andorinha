import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from andorinha.publishing import drops  # noqa: E402
from andorinha import config, publishing  # noqa: E402


def cat(base=64, **states):
    return {"base": {"tiles": base}, "states": {state: {"tiles": n} for state, n in states.items()}}


class DropsTest(unittest.TestCase):
    def test_no_change(self):
        self.assertEqual([], drops(cat(GO=605, DF=23), cat(GO=605, DF=23)))

    def test_small_variation_passes(self):
        self.assertEqual([], drops(cat(GO=605), cat(GO=590)))

    def test_large_drop_blocks(self):
        self.assertEqual(["GO: 605 -> 500 tiles"], drops(cat(GO=605), cat(GO=500)))

    def test_missing_state_blocks(self):
        self.assertEqual(["DF: sumiu do catálogo"], drops(cat(GO=605, DF=23), cat(GO=605)))

    def test_base_also_counts(self):
        self.assertEqual(["base: 64 -> 40 tiles"], drops(cat(base=64), cat(base=40)))

    def test_new_state_is_not_a_problem(self):
        self.assertEqual([], drops(cat(GO=605), cat(GO=605, DF=23)))


if __name__ == "__main__":
    unittest.main()


class ZstdFilesTest(unittest.TestCase):
    """O .tar.zst de cada pacote (2026-10-05) sobe na release junto do .tar.gz e é conferido do mesmo jeito: existe,
    cabe no limite do GitHub e o sha256 bate com o catálogo."""

    def _cat(self, folder):
        from andorinha.util import file_hash
        for name in ("andorinha-base.tar.gz", "andorinha-base.tar.zst"):
            (folder / name).write_bytes(name.encode())
        gz, zst = folder / "andorinha-base.tar.gz", folder / "andorinha-base.tar.zst"
        return {"valhalla_version": config.VALHALLA_VERSION, "states": {},
                "base": {"file": gz.name, "sha256": file_hash(gz), "tiles": 1,
                         "zstd": {"file": zst.name, "bytes": zst.stat().st_size, "sha256": file_hash(zst)}}}

    def test_both_files_go_to_the_release(self):
        cat = {"base": {"file": "andorinha-base.tar.gz", "zstd": {"file": "andorinha-base.tar.zst"}},
               "states": {"GO": {"file": "andorinha-GO.tar.gz"}}}  # sem zstd (geração antiga): só o gz
        self.assertEqual(["andorinha-base.tar.gz", "andorinha-base.tar.zst", "andorinha-GO.tar.gz"],
                         publishing.package_files(cat))

    def test_missing_or_wrong_zstd_blocks(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            cat = self._cat(folder)
            with mock.patch.object(config, "DIST", folder):
                self.assertEqual([], publishing.check(cat, None, accept_drop=True, accept_older=True))
                (folder / "andorinha-base.tar.zst").write_bytes(b"outro")
                self.assertEqual(["base: sha256 de andorinha-base.tar.zst não bate com o catálogo"],
                                 publishing.check(cat, None, accept_drop=True, accept_older=True))
                (folder / "andorinha-base.tar.zst").unlink()
                self.assertEqual(["base: falta andorinha-base.tar.zst"],
                                 publishing.check(cat, None, accept_drop=True, accept_older=True))
