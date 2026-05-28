import random

import pygame

from evogame.genetics import Creature, GUPPY_SCHEMA
from evogame.ui.fishing import (
    FishingMinigame,
    attract_visible_fish_to_bobber,
    fish_contacts_bobber,
    fishing_panel_rect,
    fishing_rod_geometry,
)
from evogame.ui.pond import VisibleFish


def _fish(n=4):
    rng = random.Random(0)
    return [Creature.random(GUPPY_SCHEMA, rng) for _ in range(n)]


def test_fishing_minigame_selects_candidate_from_population():
    candidates = _fish()
    game = FishingMinigame(candidates, random.Random(1))

    assert game.selected in candidates


def test_fishing_minigame_contact_auto_catches_selected_creature():
    game = FishingMinigame(_fish(), random.Random(1), duration_ms=5000, bobber_pos=(100, 100))

    assert game.check_for_bite([(100, 100)]) is True
    result = game.update(0)

    assert result is not None
    assert result.success is True
    assert result.creature is game.selected
    assert result.reason == "caught"


def test_fishing_has_no_skill_check_after_bite():
    game = FishingMinigame(_fish(), random.Random(1), bobber_pos=(100, 100))

    game.check_for_bite([(100, 100)])

    assert game.skill_check_enabled is False


def test_fishing_waits_for_fish_contact_before_skill_check():
    game = FishingMinigame(_fish(), random.Random(1), bobber_pos=(100, 100))

    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert game.update(1000) is None
    assert game.bite_detected is False

    assert game.check_for_bite([(100, 100)]) is True
    assert game.bite_detected is True


def test_fishing_contact_detection_uses_bobber_radius():
    assert fish_contacts_bobber((10, 10), (20, 10), radius=10) is True
    assert fish_contacts_bobber((10, 10), (21, 10), radius=10) is False


def test_fishing_rod_geometry_places_bobber_inside_pond():
    pond = pygame.Rect(100, 80, 300, 200)

    geometry = fishing_rod_geometry(pond)

    assert pond.collidepoint(geometry["bobber_center"])
    assert geometry["line_start"][1] < geometry["bobber_center"][1]


def test_fishing_rod_geometry_uses_player_hand_as_handle():
    pond = pygame.Rect(220, 120, 260, 160)
    player_rect = pygame.Rect(120, 165, 32, 32)

    geometry = fishing_rod_geometry(pond, player_rect=player_rect)

    assert abs(geometry["handle"][0] - player_rect.right) <= 4
    assert player_rect.top <= geometry["handle"][1] <= player_rect.bottom
    assert geometry["rod_tip"][0] > geometry["handle"][0]
    assert pond.collidepoint(geometry["bobber_center"])


def test_fishing_waiting_panel_does_not_overlap_pond_bounds():
    surface_rect = pygame.Rect(0, 0, 1000, 620)
    pond = pygame.Rect(300, 180, 360, 220)

    panel = fishing_panel_rect(surface_rect, pond_bounds=pond, bite_detected=False)

    assert not panel.colliderect(pond)


def test_fishing_tension_marker_animates_while_waiting_for_bite():
    game = FishingMinigame(_fish(), random.Random(1))
    before = game.tension

    assert game.update(250) is None

    assert game.bite_detected is False
    assert game.tension != before


def test_attract_visible_fish_to_bobber_moves_only_closest_two_gradually():
    fish = [
        VisibleFish("red", 1.0, (90.0, 100.0), 0.0, 0.0, 1000.0),
        VisibleFish("pink", 1.0, (120.0, 100.0), 0.0, 0.0, 1000.0),
        VisibleFish("white", 1.0, (220.0, 100.0), 0.0, 0.0, 1000.0),
    ]
    bobber = (100.0, 100.0)

    attract_visible_fish_to_bobber(fish, bobber, dt_ms=1000.0, max_fish=2, speed_px_per_s=10.0)

    assert fish[0].pos == (100.0, 100.0)
    assert fish[1].pos == (110.0, 100.0)
    assert fish[2].pos == (220.0, 100.0)


def test_fishing_draw_does_not_raise(pygame_surface):
    font = pygame.font.Font(None, 20)
    FishingMinigame(_fish(), random.Random(1)).draw(pygame_surface, font)
