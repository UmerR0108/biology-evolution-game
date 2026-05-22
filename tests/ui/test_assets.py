import pygame

from evogame.ui.assets import load_tileset, load_fish_base, load_bunny_frames


def test_load_tileset_returns_named_surfaces(pygame_surface):
    tiles = load_tileset()
    for name in ("grass", "water_nw", "water_ne", "water_sw", "water_se",
                 "tree", "cottage", "char_down"):
        assert name in tiles, f"missing tile: {name}"
        assert isinstance(tiles[name], pygame.Surface)
        w, h = tiles[name].get_size()
        assert w > 0 and h > 0


def test_load_fish_base_is_a_surface(pygame_surface):
    fish = load_fish_base()
    assert isinstance(fish, pygame.Surface)
    w, h = fish.get_size()
    assert w > 0 and h > 0


def test_load_bunny_frames_returns_per_direction_lists(pygame_surface):
    frames = load_bunny_frames()
    for direction in ("down", "up", "left", "right"):
        assert direction in frames, f"missing direction: {direction}"
        assert len(frames[direction]) >= 1
        for surf in frames[direction]:
            assert isinstance(surf, pygame.Surface)


def test_decoration_sprites_are_visible(pygame_surface):
    from evogame.ui.assets import load_decoration_sprite

    for kind in (
        "bush", "yellow_bush", "rock", "small_rock", "flower_red",
        "flower_yellow", "stump", "log", "mushroom",
    ):
        sprite = load_decoration_sprite(kind)
        opaque_pixels = 0
        for x in range(sprite.get_width()):
            for y in range(sprite.get_height()):
                if sprite.get_at((x, y)).a:
                    opaque_pixels += 1
        assert opaque_pixels > 20, f"{kind} sprite should not be an empty slice"


def test_load_player_walk_frames_returns_independent_surfaces(pygame_surface):
    from evogame.ui.assets import load_player_walk_frames
    frames = load_player_walk_frames()
    for direction in ("down", "up", "left", "right"):
        assert direction in frames, f"missing direction: {direction}"
        assert len(frames[direction]) >= 2, f"{direction} should have >=2 walk frames"
        for surf in frames[direction]:
            assert isinstance(surf, pygame.Surface)
            w, h = surf.get_size()
            assert w > 0 and h > 0
    # Mutate-and-read independence check.
    sentinel = (255, 0, 255, 255)
    before_up = frames["up"][0].get_at((0, 0))
    frames["down"][0].fill(sentinel)
    assert frames["up"][0].get_at((0, 0)) == before_up, \
        "mutating frames['down'] must not affect frames['up']"


def test_load_bunny_frames_returns_independent_surfaces(pygame_surface):
    frames = load_bunny_frames()
    sentinel = (255, 0, 255, 255)
    before_up = frames["up"][0].get_at((0, 0))
    frames["down"][0].fill(sentinel)
    assert frames["up"][0].get_at((0, 0)) == before_up, \
        "mutating bunny frames['down'] must not affect frames['up']"


def test_load_bunny_frames_use_complete_paired_sprites(pygame_surface):
    frames = load_bunny_frames()

    for direction_frames in frames.values():
        for frame in direction_frames:
            # MiniBunny stores each visible bunny across a left/right 16px pair.
            # A frame that is only one half has width 16 and alpha touching an edge.
            assert frame.get_width() >= 32
            bbox = frame.get_bounding_rect()
            assert bbox.left > 0
            assert bbox.right < frame.get_width()


def test_load_tree_sprite_returns_surface(pygame_surface):
    from evogame.ui.assets import load_tree_sprite
    surf = load_tree_sprite("6", "green")
    assert isinstance(surf, pygame.Surface)
    w, h = surf.get_size()
    assert w > 0 and h > 0
    # Tree 6 is a tall tree — height should exceed width.
    assert h > w


def test_load_tree_sprite_supports_color_variants(pygame_surface):
    from evogame.ui.assets import load_tree_sprite
    a = load_tree_sprite("6", "green")
    b = load_tree_sprite("6", "teal")
    # Different colors → different surfaces (after independent loads).
    assert a is not b


def test_load_pond_composite_returns_surface(pygame_surface):
    from evogame.ui.assets import load_pond_composite
    surf = load_pond_composite()
    assert isinstance(surf, pygame.Surface)
    w, h = surf.get_size()
    assert w >= 32 and h >= 32  # nontrivial size


def test_load_tileset_includes_reference_forest_biome_tiles(pygame_surface):
    tiles = load_tileset()
    for name in (
        "forest_grass", "forest_grass_light", "forest_grass_dark",
        "forest_path_soft", "cliff_top", "cliff_face", "water_center",
    ):
        assert name in tiles
        assert isinstance(tiles[name], pygame.Surface)
        assert tiles[name].get_size() == (16, 16)


def test_load_environment_sheets_for_new_art_direction(pygame_surface):
    from evogame.ui.assets import load_environment_sheet
    for name in (
        "waterfall_autotiles",
        "calm_water_autotiles",
        "water_sheet",
        "building_sheet",
        "item_sheet",
        "grass_sheet",
        "cliff_sheet",
        "forest_reference",
    ):
        surf = load_environment_sheet(name)
        assert isinstance(surf, pygame.Surface)
        assert surf.get_width() > 0
        assert surf.get_height() > 0


def test_load_cottage_sprite_uses_building_sheet(pygame_surface):
    from evogame.ui.assets import load_cottage_sprite
    surf = load_cottage_sprite()
    assert isinstance(surf, pygame.Surface)
    assert surf.get_width() >= 100
    assert surf.get_height() >= 80


def test_load_decoration_sprite_returns_item_sprite(pygame_surface):
    from evogame.ui.assets import load_decoration_sprite
    surf = load_decoration_sprite("bush")
    assert isinstance(surf, pygame.Surface)
    assert surf.get_width() > 0
    assert surf.get_height() > 0
