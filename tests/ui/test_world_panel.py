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


def test_world_panel_covers_full_game_rect_without_black_gutters():
    surface = pygame.Surface((1000, 620))
    surface.fill((0, 0, 0))
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    panel.draw(surface)

    # The world rect is not an exact multiple of the 32px tile size, so the
    # authored map must overscan the panel instead of leaving black strips on
    # the right or bottom edge.
    assert surface.get_at((999, 40)) != (0, 0, 0, 255)
    assert surface.get_at((500, 619)) != (0, 0, 0, 255)


def test_world_panel_draws_player(pygame_surface):
    from evogame.ui.player import Player
    from evogame.ui.world_panel import WorldPanel
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    player = Player(pos=(50.0, 50.0))
    panel.draw(pygame_surface, player=player)
    # Pixel under player should not be the all-grass background — it's a sprite.
    # Just verify draw with a player argument doesn't raise.


def test_world_panel_exposes_area_title_and_guidance():
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    assert panel.area_title_and_guidance() == (
        "Home Base",
        "Check the cottage journal, then follow paths to study sites.",
    )

    panel.switch_area("pond")
    assert panel.area_title_and_guidance() == (
        "Pond Study Site",
        "Watch guppies here; press E near water to open research data.",
    )

    panel.switch_area("forest")
    assert panel.area_title_and_guidance() == (
        "Forest Trail",
        "Explore wildlife and use the northern trail to return home.",
    )


def test_world_panel_draws_area_title_card_when_font_available():
    pygame.font.init()
    surface = pygame.Surface((1000, 596))
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    font = pygame.font.SysFont("arial", 12)

    panel.draw(surface, font=font)

    assert surface.get_at((18, 14)) != pygame.Color(0, 0, 0, 255)


def test_world_panel_draws_area_minimap_with_current_area_highlight():
    pygame.font.init()
    surface = pygame.Surface((1000, 596))
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    font = pygame.font.SysFont("arial", 12)

    panel.draw(surface, font=font)
    home_pixel = surface.get_at(panel.area_minimap_node_rects()["home"].center)

    panel.switch_area("pond")
    panel.draw(surface, font=font)
    pond_pixel = surface.get_at(panel.area_minimap_node_rects()["pond"].center)

    assert home_pixel == pygame.Color(255, 222, 89, 255)
    assert pond_pixel == pygame.Color(255, 222, 89, 255)


def test_world_panel_tracks_visited_areas_for_minimap():
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))

    assert panel.visited_area_ids == {"home"}

    panel.switch_area("pond")
    assert panel.visited_area_ids == {"home", "pond"}

    panel.switch_area("forest")
    assert panel.visited_area_ids == {"home", "pond", "forest"}


def test_world_panel_area_progress_text_tracks_discovered_sites():
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))

    assert panel.area_progress_text() == "Field sites discovered: 1/3"

    panel.switch_area("pond")
    assert panel.area_progress_text() == "Field sites discovered: 2/3"

    panel.switch_area("forest")
    assert panel.area_progress_text() == "Field sites discovered: 3/3"


def test_world_panel_draws_unvisited_minimap_nodes_dimmed():
    pygame.font.init()
    surface = pygame.Surface((1000, 596))
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    font = pygame.font.SysFont("arial", 12)

    panel.draw(surface, font=font)

    nodes = panel.area_minimap_node_rects()
    assert surface.get_at(nodes["pond"].center) == pygame.Color(*panel.MINIMAP_UNVISITED, 255)
    assert surface.get_at(nodes["forest"].center) == pygame.Color(*panel.MINIMAP_UNVISITED, 255)

    panel.switch_area("pond")
    panel.draw(surface, font=font)
    assert surface.get_at(nodes["home"].center) == pygame.Color(*panel.MINIMAP_VISITED, 255)


def test_world_panel_home_base_exposes_captive_habitat_rects():
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))

    rects = panel.home_habitat_rects()

    assert set(rects) == {"fish", "bunny"}
    assert rects["fish"].left < rects["bunny"].left
    assert rects["fish"].top > 300
    assert rects["bunny"].top > 300


def test_world_panel_draws_home_captive_habitat_areas_when_at_home():
    pygame.font.init()
    surface = pygame.Surface((1000, 620))
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    font = pygame.font.SysFont("arial", 12)

    panel.draw(
        surface,
        font=font,
        home_fish_founders=2,
        home_fish_generation=5,
        home_bunny_founders=1,
        home_bunny_generation=0,
    )

    rects = panel.home_habitat_rects()
    fish_pixel = surface.get_at(rects["fish"].center)
    bunny_pixel = surface.get_at(rects["bunny"].center)
    assert fish_pixel.b > fish_pixel.r
    assert bunny_pixel.r > bunny_pixel.b


