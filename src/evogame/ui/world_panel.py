import random as _rand_module
from typing import TYPE_CHECKING

import pygame

from evogame.ui.assets import load_tileset
from evogame.ui.pond import PondView
from evogame.ui.tilemap import TILE_PIXELS, build_forest_scene

if TYPE_CHECKING:
    from evogame.ui.player import Player


class WorldPanel:
    COTTAGE_INTERACT_RADIUS = 64

    def __init__(self, rect: pygame.Rect, pond_rng: _rand_module.Random | None = None):
        self.rect = rect
        self.scene = build_forest_scene()
        self._object_surfs: dict[str, pygame.Surface] | None = None
        self.pond_view = PondView(
            bounds=self._pond_bounds_in_panel(),
            max_visible=10,
            rng=pond_rng or _rand_module.Random(0),
        )

    def _pond_bounds_in_panel(self) -> pygame.Rect:
        b = self.scene.pond_pixel_bounds()
        return pygame.Rect(self.rect.left + b.left, self.rect.top + b.top, b.width, b.height)

    def _ensure_objects(self) -> dict[str, pygame.Surface]:
        if self._object_surfs is None:
            raw = load_tileset()
            self._object_surfs = {
                "tree": pygame.transform.scale(raw["tree"], (TILE_PIXELS * 2, TILE_PIXELS * 2)),
                "cottage": pygame.transform.scale(raw["cottage"], (TILE_PIXELS * 4, TILE_PIXELS * 3)),
            }
        return self._object_surfs

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
        objs = self._ensure_objects()
        for obj in self.scene.objects:
            sprite = objs.get(obj.kind)
            if sprite is None:
                continue
            x = self.rect.left + obj.col * TILE_PIXELS
            y = self.rect.top + obj.row * TILE_PIXELS
            surface.blit(sprite, (x, y))
        # Pond fish (after objects, before player so fish go behind player).
        self.pond_view.draw(surface, origin=(0, 0))
        if player is not None:
            sprite = player._ensure_sprite()
            surface.blit(sprite, (self.rect.left + player.pos[0], self.rect.top + player.pos[1]))
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
