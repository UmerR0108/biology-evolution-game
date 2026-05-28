"""Fishing minigame with a pond-side rod, bobber, and automatic catch on bite."""

import math
import random
from dataclasses import dataclass
from typing import Iterable

import pygame

from evogame.genetics import Creature


@dataclass
class FishingResult:
    success: bool
    creature: Creature | None = None
    reason: str | None = None


def fishing_rod_geometry(
    pond_bounds: pygame.Rect,
    *,
    player_rect: pygame.Rect | None = None,
) -> dict[str, tuple[int, int]]:
    """Return rod/line/bobber points in screen coordinates.

    When a player rect is supplied, the rod handle is placed at the edge of the
    sprite nearest the pond so the player appears to hold the pole.
    """
    bobber = (pond_bounds.left + pond_bounds.width // 2, pond_bounds.top + pond_bounds.height // 2)
    if player_rect is None:
        handle = (pond_bounds.left + 18, pond_bounds.top - 10)
    else:
        if player_rect.centerx <= pond_bounds.centerx:
            hx = player_rect.right
        else:
            hx = player_rect.left
        hy = max(player_rect.top + 4, min(player_rect.bottom - 4, pond_bounds.centery))
        handle = (int(hx), int(hy))
    # Angle the tip from the player's hand toward the pond, stopping just shy of
    # the water so the line descends to the bobber.
    tip_x = int(handle[0] + (bobber[0] - handle[0]) * 0.45)
    tip_y = int(handle[1] + (bobber[1] - handle[1]) * 0.28)
    tip_y = min(tip_y, bobber[1] - 8)
    tip = (tip_x, tip_y)
    return {"handle": handle, "line_start": tip, "rod_tip": tip, "bobber_center": bobber}


def fishing_panel_rect(
    surface_rect: pygame.Rect,
    *,
    pond_bounds: pygame.Rect | None = None,
    bite_detected: bool = False,
) -> pygame.Rect:
    """Place the fishing UI compactly, avoiding the pond when possible."""
    panel = pygame.Rect(0, 0, 360 if bite_detected else 320, 112 if bite_detected else 86)
    if pond_bounds is None:
        panel.midtop = (surface_rect.centerx, surface_rect.top + 38)
        return panel.clamp(surface_rect)
    candidates = []
    above = panel.copy(); above.midbottom = (pond_bounds.centerx, pond_bounds.top - 12); candidates.append(above)
    below = panel.copy(); below.midtop = (pond_bounds.centerx, pond_bounds.bottom + 12); candidates.append(below)
    left = panel.copy(); left.midright = (pond_bounds.left - 12, pond_bounds.centery); candidates.append(left)
    right = panel.copy(); right.midleft = (pond_bounds.right + 12, pond_bounds.centery); candidates.append(right)
    for candidate in candidates:
        clamped = candidate.clamp(surface_rect)
        if not clamped.colliderect(pond_bounds):
            return clamped
    panel.midtop = (surface_rect.centerx, surface_rect.top + 30)
    return panel.clamp(surface_rect)


def attract_visible_fish_to_bobber(
    fish: Iterable[object],
    bobber_pos: tuple[float, float],
    dt_ms: float,
    *,
    max_fish: int = 2,
    speed_px_per_s: float = 18.0,
) -> None:
    """Move only the closest visible fish a small step toward the bobber."""
    ranked = sorted(
        [f for f in fish if hasattr(f, "pos")],
        key=lambda f: (float(f.pos[0]) - bobber_pos[0]) ** 2 + (float(f.pos[1]) - bobber_pos[1]) ** 2,
    )[:max_fish]
    step = max(0.0, speed_px_per_s * dt_ms / 1000.0)
    for f in ranked:
        dx = bobber_pos[0] - float(f.pos[0])
        dy = bobber_pos[1] - float(f.pos[1])
        dist = math.hypot(dx, dy)
        if dist <= 0.0001:
            continue
        move = min(step, dist)
        f.pos = (float(f.pos[0]) + dx / dist * move, float(f.pos[1]) + dy / dist * move)


def draw_fishing_rod(surface: pygame.Surface, geometry: dict[str, tuple[int, int]]) -> None:
    """Draw a tiny procedural fishing rod, line, and red/white bobber."""
    handle = geometry["handle"]
    tip = geometry["rod_tip"]
    bobber = geometry["bobber_center"]
    pygame.draw.line(surface, (102, 65, 34), handle, tip, 5)
    pygame.draw.line(surface, (187, 122, 53), handle, tip, 2)
    pygame.draw.line(surface, (230, 230, 210), tip, bobber, 1)
    pygame.draw.circle(surface, (245, 245, 245), bobber, 6)
    pygame.draw.arc(surface, (218, 54, 54), pygame.Rect(bobber[0] - 6, bobber[1] - 6, 12, 12), math.pi, math.tau, 3)
    pygame.draw.circle(surface, (38, 56, 72), bobber, 6, 1)


def fish_contacts_bobber(fish_pos: tuple[float, float], bobber_pos: tuple[float, float], radius: float = 14.0) -> bool:
    return (fish_pos[0] - bobber_pos[0]) ** 2 + (fish_pos[1] - bobber_pos[1]) ** 2 <= radius ** 2


class FishingMinigame:
    def __init__(
        self,
        candidates: list[Creature],
        rng: random.Random,
        duration_ms: float = 5000.0,
        *,
        bobber_pos: tuple[float, float] = (500.0, 300.0),
    ):
        if not candidates:
            raise ValueError("FishingMinigame needs at least one candidate fish")
        self.rng = rng
        self.duration_ms = duration_ms
        self.elapsed_ms = 0.0
        self.selected = rng.choice(candidates)
        self.tension = 0.45
        self.zone_center = rng.uniform(0.35, 0.65)
        self.zone_width = 0.30
        self.progress = 0.0
        self.action_held = False
        self.finished = False
        self.bobber_pos = bobber_pos
        self.bite_detected = False
        self._pending_result: FishingResult | None = None
        self._wait_elapsed_ms = 0.0

    @property
    def skill_check_enabled(self) -> bool:
        return False

    def register_bite(self) -> None:
        if not self.finished:
            self.bite_detected = True
            self.finished = True
            self._pending_result = FishingResult(True, self.selected, "caught")

    def check_for_bite(self, fish_positions: Iterable[tuple[float, float]], radius: float = 14.0) -> bool:
        if self.bite_detected:
            return True
        for pos in fish_positions:
            if fish_contacts_bobber(pos, self.bobber_pos, radius=radius):
                self.register_bite()
                return True
        return False

    def handle_event(self, event: pygame.event.Event) -> None:
        return

    def update(self, dt_ms: float) -> FishingResult | None:
        if self._pending_result is not None:
            result = self._pending_result
            self._pending_result = None
            return result
        if self.finished:
            return None
        if not self.bite_detected:
            self._wait_elapsed_ms += dt_ms
            self.tension = 0.5 + 0.42 * math.sin(self._wait_elapsed_ms / 360.0)
            self.tension = max(0.0, min(1.0, self.tension))
            return None
        return None

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        *,
        pond_bounds: pygame.Rect | None = None,
    ) -> None:
        panel = fishing_panel_rect(surface.get_rect(), pond_bounds=pond_bounds, bite_detected=self.bite_detected)
        pygame.draw.rect(surface, (30, 38, 54), panel, border_radius=8)
        pygame.draw.rect(surface, (220, 230, 240), panel, 2, border_radius=8)
        title = "Fishing: wait for a fish to touch the bobber"
        if self.bite_detected:
            title = "Congrats, you caught a fish!"
        surface.blit(font.render(title, True, (240, 240, 230)), (panel.left + 16, panel.top + 12))
        if not self.bite_detected:
            bar = pygame.Rect(panel.left + 26, panel.top + 48, panel.width - 52, 10)
            pygame.draw.rect(surface, (88, 103, 126), bar)
            x = bar.left + int(self.tension * bar.width)
            pygame.draw.circle(surface, (245, 245, 245), (x, bar.centery), 5)
            pygame.draw.circle(surface, (218, 54, 54), (x, bar.centery - 2), 3)