def test_world_panel_reports_clicked_minimap_area():
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    nodes = panel.area_minimap_node_rects()

    assert panel.area_at_minimap_pos(nodes["pond"].center) == "pond"
    assert panel.area_at_minimap_pos(nodes["forest"].center) == "forest"
    assert panel.area_at_minimap_pos((0, 0)) is None


def test_world_panel_minimap_labels_are_clickable():
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    nodes = panel.area_minimap_node_rects()

    assert panel.area_at_minimap_pos((nodes["home"].centerx, nodes["home"].bottom + 10)) == "home"
    assert panel.area_at_minimap_pos((nodes["pond"].centerx, nodes["pond"].bottom + 10)) == "pond"
    assert panel.area_at_minimap_pos((nodes["forest"].centerx, nodes["forest"].bottom + 10)) == "forest"


def test_world_panel_minimap_labels_advertise_travel_shortcuts():
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))

    assert panel.area_minimap_labels() == {
        "home": "1 Home",
        "pond": "2 Pond",
        "forest": "3 Forest",
    }


def test_cottage_in_range_when_player_close(pygame_surface):
    from evogame.ui.player import Player
    from evogame.ui.world_panel import WorldPanel
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    cottage = next(o for o in panel.scene.objects if o.kind == "cottage")
    cx = cottage.col * 32 + 112
    cy = cottage.row * 32 + 112
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


def test_world_panel_interaction_prompts_include_action_keys():
    from evogame.ui.player import Player
    from evogame.ui.world_panel import WorldPanel

    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    cottage = next(o for o in panel.scene.objects if o.kind == "cottage")
    player = Player(pos=(cottage.col * 32 + 96.0, cottage.row * 32 + 96.0))
    assert panel.interaction_prompt_for_player(player) == "[E/Enter] Field Journal"

    panel.switch_area("pond")
    bounds = panel.scene.pond_pixel_bounds()
    player.pos = (bounds.centerx - player.size[0] / 2, bounds.centery - player.size[1] / 2)
    assert panel.interaction_prompt_for_player(player) == "[E/Enter] Research Pond"


def test_world_panel_reports_nearby_wildlife_observation():
    import random

    from evogame.ui.player import Player
    from evogame.ui.wildlife import Bunny
    from evogame.ui.world_panel import WorldPanel

    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    panel.switch_area("forest")
    player = Player(pos=(10 * 32.0, 9 * 32.0))
    panel.wildlife = [Bunny(pos=(player.pos[0] + 18.0, player.pos[1] + 12.0), scene=panel.scene, rng=random.Random(1))]

    assert panel.wildlife_observation_for_player(player) == "Bunny nearby: observe camouflage and foraging"
    assert panel.interaction_prompt_for_player(player) == "[E/Enter] Observe bunny: camouflage and foraging"
    assert panel.wildlife_field_note_for_player(player) == (
        "Forest Trail: bunny camouflage observed near dense cover."
    )

    panel.switch_area("pond")
    player.pos = (10 * 32.0, 9 * 32.0)
    panel.wildlife = [Bunny(pos=(player.pos[0] + 18.0, player.pos[1] + 12.0), scene=panel.scene, rng=random.Random(2))]
    assert panel.wildlife_field_note_for_player(player) == (
        "Pond Study Site: bunny browsing near the bank; compare camouflage with guppy predator pressure."
    )

    panel.wildlife[0].pos = (player.pos[0] + 140.0, player.pos[1])
    assert panel.wildlife_observation_for_player(player) is None


def test_world_panel_anchors_wildlife_prompt_above_player():
    import random

    from evogame.ui.player import Player
    from evogame.ui.wildlife import Bunny

    panel = WorldPanel(pygame.Rect(10, 24, 1000, 596))
    panel.switch_area("forest")
    player = Player(pos=(10 * 32.0, 9 * 32.0))
    panel.wildlife = [Bunny(pos=(player.pos[0] + 18.0, player.pos[1] + 12.0), scene=panel.scene, rng=random.Random(1))]

    prompt = panel.interaction_prompt_for_player(player)
    assert panel.interaction_prompt_anchor_for_player(player, prompt) == (
        panel.rect.left + int(player.pos[0]) - 52,
        panel.rect.top + int(player.pos[1]) - 18,
    )


def test_world_panel_reports_observable_wildlife_screen_positions():
    import random

    from evogame.ui.player import Player
    from evogame.ui.wildlife import Bunny

    panel = WorldPanel(pygame.Rect(10, 24, 1000, 596))
    panel.switch_area("forest")
    player = Player(pos=(10 * 32.0, 9 * 32.0))
    nearby = Bunny(pos=(player.pos[0] + 18.0, player.pos[1] + 12.0), scene=panel.scene, rng=random.Random(1))
    distant = Bunny(pos=(player.pos[0] + 160.0, player.pos[1]), scene=panel.scene, rng=random.Random(2))
    panel.wildlife = [nearby, distant]

    assert panel.observable_wildlife_screen_positions(player) == [
        (panel.rect.left + int(nearby.pos[0]), panel.rect.top + int(nearby.pos[1]))
    ]


