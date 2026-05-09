import random as _rand_module
from typing import TYPE_CHECKING

import pygame

from evogame.ui.assets import load_pond_composite, load_tileset, load_tree_sprite
from evogame.ui.pond import PondView
from evogame.ui.tilemap import TILE_PIXELS, build_forest_scene
from evogame.ui.wildlife import Bunny

if TYPE_CHECKING:
    from evogame.ui.player import Player


class WorldPanel:
    COTTAGE_INTERACT_RADIUS = 64

    def __init__(self, rect: pygame.Rect,
                 pond_rng: _rand_module.Random | None = None,
                 wildlife_rng: _rand_module.Random | None = None):
        self.rect = rect
        self.scene = build_forest_scene()
        self._object_surfs: dict[str, pygame.Surface] | None = None
        self._pond_composite: pygame.Surface | None = None
        self.pond_view = PondView(
            bounds=self._pond_bounds_in_panel(),
            max_visible=10,
            rng=pond_rng or _rand_module.Random(0),
        )

        wlrng = wildlife_rng or _rand_module.Random(7)
        self.wildlife: list[Bunny] = []
        for _ in range(3):
            for _attempt in range(20):
                x = wlrng.uniform(0, self.scene.tilemap.pixel_width)
                y = wlrng.uniform(0, self.scene.tilemap.pixel_height)
                col = int(x // TILE_PIXELS)
                row = int(y // TILE_PIXELS)
                if self.scene.tilemap.is_walkable(col, row):
                    self.wildlife.append(Bunny(pos=(x, y), scene=self.scene, rng=wlrng))
                    break

    def _pond_bounds_in_panel(self) -> pygame.Rect:
        b = self.scene.pond_pixel_bounds()
        return pygame.Rect(self.rect.left + b.left, self.rect.top + b.top, b.width, b.height)

    def update_wildlife(self, dt_ms: float) -> None:
        for b in self.wildlife:
            b.update(dt_ms)

    def _ensure_objects(self) -> dict[str, pygame.Surface]:
        if self._object_surfs is None:
            raw = load_tileset()
            # Tree 6 (70x98 native) is taller-than-wide and reads as a
            # proper 3D-feeling tree. We blit it at native size and
            # anchor it at the cell's bottom edge in ``draw`` so the
            # canopy rises above the grid cell.
            self._object_surfs = {
                "tree": load_tree_sprite("6", "green"),
                "cottage": pygame.transform.scale(raw["cottage"], (TILE_PIXELS * 4, TILE_PIXELS * 3)),
            }
        return self._object_surfs

    def _ensure_pond_composite(self) -> pygame.Surface:
        if self._pond_composite is None:
            composite = load_pond_composite()
            bounds = self.scene.pond_pixel_bounds()
            self._pond_composite = pygame.transform.scale(
                composite, (bounds.width, bounds.height)
            )
        return self._pond_composite

    def cottage_in_range(self, player: "Player") -> bool:
        cottage = next((o for o in self.scene.objects if o.kind == "cottage"), None)
        if cottage is None:
            return False
        cx = cottage.col * TILE_PIXELS + TILE_PIXELS * 2
        cy = cottage.row * TILE_PIXELS + TILE_PIXELS * 1.5
        px = player.pos[0] + player.size[0] / 2
        py = player.pos[1] + player.size[1] / 2
        return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 <= self.COTTAGE_INTERACT_RADIUS

    def draw(self, surface: pygame.Surface, player: "Player | None" = None, font: pygame.font.Font | None = None) -> None:
        self.scene.tilemap.draw(surface, origin=(self.rect.left, self.rect.top))
        # Pond composite overlays the synthesized water tiles, providing
        # a single grass-bordered sprite that visually merges with the
        # surrounding grass. The water_* tiles in the grid still drive
        # is_walkable / collision — only visuals change here.
        bounds = self.scene.pond_pixel_bounds()
        if bounds.width > 0 and bounds.height > 0:
            pond_composite = self._ensure_pond_composite()
            surface.blit(
                pond_composite,
                (self.rect.left + bounds.left, self.rect.top + bounds.top),
            )
        objs = self._ensure_objects()
        for obj in self.scene.objects:
            sprite = objs.get(obj.kind)
            if sprite is None:
                continue
            x = self.rect.left + obj.col * TILE_PIXELS
            if obj.kind == "tree":
                # Anchor tree at cell's bottom edge so the canopy rises
                # above the cell. (sprite.height - TILE_PIXELS) lifts the
                # blit origin upward by the canopy overhang.
                y = self.rect.top + obj.row * TILE_PIXELS - (sprite.get_height() - TILE_PIXELS)
            else:
                y = self.rect.top + obj.row * TILE_PIXELS
            surface.blit(sprite, (x, y))
        # Bunnies drawn after objects, before pond fish (so a bunny near a tree appears in front of the tree).
        for b in self.wildlife:
            b.draw(surface, origin=(self.rect.left, self.rect.top))
        # Pond fish (after objects, before player so fish go behind player).
        self.pond_view.draw(surface, origin=(0, 0))
        if player is not None:
            player.draw(surface, origin=(self.rect.left, self.rect.top))
        if player is not None and font is not None and self.cottage_in_range(player):
            cottage = next((o for o in self.scene.objects if o.kind == "cottage"), None)
            if cottage is not None:
                text = font.render("Press E", True, (255, 255, 255))
                x = self.rect.left + cottage.col * TILE_PIXELS
                y = self.rect.top + cottage.row * TILE_PIXELS - 18
                shadow = pygame.Surface((text.get_width() + 6, text.get_height() + 4), pygame.SRCALPHA)
                shadow.fill((0, 0, 0, 160))
                surface.blit(shadow, (x, y))
                surface.blit(text, (x + 3, y + 2))
