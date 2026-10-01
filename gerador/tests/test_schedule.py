"""A regra do agendamento: gera de novo quando a geração publicada completa o intervalo (29 dias)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

GENERATOR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GENERATOR))
from andorinha import config, schedule  # noqa: E402

BUILT = "2026-09-30T18:21:32Z"


def utc(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def after(**delta) -> datetime:
    return utc(BUILT) + timedelta(**delta)


class GenerationDueTest(unittest.TestCase):
    def due(self, built_at, now, **kwargs):
        return schedule.generation_due(built_at, now, 29, **kwargs)[0]

    def test_default_interval_is_29_days(self):
        self.assertEqual(29, config.GENERATION_INTERVAL_DAYS)

    def test_28_days_is_too_early(self):
        self.assertFalse(self.due(BUILT, after(days=28)))

    def test_29_days_generates(self):
        self.assertTrue(self.due(BUILT, after(days=29)))

    def test_days_are_rounded(self):
        """28 dias e 13 h já contam como 29: o horário do build não empurra a geração para o dia seguinte."""
        self.assertTrue(self.due(BUILT, after(days=28, hours=13)))
        self.assertFalse(self.due(BUILT, after(days=28, hours=11)))

    def test_scheduled_run_after_a_scheduled_build(self):
        """Geração agendada termina por volta das 06:40 UTC; 29 dias depois, o agendamento das 06:00 já gera."""
        self.assertTrue(self.due("2026-10-30T06:40:00Z", utc("2026-11-28T06:00:00Z")))
        self.assertFalse(self.due("2026-10-30T06:40:00Z", utc("2026-11-27T06:00:00Z")))

    def test_first_scheduled_generation_after_the_manual_one(self):
        self.assertFalse(self.due(BUILT, utc("2026-10-29T06:00:00Z")))
        self.assertTrue(self.due(BUILT, utc("2026-10-30T06:00:00Z")))

    def test_no_published_date_generates(self):
        self.assertTrue(self.due(None, after(days=1)))

    def test_unreadable_date_generates(self):
        self.assertTrue(self.due("ontem", after(days=1)))

    def test_manual_always_generates(self):
        self.assertTrue(self.due(BUILT, after(hours=1), manual=True))

    def test_reason_says_the_age(self):
        due, reason = schedule.generation_due(BUILT, after(days=10), 29)
        self.assertFalse(due)
        self.assertIn("10 dias", reason)
        self.assertIn("29", reason)


class CatalogBuiltAtTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_reads_built_at(self):
        f = self.tmp / "catalogo.json"
        f.write_text(json.dumps({"built_at": BUILT}), encoding="utf-8")
        self.assertEqual(BUILT, schedule.catalog_built_at(f))

    def test_missing_catalog(self):
        self.assertIsNone(schedule.catalog_built_at(self.tmp / "catalogo.json"))

    def test_broken_catalog(self):
        f = self.tmp / "catalogo.json"
        f.write_text("<html>", encoding="utf-8")
        self.assertIsNone(schedule.catalog_built_at(f))

    def test_catalog_without_the_date(self):
        f = self.tmp / "catalogo.json"
        f.write_text(json.dumps({"schema": 1}), encoding="utf-8")
        self.assertIsNone(schedule.catalog_built_at(f))


class DueScriptTest(unittest.TestCase):
    """A linha de comando que o workflow chama: imprime o motivo e grava run=true|false em $GITHUB_OUTPUT."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.output = self.tmp / "github_output"

    def run_script(self, built_at, *args):
        catalog = self.tmp / "catalogo.json"
        if built_at is not None:
            catalog.write_text(json.dumps({"built_at": built_at}), encoding="utf-8")
        env = {**os.environ, "GITHUB_OUTPUT": str(self.output)}
        r = subprocess.run([sys.executable, str(GENERATOR / "scripts" / "due.py"), "--catalog", str(catalog), *args],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(0, r.returncode, r.stderr)
        return self.output.read_text(encoding="utf-8"), r.stdout

    def stamp(self, days_ago: int) -> str:
        return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def test_recent_generation(self):
        output, log = self.run_script(self.stamp(3))
        self.assertEqual("run=false\n", output)
        self.assertIn("3 dias", log)

    def test_old_generation(self):
        self.assertEqual("run=true\n", self.run_script(self.stamp(40))[0])

    def test_no_catalog(self):
        self.assertEqual("run=true\n", self.run_script(None)[0])

    def test_manual(self):
        self.assertEqual("run=true\n", self.run_script(self.stamp(3), "--manual")[0])

    def test_interval_from_the_command_line(self):
        self.assertEqual("run=true\n", self.run_script(self.stamp(3), "--interval-days", "2")[0])


if __name__ == "__main__":
    unittest.main()
