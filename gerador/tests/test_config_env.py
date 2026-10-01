"""O que o config lê do ambiente, para o mesmo código rodar aqui, num repositório de teste e no público."""
import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from andorinha import config  # noqa: E402

ENV_VARS = ("ANDORINHA_REPO", "GITHUB_REPOSITORY", "ANDORINHA_THREADS", "ANDORINHA_MIN_FREE_DISK_GB",
            "ANDORINHA_KEEP_GENERATIONS")


def reload_config(**env):
    clean = {k: v for k, v in os.environ.items() if k not in ENV_VARS}
    with mock.patch.dict(os.environ, {**clean, **env}, clear=True):
        return importlib.reload(config)


class EnvironmentTest(unittest.TestCase):
    def tearDown(self):
        reload_config()  # devolve o config ao padrão para os outros testes

    def test_default_is_public_repository(self):
        c = reload_config()
        self.assertEqual("Murkiriel/andorinha", c.GITHUB_REPO)
        self.assertEqual("https://github.com/Murkiriel/andorinha/releases/download/{tag}/", c.RELEASE_URL)

    def test_actions_repository(self):
        c = reload_config(GITHUB_REPOSITORY="Murkiriel/andorinha-teste")
        self.assertEqual("Murkiriel/andorinha-teste", c.GITHUB_REPO)
        self.assertIn("/andorinha-teste/releases/download/", c.RELEASE_URL)

    def test_andorinha_repo_wins_over_actions(self):
        c = reload_config(GITHUB_REPOSITORY="outro/repo", ANDORINHA_REPO="Murkiriel/andorinha")
        self.assertEqual("Murkiriel/andorinha", c.GITHUB_REPO)

    def test_threads_from_environment(self):
        self.assertEqual(2, reload_config(ANDORINHA_THREADS="2").THREADS)

    def test_default_threads_at_most_8(self):
        c = reload_config()
        self.assertEqual(min(8, os.cpu_count() or 1), c.THREADS)

    def test_min_free_disk_from_environment(self):
        self.assertEqual(18_000_000_000, reload_config(ANDORINHA_MIN_FREE_DISK_GB="18").MIN_FREE_DISK_BYTES)
        self.assertEqual(25_000_000_000, reload_config().MIN_FREE_DISK_BYTES)

    def test_kept_generations(self):
        self.assertEqual(3, reload_config().KEEP_GENERATIONS)
        self.assertEqual(5, reload_config(ANDORINHA_KEEP_GENERATIONS="5").KEEP_GENERATIONS)
        self.assertEqual(0, reload_config(ANDORINHA_KEEP_GENERATIONS="0").KEEP_GENERATIONS)  # 0 = não apaga


if __name__ == "__main__":
    unittest.main()
