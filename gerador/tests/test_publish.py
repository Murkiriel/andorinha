import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from andorinha.publishing import drops  # noqa: E402


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
