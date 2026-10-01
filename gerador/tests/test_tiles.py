import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from andorinha.tiles import Tile, from_path, at_point  # noqa: E402


class TilesTest(unittest.TestCase):
    # Caminhos reais de um build do Valhalla 3.6.3 (Brasil), no ponto da Rodoviária de Brasília.
    BUS_STATION = (-15.7942, -47.8825)

    def test_point_falls_in_right_tile_on_all_levels(self):
        self.assertEqual("0/001/653.gph", at_point(0, *self.BUS_STATION).path())
        self.assertEqual("1/026/772.gph", at_point(1, *self.BUS_STATION).path())
        self.assertEqual("2/000/426/768.gph", at_point(2, *self.BUS_STATION).path())

    def test_bbox_contains_the_point(self):
        for level in (0, 1, 2):
            lon0, lat0, lon1, lat1 = at_point(level, *self.BUS_STATION).bbox()
            self.assertTrue(lon0 <= self.BUS_STATION[1] < lon1 and lat0 <= self.BUS_STATION[0] < lat1)

    def test_level_2_bbox(self):
        self.assertEqual((-48.0, -16.0, -47.75, -15.75), Tile(2, 426768).bbox())

    def test_roundtrip(self):
        for t in (Tile(0, 0), Tile(0, 4049), Tile(1, 26772), Tile(1, 64799), Tile(2, 426768), Tile(2, 1036799)):
            self.assertEqual(t, from_path(t.path()))

    def test_windows_path(self):
        self.assertEqual(Tile(2, 426768), from_path("2\\000\\426\\768.gph"))

    def test_unknown_level(self):
        with self.assertRaises(ValueError):
            from_path("3/000/001.gph")


if __name__ == "__main__":
    unittest.main()
