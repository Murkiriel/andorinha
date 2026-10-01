import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from andorinha import sources, config  # noqa: E402
from tests.fake_server import FakeServer  # noqa: E402

A = b"extrato versao A " * 5000
B = b"extrato versao B, mais nova " * 5000


def md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


class ExtractTest(unittest.TestCase):
    """sources.osm_extract contra um servidor local que imita o openstreetmap.fr (state.txt, .md5 e o .pbf)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raw = Path(self._tmp.name)
        self.current = [A]  # o arquivo que o "servidor" publica agora
        self.server = FakeServer().__enter__()
        s = self.server
        s.files["/state.txt"] = lambda: b"sequenceNumber=1\ntimestamp=2026-09-29T00\\:59\\:51Z\n"
        s.files["/x.md5"] = lambda: f"{md5(self.current[0])}  brazil.osm.pbf\n".encode()
        s.files["/x.pbf"] = lambda: self.current[0]
        self._patches = [mock.patch.object(config, "RAW", self.raw),
                         mock.patch.object(config, "OSM_STATE_URL", s.url("/state.txt")),
                         mock.patch.object(config, "OSM_MD5_URL", s.url("/x.md5")),
                         mock.patch.object(config, "OSM_PBF_URL", s.url("/x.pbf")),
                         mock.patch.object(sources, "RETRY_DELAY", 0)]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self.server.__exit__(None, None, None)
        self._tmp.cleanup()

    def downloads(self):
        return sum(1 for path, _ in self.server.requests if path == "/x.pbf")

    def test_downloads_and_saves_meta_with_size(self):
        meta = sources.osm_extract()
        self.assertEqual(A, (self.raw / "brazil-latest.osm.pbf").read_bytes())
        self.assertEqual(md5(A), meta["md5"])
        self.assertEqual("2026-09-29T00:59:51Z", meta["timestamp"])
        self.assertEqual(len(A), json.loads((self.raw / "brazil-latest.meta.json").read_text())["size"])

    def test_does_not_download_again_when_up_to_date(self):
        sources.osm_extract()
        sources.osm_extract()
        self.assertEqual(1, self.downloads())

    def test_extract_updated_during_download(self):
        # O md5 lido antes do download é o de A, mas o servidor troca para B antes de mandar o arquivo.
        def switch_and_serve():
            self.current[0] = B
            return B
        self.server.files["/x.pbf"] = switch_and_serve
        meta = sources.osm_extract()
        self.assertEqual(md5(B), meta["md5"])
        self.assertEqual(B, (self.raw / "brazil-latest.osm.pbf").read_bytes())

    def test_corrupted_file_fails_and_is_removed(self):
        self.server.files["/x.pbf"] = lambda: A[:-10] + b"corrompido"
        with self.assertRaises(RuntimeError):
            sources.osm_extract()
        self.assertFalse((self.raw / "brazil-latest.osm.pbf").exists())

    def test_truncated_local_extract_is_downloaded_again(self):
        sources.osm_extract()
        pbf = self.raw / "brazil-latest.osm.pbf"
        pbf.write_bytes(A[:1000])  # meta diz que está tudo certo, mas o arquivo encolheu
        sources.osm_extract()
        self.assertEqual(A, pbf.read_bytes())
        self.assertEqual(2, self.downloads())


def fake_mesh(exclude=()) -> bytes:
    """GeoJSON no formato da API de malhas do IBGE: uma feição por UF, código em `codarea`."""
    features = [{"type": "Feature", "properties": {"codarea": code},
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}}
                for code in config.IBGE_STATE_CODES if code not in exclude]
    return json.dumps({"type": "FeatureCollection", "features": features}).encode()


class MeshTest(unittest.TestCase):
    """sources.malha_ibge: só grava (e só aceita do cache) uma malha com as 27 UFs."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raw = Path(self._tmp.name)
        self.dest = self.raw / "ibge_malha_uf.json"
        self.server = FakeServer().__enter__()
        self.server.files["/malha"] = fake_mesh()
        self._patches = [mock.patch.object(config, "RAW", self.raw),
                         mock.patch.object(config, "IBGE_MESH_URL", self.server.url("/malha")),
                         mock.patch.object(sources, "RETRY_DELAY", 0)]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self.server.__exit__(None, None, None)
        self._tmp.cleanup()

    def downloads(self):
        return sum(1 for path, _ in self.server.requests if path == "/malha")

    def test_good_mesh_is_saved(self):
        self.assertEqual(self.dest, sources.ibge_mesh())
        self.assertEqual(27, len(json.loads(self.dest.read_text())["features"]))

    def test_error_page_with_200_is_not_saved(self):
        self.server.files["/malha"] = b"<html><body>Servico indisponivel</body></html>"
        with self.assertRaises(RuntimeError):
            sources.ibge_mesh()
        self.assertFalse(self.dest.exists())

    def test_mesh_missing_a_state_is_rejected(self):
        self.server.files["/malha"] = fake_mesh(exclude=("53",))  # sem o DF
        with self.assertRaises(RuntimeError) as ctx:
            sources.ibge_mesh()
        self.assertIn("DF", str(ctx.exception))
        self.assertFalse(self.dest.exists())

    def test_invalid_cache_is_replaced(self):
        self.dest.write_text("<html>erro gravado por uma versão antiga</html>")
        sources.ibge_mesh()
        self.assertEqual(27, len(json.loads(self.dest.read_text())["features"]))
        self.assertEqual(1, self.downloads())

    def test_valid_cache_does_not_download(self):
        self.dest.write_bytes(fake_mesh())
        sources.ibge_mesh()
        self.assertEqual(0, self.downloads())


if __name__ == "__main__":
    unittest.main()
