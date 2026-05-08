import pygame

_BG = (25, 25, 35)
_FG = (220, 220, 220)


class StatusStrip:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, *,
             generation: int, population: int, gens_per_second: float,
             extinct: bool, journal_open: bool) -> None:
        pygame.draw.rect(surface, _BG, self.rect)
        text = f"Gen {generation}   Pop {population}   Speed {gens_per_second:.1f}/s"
        if extinct:
            text += "   EXTINCT"
        if not journal_open:
            text += "   [J] Journal"
        surface.blit(font.render(text, True, _FG), (self.rect.left + 12, self.rect.top + 5))