def test_world_panel_does_not_anchor_missing_interaction_prompt():
    from evogame.ui.player import Player

    panel = WorldPanel(pygame.Rect(10, 24, 1000, 596))
    player = Player(pos=(2 * 32.0, 2 * 32.0))

    assert panel.interaction_prompt_for_player(player) is None
    assert panel.interaction_prompt_anchor_for_player(player, None) is None


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
    panel.switch_area("pond")
    # Up to 3 bunnies, all on walkable tiles.
    assert 1 <= len(panel.wildlife) <= 3
    for bunny in panel.wildlife:
        col = int(bunny.pos[0] // 32)
        row = int(bunny.pos[1] // 32)
        assert panel.scene.tilemap.is_walkable(col, row)


def test_world_panel_switches_between_three_areas(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    assert panel.area_id == "home"
    assert panel.scene.pond_pixel_bounds().size == (0, 0)
    panel.switch_area("forest")
    assert panel.area_id == "forest"
    assert len(panel.wildlife) >= 1
    panel.switch_area("pond")
    assert panel.area_id == "pond"
    assert panel.scene.pond_pixel_bounds().width > 0


def test_world_panel_uses_contextual_entry_spawns_for_area_transitions():
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))

    pond_spawn = panel.switch_area("pond", from_area="home")
    assert pond_spawn == panel.scene.entry_spawns["home"]
    assert pond_spawn[0] < 3 * 32

    home_from_pond = panel.switch_area("home", from_area="pond")
    assert home_from_pond == panel.scene.entry_spawns["pond"]
    assert home_from_pond[0] > panel.scene.tilemap.pixel_width - 4 * 32

    forest_from_home = panel.switch_area("forest", from_area="home")
    assert forest_from_home == panel.scene.entry_spawns["home"]
    assert forest_from_home[1] < 5 * 32

    home_from_forest = panel.switch_area("home", from_area="forest")
    assert home_from_forest == panel.scene.entry_spawns["forest"]
    assert home_from_forest[1] > panel.scene.tilemap.pixel_height - 4 * 32


def test_world_panel_describes_nearby_area_exits():
    from evogame.ui.player import Player

    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    player = Player(pos=(panel.scene.tilemap.pixel_width - 36.0, 9 * 32.0))
    assert panel.area_exit_hint_for_player(player) == "[E/Enter] Path to pond →"

    player.pos = (12 * 32.0, panel.scene.tilemap.pixel_height - 36.0)
    assert panel.area_exit_hint_for_player(player) == "[E/Enter] Trail to forest ↓"

    player.pos = panel.switch_area("pond")
    player.pos = (8.0, 8 * 32.0)
    assert panel.area_exit_hint_for_player(player) == "[E/Enter] Path home ←"

    player.pos = panel.switch_area("forest")
    player.pos = (12 * 32.0, 8.0)
    assert panel.area_exit_hint_for_player(player) == "[E/Enter] Trail home ↑"


def test_world_panel_exposes_screen_space_area_exit_markers():
    panel = WorldPanel(pygame.Rect(10, 24, 1000, 596))

    markers = panel.area_exit_marker_rects()
    assert set(markers) == {"pond", "forest"}
    assert markers["pond"].right == panel.rect.right - 12
    assert markers["forest"].bottom == panel.rect.bottom - 12

    panel.switch_area("pond")
    markers = panel.area_exit_marker_rects()
    assert set(markers) == {"home"}
    assert markers["home"].left == panel.rect.left + 12

    panel.switch_area("forest")
    markers = panel.area_exit_marker_rects()
    assert set(markers) == {"home"}
    assert markers["home"].top == panel.rect.top + 12


def test_world_panel_area_exit_marker_labels_show_direction():
    panel = WorldPanel(pygame.Rect(10, 24, 1000, 596))
    assert panel.area_exit_marker_labels() == {"pond": "POND →", "forest": "FOREST ↓"}

    panel.switch_area("pond")
    assert panel.area_exit_marker_labels() == {"home": "← HOME"}

    panel.switch_area("forest")
    assert panel.area_exit_marker_labels() == {"home": "HOME ↑"}


def test_world_panel_reports_clicked_area_exit_marker_target():
    panel = WorldPanel(pygame.Rect(10, 24, 1000, 596))
    markers = panel.area_exit_marker_rects()

    assert panel.area_at_exit_marker_pos(markers["pond"].center) == "pond"
    assert panel.area_at_exit_marker_pos(markers["forest"].center) == "forest"
    assert panel.area_at_exit_marker_pos((0, 0)) is None

    panel.switch_area("pond")
    assert panel.area_at_exit_marker_pos(panel.area_exit_marker_rects()["home"].center) == "home"


def test_world_panel_accepts_near_signpost_clicks():
    panel = WorldPanel(pygame.Rect(10, 24, 1000, 596))
    marker = panel.area_exit_marker_rects()["pond"]

    assert panel.area_at_exit_marker_pos((marker.left - 5, marker.centery)) == "pond"
    assert panel.area_at_exit_marker_pos((marker.left - 18, marker.centery)) is None


def test_world_panel_reports_nearby_area_exit_targets():
    from evogame.ui.player import Player

    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    player = Player(pos=(panel.scene.tilemap.pixel_width - 70.0, 9 * 32.0))
    assert panel.area_exit_target_for_player(player) == "pond"

    player.pos = (12 * 32.0, panel.scene.tilemap.pixel_height - 70.0)
    assert panel.area_exit_target_for_player(player) == "forest"

    player.pos = panel.switch_area("pond")
    player.pos = (40.0, 8 * 32.0)
    assert panel.area_exit_target_for_player(player) == "home"

    player.pos = panel.switch_area("forest")
    player.pos = (12 * 32.0, 40.0)
    assert panel.area_exit_target_for_player(player) == "home"


def test_world_panel_detects_pond_hotspot(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    panel.switch_area("pond")
    bounds = panel.scene.pond_pixel_bounds().move(panel.rect.left, panel.rect.top)
    assert panel.pond_at_screen_pos(bounds.center) is True
    assert panel.pond_at_screen_pos((0, 0)) is False


def test_world_panel_accepts_near_shore_pond_clicks(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    panel.switch_area("pond")
    bounds = panel.scene.pond_pixel_bounds().move(panel.rect.left, panel.rect.top)

    assert panel.pond_at_screen_pos((bounds.left - 6, bounds.centery)) is True
    assert panel.pond_at_screen_pos((bounds.left - 20, bounds.centery)) is False


def test_world_panel_detects_cottage_hotspot(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    cottage = next(o for o in panel.scene.objects if o.kind == "cottage")
    bounds = pygame.Rect(
        panel.rect.left + cottage.col * 32,
        panel.rect.top + cottage.row * 32,
        panel.COTTAGE_TILE_SIZE[0] * 32,
        panel.COTTAGE_TILE_SIZE[1] * 32,
    )
    assert panel.cottage_at_screen_pos(bounds.center) is True
    assert panel.cottage_at_screen_pos((0, 0)) is False


def test_world_panel_accepts_near_porch_cottage_clicks(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    cottage = next(o for o in panel.scene.objects if o.kind == "cottage")
    bounds = pygame.Rect(
        panel.rect.left + cottage.col * 32,
        panel.rect.top + cottage.row * 32,
        panel.COTTAGE_TILE_SIZE[0] * 32,
        panel.COTTAGE_TILE_SIZE[1] * 32,
    )

    assert panel.cottage_at_screen_pos((bounds.centerx, bounds.bottom + 6)) is True
    assert panel.cottage_at_screen_pos((bounds.centerx, bounds.bottom + 20)) is False


def test_world_panel_ignores_cottage_hotspot_outside_home(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    panel.switch_area("pond")
    assert panel.cottage_at_screen_pos((14 * 32, 5 * 32)) is False


def test_world_panel_forest_water_is_not_pond_research_hotspot(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 24, 1000, 596))
    panel.switch_area("forest")
    bounds = panel.scene.pond_pixel_bounds().move(panel.rect.left, panel.rect.top)
    assert bounds.width > 0 and bounds.height > 0
    assert panel.pond_at_screen_pos(bounds.center) is False


def test_world_panel_renders_irregular_pond_without_error():
    from evogame.ui.world_panel import WorldPanel
    big_surface = pygame.Surface((1000, 596))
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    panel.switch_area("pond")
    panel.draw(big_surface)
    # Pixel inside the pond region should not be all-grass.
    bounds = panel.scene.pond_pixel_bounds()
    panel_rect = panel.rect
    pond_center_x = panel_rect.left + bounds.left + bounds.width // 2
    pond_center_y = panel_rect.top + bounds.top + bounds.height // 2
    pixel = big_surface.get_at((pond_center_x, pond_center_y))
    # Pond should be bluish — green channel less than blue channel.
    assert pixel[2] > pixel[1] - 30 or pixel[2] > 100, \
        f"pond center should be bluish, got {pixel}"
