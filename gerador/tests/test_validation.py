"""As rotas de teste da validação, sem tiles: cobertura das 27 UFs, perfis, pontos no estado certo e pacote
ausente."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from andorinha import config, validation  # noqa: E402


def single_state_routes():
    return [r for r in validation.ROUTES if len(r.packages) == 1]


class RoutesTest(unittest.TestCase):
    def test_one_motorcycle_route_inside_each_state(self):
        covered = sorted(r.packages[0] for r in single_state_routes() if r.costing == "motorcycle")
        self.assertEqual(sorted(config.STATES), covered)

    def test_keeps_border_and_long_routes(self):
        package_sets = {r.packages for r in validation.ROUTES}
        for packages in (("GO", "DF"), ("SP", "RJ"), ("RS", "CE")):
            self.assertIn(packages, package_sets)

    def test_unique_names(self):
        names = [r.name for r in validation.ROUTES]
        self.assertEqual(len(names), len(set(names)))

    def test_points_are_inside_the_route_state(self):
        # Confere as coordenadas contra a malha do IBGE (se já baixada): um ponto no estado errado faria a rota
        # "de uma UF" depender de outro pacote e a validação não provaria nada sobre aquela UF.
        mesh = config.RAW / "ibge_malha_uf.json"
        try:
            from shapely.geometry import Point

            from andorinha.packing import state_polygons
        except ImportError:
            self.skipTest("shapely não instalado")
        if not mesh.exists():
            self.skipTest("malha do IBGE não baixada")
        polygons = state_polygons(mesh)
        for route in single_state_routes():
            state = route.packages[0]
            for lat, lon in route.points:
                self.assertTrue(polygons[state].buffer(0.01).contains(Point(lon, lat)),
                                f"{route.name}: {lat}, {lon} fora de {state}")


# Como o README da raiz chama cada perfil, e o nome dele no Valhalla.
README_PROFILES = {"carro": "auto", "moto": "motorcycle", "bicicleta": "bicycle", "a pé": "pedestrian"}


class ProfilesTest(unittest.TestCase):
    def test_default_profile_is_motorcycle(self):
        self.assertEqual("motorcycle", validation.RouteCheck("A", ((0.0, 0.0), (1.0, 1.0)), ("GO",)).costing)

    def test_every_profile_the_readme_promises_is_validated(self):
        """O README da raiz diz que os pacotes servem para estes perfis: cada um precisa de ao menos uma rota."""
        promise = (config.REPO / "README.md").read_text(encoding="utf-8").split("## ", 1)[0]  # até o 1º título
        validated = {r.costing for r in validation.ROUTES}
        for word, costing in README_PROFILES.items():
            self.assertIn(word, promise, f"o README deixou de prometer '{word}': atualize README_PROFILES")
            self.assertIn(costing, validated, f"o README promete '{word}', mas nenhuma rota valida {costing}")

    def test_no_unknown_profile(self):
        self.assertLessEqual({r.costing for r in validation.ROUTES}, set(README_PROFILES.values()))

    def test_motorcycle_is_the_focus(self):
        """Uma rota por perfil a mais; as de divisa e a longa continuam de moto."""
        others = [r for r in validation.ROUTES if r.costing != "motorcycle"]
        self.assertEqual(["auto", "bicycle", "pedestrian"], sorted(r.costing for r in others))
        self.assertTrue(all(len(r.packages) == 1 for r in others))
        self.assertEqual(30, len(validation.ROUTES) - len(others))

    def test_request_uses_the_route_profile(self):
        route = validation.RouteCheck("A", ((-16.0, -49.0), (-15.5, -48.5)), ("GO",), costing="bicycle")
        req = validation.request(route)
        self.assertEqual("bicycle", req["costing"])
        self.assertEqual([{"lat": -16.0, "lon": -49.0}, {"lat": -15.5, "lon": -48.5}], req["locations"])
        self.assertEqual("kilometers", req["directions_options"]["units"])


class MissingPackagesTest(unittest.TestCase):
    def test_missing_package_becomes_problem(self):
        routes = [validation.RouteCheck("A", ((0.0, 0.0), (1.0, 1.0)), ("GO",)),
                  validation.RouteCheck("B", ((0.0, 0.0), (1.0, 1.0)), ("SP", "RJ"))]
        problems = validation.missing_packages(routes, {"base": "b.tar.gz", "GO": "go.tar.gz", "SP": "sp.tar.gz"})
        self.assertEqual(["B: falta o pacote RJ"], problems)

    def test_missing_base_is_also_a_problem(self):
        routes = [validation.RouteCheck("A", ((0.0, 0.0), (1.0, 1.0)), ("GO",))]
        self.assertEqual(["A: falta o pacote base"], validation.missing_packages(routes, {"GO": "go.tar.gz"}))


if __name__ == "__main__":
    unittest.main()


class ExtractTest(unittest.TestCase):
    def test_a_zstd_package_extracts_for_the_test_routes(self):
        """A validação monta os pacotes .tar.zst numa pasta, como quem os usa."""
        import tempfile
        from andorinha.packing import write_package
        from andorinha.tiles import Tile
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tiles"
            t = Tile(2, 426768)
            (folder / t.path()).parent.mkdir(parents=True, exist_ok=True)
            (folder / t.path()).write_bytes(b"tile")
            write_package("AA", [t], folder, Path(tmp) / "andorinha-AA.tar.zst")
            out = Path(tmp) / "out"
            validation._extract(Path(tmp) / "andorinha-AA.tar.zst", out)
            self.assertEqual(b"tile", (out / t.path()).read_bytes())
