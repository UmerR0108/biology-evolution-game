"""Tilemap for the field-researcher game.

Holds a 2D grid of tile-name strings and renders ground tiles by
blitting scaled tileset surfaces. Water tiles report as non-walkable
so the player collision check can use ``is_walkable`` directly.

Only 16x16 source tiles from ``load_tileset`` are rendered here -
larger object sprites (tree, cottage) and the character sprite are
drawn by other code on top of the ground layer.
"""

from dataclasses import dataclass, field

import pygame

from evogame.ui.assets import load_tileset

TILE_PIXELS = 32  # 16x16 source tiles drawn at 2x scale

_NON_WALKABLE_PREFIXES = ("water_", "cliff_")
_OBJECT_FOOTPRINT_TILES = {
    "cottage": (7, 6),
    "rock": (1, 1),
    "small_rock": (1, 1),
    "stump": (1, 1),
    "log": (1, 1),
}


class Tilemap:
    def __init__(self, grid: list[list[str]]):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if grid else 0
        self.pixel_width = self.cols * TILE_PIXELS
        self.pixel_height = self.rows * TILE_PIXELS
        self._tiles: dict[str, pygame.Surface] | None = None

    def _ensure_tiles(self) -> dict[str, pygame.Surface]:
        if self._tiles is None:
            raw = load_tileset()
            # Tilemap renders only 16x16 ground tiles. Larger object
            # sprites (tree ~16x32, cottage ~80x80) and the character
            # (28x28) live in the same dict but are drawn elsewhere.
            self._tiles = {
                name: pygame.transform.scale(s, (TILE_PIXELS, TILE_PIXELS))
                for name, s in raw.items()
                if s.get_width() == 16 and s.get_height() == 16
            }
        return self._tiles

    def is_walkable(self, col: int, row: int) -> bool:
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return False
        return not self.grid[row][col].startswith(_NON_WALKABLE_PREFIXES)

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        ox, oy = origin
        tiles = self._ensure_tiles()
        for r, row_tiles in enumerate(self.grid):
            for c, name in enumerate(row_tiles):
                tile = tiles.get(name)
                if tile is None:
                    continue
                surface.blit(tile, (ox + c * TILE_PIXELS, oy + r * TILE_PIXELS))


@dataclass(frozen=True)
class SceneObject:
    kind: str
    col: int
    row: int


