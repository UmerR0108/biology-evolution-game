import pygame

from evogame.genetics import Creature

_POND = (60, 110, 150)
_COLOR_MAP = {
    "red": (220, 40, 40),
    "pink": (240, 140, 160),
    "white": (240, 240, 240),
}
_FALLBACK = (128, 128, 128)


class WorldPanel:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect

    def draw(self, surface: pygame.Surface, creatures: list[Creature]) -> None:
        pygame.draw.rect(surface, _POND, self.rect)
        if not creatures:
            return
        cols = max(1, int(len(creatures) ** 0.5) + 1)
        cell_w = max(1, (self.rect.width - 20) // cols)
        cell_h = cell_w
        for i, creature in enumerate(creatures):
            col = i % cols
            row = i // cols
            cx = self.rect.left + 10 + col * cell_w + cell_w // 2
            cy = self.rect.top + 10 + row * cell_h + cell_h // 2
            if cy > self.rect.bottom - 10:
                break
            color_cat = creature.phenotype["color"].category
            color = _COLOR_MAP.get(color_cat, _FALLBACK)
            body_size = creature.phenotype["body_size"].value
            radius = max(3, int(4 + body_size * 0.5))
            pygame.draw.circle(surface, color, (cx, cy), radius)
