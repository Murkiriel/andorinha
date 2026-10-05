import gzip
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from andorinha.packing import distribute, write_package  # noqa: E402
from andorinha.tiles import Tile, at_point  # noqa: E402

try:
    from shapely.geometry import box
except ImportError:  # pragma: no cover
    box = None


@unittest.skipIf(box is None, "shapely não instalado")
class DistributeTest(unittest.TestCase):
    def setUp(self):
        # Duas "UFs" vizinhas, com a divisa em lon -47.5. BB acaba 0,02 grau antes da linha de tiles de -47.0.
        self.states = {"AA": box(-48.0, -16.0, -47.5, -15.0), "BB": box(-47.5, -16.0, -47.02, -15.0)}

    def test_level_0_goes_entirely_to_base(self):
        packages, _ = distribute([Tile(0, 1653)], self.states, 0.05)
        self.assertEqual([Tile(0, 1653)], packages["base"])
        self.assertNotIn("AA", packages)

    def test_tile_inside_one_state(self):
        t = at_point(2, -15.5, -47.9)  # quadrado -48.0..-47.75: só em AA
        packages, outside = distribute([t], self.states, 0.05)
        self.assertEqual([t], packages["AA"])
        self.assertNotIn("BB", packages)
        self.assertEqual([], outside)

    def test_border_tile_goes_to_both(self):
        t = at_point(1, -15.5, -47.5)  # quadrado de 1 grau que cobre as duas
        packages, _ = distribute([t], self.states, 0.05)
        self.assertIn(t, packages["AA"])
        self.assertIn(t, packages["BB"])

    def test_margin_catches_neighbor_tile(self):
        t = at_point(2, -15.5, -46.9)  # quadrado -47.0..-46.75: a 0,02 grau de BB, dentro da margem
        self.assertEqual({"base": []}, distribute([t], self.states, 0.0)[0])
        self.assertEqual([t], distribute([t], self.states, 0.05)[0]["BB"])

    def test_far_tile_is_left_out(self):
        t = at_point(2, 10.0, 10.0)
        _, outside = distribute([t], self.states, 0.05)
        self.assertEqual([t], outside)


class WritePackageTest(unittest.TestCase):
    def test_reproducible_package_with_tile_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tiles"
            tiles = [Tile(2, 426768), Tile(1, 26772)]
            for t in tiles:
                (folder / t.path()).parent.mkdir(parents=True, exist_ok=True)
                (folder / t.path()).write_bytes(b"tile " + t.path().encode())
            a = write_package("AA", tiles, folder, Path(tmp) / "a.tar.gz")
            b = write_package("AA", list(reversed(tiles)), folder, Path(tmp) / "b.tar.gz")
            self.assertEqual(a.sha256, b.sha256)  # mesma entrada, mesmo arquivo byte a byte
            self.assertEqual(2, a.tiles)
            with tarfile.open(Path(tmp) / "a.tar.gz", "r:gz") as tar:
                self.assertEqual(["1/026/772.gph", "2/000/426/768.gph"], tar.getnames())
            with gzip.open(Path(tmp) / "a.tar.gz") as gz:
                gz.read()  # gzip válido

    def test_zstd_twin_holds_the_same_tar(self):
        """Ao lado de cada .tar.gz sai um .tar.zst (zstd 19, janela padrão: pouca memória para descompactar no
        celular) com o mesmo tar dentro, byte a byte, também reproduzível; o catálogo leva arquivo, tamanho e
        sha256 dele."""
        import zstandard
        from andorinha.util import file_hash
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tiles"
            tiles = [Tile(2, 426768), Tile(1, 26772)]
            for t in tiles:
                (folder / t.path()).parent.mkdir(parents=True, exist_ok=True)
                (folder / t.path()).write_bytes(b"tile " + t.path().encode() * 50)
            a = write_package("AA", tiles, folder, Path(tmp) / "andorinha-AA.tar.gz")
            zst = Path(tmp) / "andorinha-AA.tar.zst"
            self.assertTrue(zst.exists(), "falta o .tar.zst ao lado do .tar.gz")
            self.assertEqual({"file": zst.name, "bytes": zst.stat().st_size, "sha256": file_hash(zst)}, a.zstd)
            with gzip.open(Path(tmp) / "andorinha-AA.tar.gz") as gz:
                tar_from_gz = gz.read()
            with open(zst, "rb") as f:
                tar_from_zst = zstandard.ZstdDecompressor().stream_reader(f).read()
            self.assertEqual(tar_from_gz, tar_from_zst)
            params = zstandard.get_frame_parameters(zst.read_bytes())
            self.assertLessEqual(params.window_size, 8 * 1024 * 1024)
            (Path(tmp) / "b").mkdir()
            b = write_package("AA", list(reversed(tiles)), folder, Path(tmp) / "b" / "andorinha-AA.tar.gz")
            self.assertEqual(a.zstd["sha256"], b.zstd["sha256"])
            self.assertFalse((Path(tmp) / "andorinha-AA.tar").exists())  # o tar aberto não fica na pasta

    def test_clean_output_also_removes_old_zstd(self):
        from andorinha.packing import clean_output
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for name in ("andorinha-GO.tar.gz", "andorinha-GO.tar.zst", "catalogo.json", "outro.txt"):
                (out / name).write_text("x")
            clean_output(out)
            self.assertEqual(["outro.txt"], sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    unittest.main()
