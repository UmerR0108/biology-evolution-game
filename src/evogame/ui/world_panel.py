from typing import TYPE_CHECKING

import pygame

from evogame.ui.assets import load_tileset
from evogame.ui.tilemap import TILE_PIXELS, build_forest_scene

if TYPE_CHECKING:
    from evogame.ui.player import Player


class WorldPanel:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.scene = build_forest_scene()
        self._object_surfs: dict[str, pygame.Surface] | None = None

    def _ensure_objects(self) -> dict[str, pygame.Surface]:
        if self._object_surfs is None:
            raw = load_tileset()
            self._object_surfs = {
                "tree": pygame.transform.scale(raw["tree"], (TILE_PIXELS * 2, TILE_PIXELS * 2)),
                "cottage": pygame.transform.scale(raw["cottage"], (TILE_PIXELS * 4, TILE_PIXELS * 3)),
            }
        return self._object_surfs

    def draw(self, surface: pygame.Surface, player: "Player | None" = None) -> None:
        self.scene.tilemap.draw(surface, origin=(self.rect.left, self.rect.top))
        objs = self._ensure_objects()
        for obj in self.scene.objects:
            sprite = objs.get(obj.kind)
            if sprite is None:
                continue
            x = self.rect.left + obj.col * TILE_PIXELS
            y = self.rect.top + obj.row * TILE_PIXELS
            surface.blit(sprite, (x, y))
        if player is not None:
            sprite = player._ensure_sprite()
            surface.blit(sprite, (self.rect.left + player.pos[0], self.rect.top + player.pos[1]))
