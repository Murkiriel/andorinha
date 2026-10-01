"""Grade de tiles do Valhalla: caminho do arquivo <-> nível, índice e retângulo coberto.

O Valhalla corta o mundo em três grades (valhalla.github.io/valhalla/concepts/tiles):
nível 0 (rodovias) em quadrados de 4°, nível 1 (arteriais) de 1° e nível 2 (vias locais) de 0,25°.
O índice conta a partir do canto inferior esquerdo do mundo (-180, -90), linha a linha:
índice = linha * colunas + coluna. O arquivo fica em <nível>/<índice com zeros, em grupos de 3>.gph,
por exemplo 2/000/426/768.gph.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Tuple

TILE_SIZE_DEG = {0: 4.0, 1: 1.0, 2: 0.25}


@dataclass(frozen=True, order=True)
class Tile:
    level: int
    index: int

    @property
    def size(self) -> float:
        return TILE_SIZE_DEG[self.level]

    @property
    def columns(self) -> int:
        return int(round(360 / self.size))

    def bbox(self) -> Tuple[float, float, float, float]:
        """(lon mínima, lat mínima, lon máxima, lat máxima)."""
        line, column = divmod(self.index, self.columns)
        lon = -180.0 + column * self.size
        lat = -90.0 + line * self.size
        return lon, lat, lon + self.size, lat + self.size

    def path(self) -> str:
        """Caminho relativo à pasta de tiles, com '/' (o mesmo dentro do .tar)."""
        lines = int(round(180 / self.size))
        digits = len(str(self.columns * lines - 1))
        digits += (3 - digits % 3) % 3  # completa grupos de 3
        s = str(self.index).zfill(digits)
        groups = [s[i:i + 3] for i in range(0, len(s), 3)]
        return f"{self.level}/" + "/".join(groups) + ".gph"


def from_path(relative: str) -> Tile:
    """'2/000/426/768.gph' -> Tile(2, 426768)."""
    parts = relative.replace("\\", "/").split("/")
    level = int(parts[0])
    if level not in TILE_SIZE_DEG:
        raise ValueError(f"nível desconhecido em {relative}")
    return Tile(level, int("".join(parts[1:]).removesuffix(".gph")))


def at_point(level: int, lat: float, lon: float) -> Tile:
    """O tile do nível que contém o ponto."""
    size = TILE_SIZE_DEG[level]
    columns = int(round(360 / size))
    line = int((lat + 90.0) // size)
    column = int((lon + 180.0) // size)
    return Tile(level, line * columns + column)


def list_tiles(folder: Path) -> Iterator[Tuple[Tile, Path]]:
    """Todos os .gph da pasta de tiles (só os níveis 0, 1 e 2: o de transporte público não é gerado aqui)."""
    for p in sorted(folder.rglob("*.gph")):
        rel = p.relative_to(folder).as_posix()
        if rel.split("/")[0] in ("0", "1", "2"):
            yield from_path(rel), p