@dataclass
class Scene:
    tilemap: Tilemap
    objects: list[SceneObject] = field(default_factory=list)
    area_id: str = "pond"
    name: str = "Pond"
    spawn: tuple[float, float] = (480.0, 420.0)
    entry_spawns: dict[str, tuple[float, float]] = field(default_factory=dict)

    def pond_pixel_bounds(self) -> pygame.Rect:
        coords = [
            (c, r) for r in range(self.tilemap.rows) for c in range(self.tilemap.cols)
            if self.tilemap.grid[r][c].startswith("water_")
        ]
        if not coords:
            return pygame.Rect(0, 0, 0, 0)
        cols = [c for c, _ in coords]
        rows = [r for _, r in coords]
        x0, x1 = min(cols), max(cols) + 1
        y0, y1 = min(rows), max(rows) + 1
        return pygame.Rect(
            x0 * TILE_PIXELS, y0 * TILE_PIXELS,
            (x1 - x0) * TILE_PIXELS, (y1 - y0) * TILE_PIXELS,
        )

    def pond_swim_bounds(self) -> pygame.Rect:
        bounds = self.pond_pixel_bounds()
        if bounds.width <= 0 or bounds.height <= 0:
            return pygame.Rect(0, 0, 0, 0)
        inset_x = min(TILE_PIXELS, max(0, bounds.width // 5))
        inset_y = min(TILE_PIXELS, max(0, bounds.height // 5))
        return bounds.inflate(-inset_x * 2, -inset_y * 2)

    def object_blocks_tile(self, col: int, row: int) -> bool:
        for obj in self.objects:
            width, height = (1, 1) if obj.kind.startswith("tree_") else _OBJECT_FOOTPRINT_TILES.get(obj.kind, (0, 0))
            if width <= 0 or height <= 0:
                continue
            if obj.col <= col < obj.col + width and obj.row <= row < obj.row + height:
                return True
        return False

    def object_blocks_pixel(self, x: float, y: float) -> bool:
        return self.object_blocks_tile(int(x // TILE_PIXELS), int(y // TILE_PIXELS))

    def is_walkable_at_pixel(self, x: float, y: float) -> bool:
        col = int(x // TILE_PIXELS)
        row = int(y // TILE_PIXELS)
        return self.tilemap.is_walkable(col, row) and not self.object_blocks_tile(col, row)


def _base_grid(cols: int, rows: int) -> list[list[str]]:
    return [
        ["grass_alt" if (c + r) % 5 == 0 else "grass" for c in range(cols)]
        for r in range(rows)
    ]


def _forest_grid(cols: int, rows: int) -> list[list[str]]:
    grid: list[list[str]] = []
    for r in range(rows):
        row: list[str] = []
        for c in range(cols):
            edge = c < 4 or c > cols - 5 or r < 3 or r > rows - 4
            clearing = 8 <= c <= 21 and 6 <= r <= 13
            if clearing:
                name = "forest_grass_light" if (c + r) % 4 else "forest_grass"
            elif edge:
                name = "forest_grass_dark"
            else:
                name = "forest_grass" if (c * 2 + r) % 5 else "forest_grass_dark"
            row.append(name)
        grid.append(row)
    return grid


def _set_path(grid: list[list[str]], points: list[tuple[int, int]]) -> None:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    for c, r in points:
        if 0 <= r < rows and 0 <= c < cols:
            grid[r][c] = "path"


def _set_pond(grid: list[list[str]], left: int, top: int, pattern: list[str]) -> None:
    for dr, row in enumerate(pattern):
        for dc, marker in enumerate(row):
            if marker != "#":
                continue
            r = top + dr
            c = left + dc
            if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
                grid[r][c] = "water_center"


def build_forest_scene() -> Scene:
    """Hand-authored pond field site.
    30 cols x 18 rows = 960x576 px.
    """
    cols, rows = 30, 18
    grid = _base_grid(cols, rows)
    _set_pond(grid, 8, 4, [
        "..#######..",
        ".#########.",
        "###########",
        "###########",
        ".#########.",
        "..#######..",
    ])
    _set_path(grid, [(c, 13) for c in range(0, 10)])

    objects = [
        SceneObject("tree_6", col=3, row=3),
        SceneObject("tree_2", col=1, row=8),
        SceneObject("tree_10", col=23, row=2),
        SceneObject("tree_12", col=25, row=10),
        SceneObject("tree_4", col=5, row=14),
        SceneObject("bush", col=6, row=5),
        SceneObject("yellow_bush", col=20, row=5),
        SceneObject("bush", col=6, row=9),
        SceneObject("bush", col=21, row=8),
        SceneObject("small_rock", col=7, row=4),
        SceneObject("small_rock", col=20, row=10),
        SceneObject("rock", col=6, row=10),
        SceneObject("flower_yellow", col=21, row=4),
        SceneObject("flower_red", col=12, row=11),
        SceneObject("log", col=20, row=12),
    ]
    return Scene(
        Tilemap(grid), objects,
        area_id="pond", name="Pond", spawn=(64.0, 13 * TILE_PIXELS),
        entry_spawns={"home": (64.0, 13 * TILE_PIXELS)},
    )


def build_home_scene() -> Scene:
    """Calm home base used as the field research starting area."""
    cols, rows = 30, 18
    grid = _base_grid(cols, rows)
    _set_path(grid, [(15, r) for r in range(8, 18)])
    _set_path(grid, [(c, 10) for c in range(15, 30)])
    _set_path(grid, [(c, 9) for c in range(13, 18)])
    _set_path(grid, [(14, 8), (16, 8), (13, 9), (17, 9), (14, 10), (16, 10)])
    objects = [
        SceneObject("cottage", col=11, row=1),
        SceneObject("tree_1", col=2, row=4),
        SceneObject("tree_2", col=1, row=10),
        SceneObject("tree_5", col=4, row=13),
        SceneObject("tree_6", col=23, row=5),
        SceneObject("tree_7", col=27, row=7),
        SceneObject("tree_10", col=25, row=13),
        SceneObject("bush", col=7, row=7),
        SceneObject("yellow_bush", col=21, row=8),
        SceneObject("flower_red", col=10, row=11),
        SceneObject("flower_yellow", col=18, row=11),
        SceneObject("rock", col=8, row=14),
        SceneObject("stump", col=21, row=14),
    ]
    return Scene(
        Tilemap(grid), objects,
        area_id="home", name="Home", spawn=(15 * TILE_PIXELS, 11 * TILE_PIXELS),
        entry_spawns={
            "pond": (28 * TILE_PIXELS, 10 * TILE_PIXELS),
            "forest": (15 * TILE_PIXELS, 16 * TILE_PIXELS),
        },
    )


def build_deep_forest_scene() -> Scene:
    """Denser forest clearing for slower exploration and wildlife watching."""
    cols, rows = 32, 19
    grid = _forest_grid(cols, rows)
    _set_path(grid, [
        (15, 0), (15, 1), (15, 2), (15, 3), (14, 4), (15, 4), (16, 4),
        (13, 5), (12, 6), (12, 7), (13, 8), (14, 8),
    ])
    _set_pond(grid, 7, 9, [
        ".###.",
        "#####",
        "#####",
        ".###.",
    ])
    _set_pond(grid, 17, 10, [
        ".###",
        "####",
        ".##.",
    ])
    grid[9][15] = "forest_grass_light"
    for c, r in [(12, 11), (13, 11), (14, 11), (15, 11), (16, 11)]:
        grid[r][c] = "water_center"
    for c in range(22, 31):
        grid[5][c] = "cliff_top"
    for r in range(6, 13):
        for c in range(23, 31):
            if (c + r) % 4 != 0:
                grid[r][c] = "cliff_face"
    objects = [
        # Trees are inset away from fixed UI chrome and screen edges so the
        # canopy reads as intentionally placed forest cover instead of cropped
        # sprites hiding behind HUD panels.
        SceneObject("tree_1", col=2, row=4),
        SceneObject("tree_6", col=1, row=8),
        SceneObject("tree_10", col=2, row=15),
        SceneObject("tree_11", col=5, row=3),
        SceneObject("tree_3", col=7, row=3),
        SceneObject("tree_5", col=12, row=3),
        SceneObject("tree_2", col=20, row=4),
        SceneObject("tree_5", col=24, row=4),
        SceneObject("tree_10", col=29, row=4),
        SceneObject("tree_2", col=3, row=6),
        SceneObject("tree_12", col=3, row=10),
        SceneObject("tree_13", col=6, row=14),
        SceneObject("tree_2", col=11, row=15),
        SceneObject("tree_14", col=15, row=14),
        SceneObject("tree_3", col=19, row=15),
        SceneObject("tree_4", col=23, row=13),
        SceneObject("tree_14", col=29, row=13),
        SceneObject("tree_11", col=29, row=7),
        SceneObject("tree_7", col=21, row=6),
        SceneObject("tree_6", col=18, row=4),
        SceneObject("tree_4", col=9, row=5),
        SceneObject("tree_12", col=22, row=9),
        SceneObject("tree_10", col=1, row=16),
        SceneObject("tree_13", col=26, row=15),
        SceneObject("tree_8", col=4, row=16),
        SceneObject("tree_9", col=13, row=4),
        SceneObject("bush", col=7, row=6),
        SceneObject("yellow_bush", col=20, row=7),
        SceneObject("bush", col=5, row=11),
        SceneObject("yellow_bush", col=24, row=8),
        SceneObject("bush", col=4, row=7),
        SceneObject("yellow_bush", col=10, row=6),
        SceneObject("bush", col=16, row=6),
        SceneObject("yellow_bush", col=21, row=12),
        SceneObject("bush", col=25, row=14),
        SceneObject("yellow_bush", col=13, row=13),
        SceneObject("small_rock", col=11, row=7),
        SceneObject("small_rock", col=18, row=9),
        SceneObject("rock", col=13, row=10),
        SceneObject("small_rock", col=5, row=8),
        SceneObject("rock", col=20, row=11),
        SceneObject("small_rock", col=26, row=12),
        SceneObject("flower_yellow", col=10, row=12),
        SceneObject("flower_red", col=19, row=12),
        SceneObject("log", col=21, row=10),
        SceneObject("log", col=12, row=13),
        SceneObject("log", col=6, row=12),
        SceneObject("mushroom", col=6, row=8),
        SceneObject("mushroom", col=23, row=11),
        SceneObject("mushroom", col=17, row=13),
        SceneObject("mushroom", col=27, row=4),
        SceneObject("stump", col=16, row=13),
    ]
    return Scene(
        Tilemap(grid), objects,
        area_id="forest", name="Forest", spawn=(15 * TILE_PIXELS, 3 * TILE_PIXELS),
        entry_spawns={"home": (15 * TILE_PIXELS, 3 * TILE_PIXELS)},
    )
