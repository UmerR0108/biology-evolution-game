from evogame.ui.tilemap import Tilemap, TILE_PIXELS


def test_tilemap_dimensions():
    grid = [
        ["grass", "grass", "water_nw"],
        ["grass", "grass", "water_sw"],
    ]
    tm = Tilemap(grid)
    assert tm.cols == 3
    assert tm.rows == 2
    assert tm.pixel_width == 3 * TILE_PIXELS
    assert tm.pixel_height == 2 * TILE_PIXELS


def test_tilemap_is_walkable_water_blocks():
    grid = [
        ["grass", "water_nw"],
        ["grass", "water_sw"],
    ]
    tm = Tilemap(grid)
    assert tm.is_walkable(0, 0) is True   # grass
    assert tm.is_walkable(1, 0) is False  # water


def test_tilemap_draw_paints_grass_pixels(pygame_surface):
    grid = [["grass"] * 4 for _ in range(4)]
    tm = Tilemap(grid)
    tm.draw(pygame_surface, origin=(0, 0))
    # Grass tile is not pure black; somewhere in the painted region pixel != black.
    pixel = pygame_surface.get_at((TILE_PIXELS // 2, TILE_PIXELS // 2))
    assert pixel != (0, 0, 0, 255)


def test_forest_scene_has_pond_and_dimensions():
    from evogame.ui.tilemap import build_forest_scene, TILE_PIXELS
    scene = build_forest_scene()
    # scene must fit inside 1000x596 (window height minus 24px status strip)
    assert scene.tilemap.pixel_width <= 1000
    assert scene.tilemap.pixel_height <= 596
    assert scene.tilemap.pixel_width >= 32 * TILE_PIXELS or scene.tilemap.cols >= 28
    # has at least one pond tile and at least one tree object
    pond_tiles = [
        (c, r) for r in range(scene.tilemap.rows) for c in range(scene.tilemap.cols)
        if scene.tilemap.grid[r][c].startswith("water_")
    ]
    assert len(pond_tiles) >= 4, "scene must include a 2x2-or-larger pond"
    assert any(o.kind.startswith("tree_") for o in scene.objects)
    assert any(o.kind in {"bush", "rock", "flower_red", "flower_yellow"} for o in scene.objects)


def test_forest_scene_pond_bounds_are_inside_grid():
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    assert bounds.width > 0 and bounds.height > 0
    assert bounds.left >= 0 and bounds.top >= 0
    assert bounds.right <= scene.tilemap.pixel_width
    assert bounds.bottom <= scene.tilemap.pixel_height
    swim = scene.pond_swim_bounds()
    assert bounds.contains(swim)
    assert swim.width < bounds.width
    assert swim.height < bounds.height


def test_area_scene_builders_have_expected_id_and_spawn():
    from evogame.ui.tilemap import build_deep_forest_scene, build_forest_scene, build_home_scene
    scenes = [build_home_scene(), build_forest_scene(), build_deep_forest_scene()]
    assert {scene.area_id for scene in scenes} == {"home", "pond", "forest"}
    for scene in scenes:
        assert scene.tilemap.is_walkable(
            int(scene.spawn[0] // TILE_PIXELS),
            int(scene.spawn[1] // TILE_PIXELS),
        )


def test_deep_forest_scene_has_clearing_water_and_dense_edges():
    from evogame.ui.tilemap import build_deep_forest_scene
    scene = build_deep_forest_scene()
    water_tiles = [
        (c, r) for r in range(scene.tilemap.rows) for c in range(scene.tilemap.cols)
        if scene.tilemap.grid[r][c].startswith("water_")
    ]
    edge_trees = [
        obj for obj in scene.objects
        if obj.kind.startswith("tree_") and (obj.col <= 3 or obj.col >= 24 or obj.row <= 2 or obj.row >= 13)
    ]
    assert len(water_tiles) >= 6
    assert len(edge_trees) >= 12
    assert scene.tilemap.grid[9][15] in {"forest_light", "forest_floor", "forest_grass_light"}


def test_deep_forest_scene_uses_reference_like_layers():
    from evogame.ui.tilemap import build_deep_forest_scene
    scene = build_deep_forest_scene()
    names = {name for row in scene.tilemap.grid for name in row}

    assert {"forest_grass", "forest_grass_light", "forest_grass_dark"} <= names
    assert any(name.startswith("water_") for name in names)
    assert any(name.startswith("cliff_") for name in names)
    assert any(name.startswith("forest_path") or name == "path" for name in names)


def test_deep_forest_cliff_tiles_are_not_walkable():
    from evogame.ui.tilemap import build_deep_forest_scene
    scene = build_deep_forest_scene()
    cliff_tiles = [
        (c, r) for r in range(scene.tilemap.rows) for c in range(scene.tilemap.cols)
        if scene.tilemap.grid[r][c].startswith("cliff_")
    ]
    assert cliff_tiles
    for c, r in cliff_tiles:
        assert scene.tilemap.is_walkable(c, r) is False


def test_deep_forest_objects_are_not_authored_offscreen():
    from evogame.ui.tilemap import build_deep_forest_scene
    scene = build_deep_forest_scene()
    for obj in scene.objects:
        assert 0 <= obj.col < scene.tilemap.cols
        assert 0 <= obj.row < scene.tilemap.rows


def test_deep_forest_has_reference_like_prop_density():
    from evogame.ui.tilemap import build_deep_forest_scene
    scene = build_deep_forest_scene()
    kinds = [obj.kind for obj in scene.objects]

    assert sum(k.startswith("tree_") for k in kinds) >= 24
    assert sum(k in {"bush", "yellow_bush"} for k in kinds) >= 10
    assert kinds.count("mushroom") >= 4
    assert sum(k in {"rock", "small_rock"} for k in kinds) >= 6
    assert sum(k in {"log", "stump"} for k in kinds) >= 4
