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
        cell = max(1, (self.rect.width - 20) // cols)
        for i, creature in enumerate(creatures):
            col = i % cols
            row = i // cols
            cx = self.rect.left + 10 + col * cell + cell // 2
            cy = self.rect.top + 10 + row * cell + cell // 2
            if cy > self.rect.bottom - 10:
                break
            phenotype = creature.phenotype
            color = _COLOR_MAP.get(phenotype["color"].category, _FALLBACK)
            radius = max(3, int(4 + phenotype["body_size"].value * 0.5))
            pygame.draw.circle(surface, color, (cx, cy), radius)
