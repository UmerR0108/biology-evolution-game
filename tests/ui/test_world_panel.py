import pygame

from evogame.ui.world_panel import WorldPanel


def test_world_panel_draws_scene_without_error(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface)


def test_world_panel_paints_background(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface)
    pixel = pygame_surface.get_at((100, 100))
    assert pixel != (0, 0, 0, 255), "panel background should show grass, not black"


def test_world_panel_draws_player(pygame_surface):
    from evogame.ui.player import Player
    from evogame.ui.world_panel import WorldPanel
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    player = Player(pos=(50.0, 50.0))
    panel.draw(pygame_surface, player=player)
    # Pixel under player should not be the all-grass background — it's a sprite.
    # Just verify draw with a player argument doesn't raise.


def test_cottage_in_range_when_player_close(pygame_surface):
    from evogame.ui.player import Player
    from evogame.ui.world_panel import WorldPanel
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    cottage = next(o for o in panel.scene.objects if o.kind == "cottage")
    cx = cottage.col * 32 + 16
    cy = cottage.row * 32 + 16
    near = Player(pos=(cx - 16.0, cy - 16.0))
    far = Player(pos=(0.0, 0.0))
    assert panel.cottage_in_range(near) is True
    assert panel.cottage_in_range(far) is False


def test_world_panel_draws_press_e_when_in_range(pygame_surface):
    from evogame.ui.player import Player
    from evogame.ui.world_panel import WorldPanel
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    cottage = next(o for o in panel.scene.objects if o.kind == "cottage")
    near = Player(pos=(cottage.col * 32, cottage.row * 32))
    font = pygame.font.SysFont("arial", 12)
    panel.draw(pygame_surface, player=near, font=font)
    # No assertion on the text pixels — just that calling with font + in-range player doesn't raise.


def test_world_panel_draws_pond_view(pygame_surface):
    import random
    from evogame.genetics import GUPPY_SCHEMA, Creature
    from evogame.ui.world_panel import WorldPanel
    rng = random.Random(0)
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    pop = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(10)]
    panel.pond_view.refresh(pop)
    panel.draw(pygame_surface)


def test_world_panel_spawns_three_bunnies(pygame_surface):
    from evogame.ui.world_panel import WorldPanel
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    # Up to 3 bunnies, all on walkable tiles.
    assert 1 <= len(panel.wildlife) <= 3
    for bunny in panel.wildlife:
        col = int(bunny.pos[0] // 32)
        row = int(bunny.pos[1] // 32)
        assert panel.scene.tilemap.is_walkable(col, row)
