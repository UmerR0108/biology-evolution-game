import pygame

from evogame.ui.app import App


def test_app_initializes_without_error():
    app = App(seed=0)
    assert app.sim.generation == 0
    assert app.running is True
    assert app.world_panel.area_id == "home"
    assert app.player.pos == app.world_panel.scene.spawn
    app.shutdown()


def test_app_does_not_advance_until_research_started():
    app = App(seed=0)
    app.step_one_frame(1100)
    assert app.sim.generation == 0
    app.shutdown()


def test_app_advances_generation_when_pond_research_running():
    app = App(seed=0)
    app.journal.open = True
    app.journal.paused = False
    app.step_one_frame(1100)
    assert app.sim.generation >= 1
    app.shutdown()


def test_app_does_not_advance_when_paused():
    app = App(seed=0)
    app.journal.open = True
    app.journal.paused = True
    app.step_one_frame(2000)
    assert app.sim.generation == 0
    app.shutdown()


def test_app_runs_for_n_generations():
    app = App(seed=0)
    app.journal.open = True
    app.journal.paused = False
    app.run_for_generations(5, max_frames=200)
    assert app.sim.generation == 5
    app.shutdown()


def test_app_does_not_advance_when_extinct():
    app = App(seed=0)
    app.journal.open = True
    app.journal.paused = False
    app.sim.extinct = True
    app.step_one_frame(2000)
    assert app.sim.generation == 0
    app.shutdown()


def test_app_quit_event_stops_running():
    app = App(seed=0)
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    app.step_one_frame(0)
    assert app.running is False
    app.shutdown()


def test_app_j_key_toggles_journal():
    app = App(seed=0)
    assert app.journal.open is False
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_j}))
    app.step_one_frame(0)
    assert app.journal.open is True
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_j}))
    app.step_one_frame(0)
    assert app.journal.open is False
    app.shutdown()


def test_app_tab_cycles_field_sites_for_quick_travel():
    app = App(seed=0)

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
    app.step_one_frame(0)
    assert app.world_panel.area_id == "pond"
    assert app.player.pos == app.world_panel.scene.entry_spawns["home"]

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
    app.step_one_frame(0)
    assert app.world_panel.area_id == "forest"

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
    app.step_one_frame(0)
    assert app.world_panel.area_id == "home"
    app.shutdown()


def test_app_escape_closes_journal_when_open():
    app = App(seed=0)
    app.journal.open = True
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    app.step_one_frame(0)
    assert app.journal.open is False
    assert app.running is True
    app.shutdown()


def test_app_escape_quits_when_journal_closed():
    app = App(seed=0)
    assert app.journal.open is False
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    app.step_one_frame(0)
    assert app.running is False
    app.shutdown()


def test_app_e_near_cottage_opens_journal():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("home")
    cottage = next(o for o in app.world_panel.scene.objects if o.kind == "cottage")
    from evogame.ui.tilemap import TILE_PIXELS
    app.player.pos = (cottage.col * TILE_PIXELS + 96.0, cottage.row * TILE_PIXELS + 96.0)
    assert app.world_panel.cottage_in_range(app.player) is True
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)
    assert app.journal.open is True
    app.shutdown()


def test_app_e_near_cottage_records_home_base_note_once():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("home")
    cottage = next(o for o in app.world_panel.scene.objects if o.kind == "cottage")
    from evogame.ui.tilemap import TILE_PIXELS
    app.player.pos = (cottage.col * TILE_PIXELS + 96.0, cottage.row * TILE_PIXELS + 96.0)

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)
    app.journal.open = False
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert app.journal.field_notes == [
        "Home Base survey: checked equipment and journal access before field work."
    ]
    app.shutdown()


def test_app_status_strip_confirms_home_base_note_saved():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("home")
    cottage = next(o for o in app.world_panel.scene.objects if o.kind == "cottage")
    from evogame.ui.tilemap import TILE_PIXELS
    app.player.pos = (cottage.col * TILE_PIXELS + 96.0, cottage.row * TILE_PIXELS + 96.0)
    captured = {}

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)

    app.status_strip.draw = fake_draw

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert captured["interaction_prompt"] == "Home base note saved to field journal."
    assert captured["field_notes"] == 1
    assert captured["field_note_sites"] == 1
    assert captured["total_field_note_sites"] == 3
    app.shutdown()


def test_app_status_strip_celebrates_completed_field_note_coverage():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("home")
    cottage = next(o for o in app.world_panel.scene.objects if o.kind == "cottage")
    from evogame.ui.tilemap import TILE_PIXELS
    app.player.pos = (cottage.col * TILE_PIXELS + 96.0, cottage.row * TILE_PIXELS + 96.0)
    app.journal.add_field_note(
        "Pond Study Site survey: marked guppy sampling water and nearby predator habitat."
    )
    app.journal.add_field_note(
        "Forest Trail survey: noted dense cover and wildlife habitat for camouflage observations."
    )
    captured = {}

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)

    app.status_strip.draw = fake_draw

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert captured["interaction_prompt"] == "Field notes complete: all field sites documented."
    app.shutdown()


def test_app_status_strip_explains_duplicate_home_base_note():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("home")
    cottage = next(o for o in app.world_panel.scene.objects if o.kind == "cottage")
    from evogame.ui.tilemap import TILE_PIXELS
    app.player.pos = (cottage.col * TILE_PIXELS + 96.0, cottage.row * TILE_PIXELS + 96.0)
    app.journal.add_field_note("Home Base survey: checked equipment and journal access before field work.")
    captured = {}

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)

    app.status_strip.draw = fake_draw

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert captured["interaction_prompt"] == "Home base note already in field journal."
    app.shutdown()


def test_app_enter_key_also_interacts_near_cottage():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("home")
    cottage = next(o for o in app.world_panel.scene.objects if o.kind == "cottage")
    from evogame.ui.tilemap import TILE_PIXELS
    app.player.pos = (cottage.col * TILE_PIXELS + 96.0, cottage.row * TILE_PIXELS + 96.0)

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    app.step_one_frame(0)

    assert app.journal.open is True
    app.shutdown()


def test_app_clicking_pond_opens_research_panel():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("pond")
    bounds = app.world_panel.scene.pond_pixel_bounds().move(
        app.world_panel.rect.left,
        app.world_panel.rect.top,
    )
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": bounds.center},
    ))
    app.step_one_frame(0)
    assert app.journal.open is True
    app.shutdown()


def test_app_e_near_pond_records_guppy_sample_note():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("pond")
    bounds = app.world_panel.scene.pond_pixel_bounds()
    app.player.pos = (
        bounds.centerx - app.player.size[0] / 2,
        bounds.centery - app.player.size[1] / 2,
    )

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert app.journal.open is True
    note = app.journal.field_notes[0]
    assert note.startswith("Pond Study Site: generation 0 guppy population sampled for allele frequencies")
    assert "population 30" in note
    assert "Color phenotypes:" in note
    assert "Average body size phenotype:" in note
    app.shutdown()


def test_app_pressing_e_near_pond_announces_sample_saved():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("pond")
    bounds = app.world_panel.scene.pond_pixel_bounds()
    app.player.pos = (
        bounds.centerx - app.player.size[0] / 2,
        bounds.centery - app.player.size[1] / 2,
    )

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert app.journal.open is True
    assert app._status_message == "Pond sample saved to field journal."
    app.shutdown()


def test_app_pond_sample_can_complete_field_note_coverage():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("pond")
    bounds = app.world_panel.scene.pond_pixel_bounds()
    app.player.pos = (
        bounds.centerx - app.player.size[0] / 2,
        bounds.centery - app.player.size[1] / 2,
    )
    app.journal.add_field_note("Home Base survey: checked equipment.")
    app.journal.add_field_note("Forest Trail: bunny camouflage observed.")

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert app.journal.open is True
    assert app._status_message == "Field notes complete: all field sites documented."
    app.shutdown()


def test_app_repeated_pond_sample_announces_duplicate_note():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("pond")
    bounds = app.world_panel.scene.pond_pixel_bounds()
    app.player.pos = (
        bounds.centerx - app.player.size[0] / 2,
        bounds.centery - app.player.size[1] / 2,
    )

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)
    app.journal.open = False
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert len(app.journal.field_notes) == 1
    assert app.journal.field_notes[0].startswith(
        "Pond Study Site: generation 0 guppy population sampled for allele frequencies"
    )
    assert "population 30" in app.journal.field_notes[0]
    assert app._status_message == "Pond sample already in field journal."
    app.shutdown()


def test_app_pond_sample_note_includes_current_generation():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("pond")
    bounds = app.world_panel.scene.pond_pixel_bounds()
    app.player.pos = (
        bounds.centerx - app.player.size[0] / 2,
        bounds.centery - app.player.size[1] / 2,
    )
    app.sim.tick()
    app.sim.tick()

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    note = app.journal.field_notes[0]
    assert note.startswith("Pond Study Site: generation 2 guppy population sampled for allele frequencies")
    assert f"population {len(app.sim.population)}" in note
    assert "Color phenotypes:" in note
    app.shutdown()


def test_app_pond_sample_note_records_predator_pressure():
    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("pond")
    bounds = app.world_panel.scene.pond_pixel_bounds()
    app.player.pos = (
        bounds.centerx - app.player.size[0] / 2,
        bounds.centery - app.player.size[1] / 2,
    )
    app.sim.set_predator(True)

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert "predator pressure on" in app.journal.field_notes[0]
    app.shutdown()


def test_app_clicking_cottage_opens_journal():
    app = App(seed=0)
    cottage = next(o for o in app.world_panel.scene.objects if o.kind == "cottage")
    pos = (
        app.world_panel.rect.left + (cottage.col + 3) * 32,
        app.world_panel.rect.top + (cottage.row + 3) * 32,
    )
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": pos},
    ))
    app.step_one_frame(0)
    assert app.journal.open is True
    app.shutdown()


def test_app_clicking_backdrop_closes_open_journal():
    app = App(seed=0)
    app.journal.open = True
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": (10, 30)},
    ))
    app.step_one_frame(0)
    assert app.journal.open is False
    app.shutdown()


def test_app_area_shortcuts_switch_current_area():
    app = App(seed=0)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1}))
    app.step_one_frame(0)
    assert app.world_panel.area_id == "home"
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_3}))
    app.step_one_frame(0)
    assert app.world_panel.area_id == "forest"
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_2}))
    app.step_one_frame(0)
    assert app.world_panel.area_id == "pond"
    app.shutdown()


def test_app_first_area_shortcut_records_survey_note():
    app = App(seed=0)

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_3}))
    app.step_one_frame(0)

    assert app.journal.field_notes == [
        "Forest Trail survey: noted dense cover and wildlife habitat for camouflage observations."
    ]
    app.shutdown()


def test_app_revisiting_area_does_not_duplicate_survey_note():
    app = App(seed=0)

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_3}))
    app.step_one_frame(0)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1}))
    app.step_one_frame(0)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_3}))
    app.step_one_frame(0)

    assert app.journal.field_notes == [
        "Forest Trail survey: noted dense cover and wildlife habitat for camouflage observations."
    ]
    app.shutdown()


def test_app_status_strip_announces_area_transition():
    app = App(seed=0)
    captured = {}

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)

    app.status_strip.draw = fake_draw

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_3}))
    app.step_one_frame(0)

    assert app.world_panel.area_id == "forest"
    assert captured["interaction_prompt"] == "Entered Forest Trail."
    app.shutdown()


def test_app_current_area_shortcut_does_not_warp_player():
    app = App(seed=0)
    app.player.pos = (123.0, 234.0)

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1}))
    app.step_one_frame(0)

    assert app.world_panel.area_id == "home"
    assert app.player.pos == (123.0, 234.0)
    app.shutdown()


def test_app_current_area_shortcut_confirms_already_there():
    app = App(seed=0)
    captured = {}

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)

    app.status_strip.draw = fake_draw

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1}))
    app.step_one_frame(0)

    assert captured["interaction_prompt"] == "Already at Home Base."
    app.shutdown()


def test_app_clicking_area_minimap_switches_area():
    app = App(seed=0)
    pond_node = app.world_panel.area_minimap_node_rects()["pond"]

    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": pond_node.center},
    ))
    app.step_one_frame(0)

    assert app.world_panel.area_id == "pond"
    assert app.player.pos == app.world_panel.scene.entry_spawns["home"]
    app.shutdown()


def test_app_clicking_area_exit_marker_switches_area():
    app = App(seed=0)
    pond_marker = app.world_panel.area_exit_marker_rects()["pond"]

    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": pond_marker.center},
    ))
    app.step_one_frame(0)

    assert app.world_panel.area_id == "pond"
    assert app.player.pos == app.world_panel.scene.entry_spawns["home"]
    app.shutdown()


def test_app_clicking_current_minimap_area_does_not_warp_player():
    app = App(seed=0)
    app.player.pos = (123.0, 234.0)
    home_node = app.world_panel.area_minimap_node_rects()["home"]

    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": home_node.center},
    ))
    app.step_one_frame(0)

    assert app.world_panel.area_id == "home"
    assert app.player.pos == (123.0, 234.0)
    app.shutdown()


def test_app_p_key_reaches_open_journal_instead_of_area_shortcut():
    app = App(seed=0)
    app.world_panel.switch_area("home")
    app.journal.open = True

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_p}))
    app.step_one_frame(0)

    assert app.world_panel.area_id == "home"
    assert app.sim.pressure.predator_on is True
    app.shutdown()


def test_app_e_near_wildlife_records_field_note():
    import random

    from evogame.ui.wildlife import Bunny

    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("forest")
    app.world_panel.wildlife = [Bunny(
        pos=(app.player.pos[0] + 18.0, app.player.pos[1] + 12.0),
        scene=app.world_panel.scene,
        rng=random.Random(1),
    )]

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert app.journal.field_notes == ["Forest Trail: bunny camouflage observed near dense cover."]
    assert app.journal.open is False
    app.shutdown()



def test_app_clicking_near_wildlife_records_field_note():
    import random

    from evogame.ui.wildlife import Bunny

    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("forest")
    bunny_pos = (app.player.pos[0] + 18.0, app.player.pos[1] + 12.0)
    app.world_panel.wildlife = [Bunny(
        pos=bunny_pos,
        scene=app.world_panel.scene,
        rng=random.Random(1),
    )]

    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": (
            app.world_panel.rect.left + int(bunny_pos[0]),
            app.world_panel.rect.top + int(bunny_pos[1]),
        )},
    ))
    app.step_one_frame(0)

    assert app.journal.field_notes == ["Forest Trail: bunny camouflage observed near dense cover."]
    assert app.journal.open is False
    app.shutdown()


def test_app_clicking_bunny_prompt_records_field_note():
    import random

    from evogame.ui.wildlife import Bunny

    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("forest")
    app.world_panel.wildlife = [Bunny(
        pos=(app.player.pos[0] + 18.0, app.player.pos[1] + 12.0),
        scene=app.world_panel.scene,
        rng=random.Random(1),
    )]
    prompt = app.world_panel.interaction_prompt_for_player(app.player)
    prompt_pos = app.world_panel.interaction_prompt_anchor_for_player(app.player, prompt)
    font = app.small_font
    text = font.render(prompt, True, (255, 255, 255))
    click_pos = (prompt_pos[0] + text.get_width() // 2, prompt_pos[1] + text.get_height() // 2)

    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": click_pos},
    ))
    app.step_one_frame(0)

    assert app.journal.field_notes == ["Forest Trail: bunny camouflage observed near dense cover."]
    assert app._status_message == "Observation saved to field journal."
    app.shutdown()



def test_app_status_strip_confirms_wildlife_observation_saved():
    import random

    from evogame.ui.wildlife import Bunny

    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("forest")
    app.world_panel.wildlife = [Bunny(
        pos=(app.player.pos[0] + 18.0, app.player.pos[1] + 12.0),
        scene=app.world_panel.scene,
        rng=random.Random(1),
    )]
    captured = {}

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)

    app.status_strip.draw = fake_draw

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert captured["interaction_prompt"] == "Observation saved to field journal."
    app.shutdown()


def test_app_status_strip_explains_duplicate_wildlife_observation():
    import random

    from evogame.ui.wildlife import Bunny

    app = App(seed=0)
    app.player.pos = app.world_panel.switch_area("forest")
    app.world_panel.wildlife = [Bunny(
        pos=(app.player.pos[0] + 18.0, app.player.pos[1] + 12.0),
        scene=app.world_panel.scene,
        rng=random.Random(1),
    )]
    app.journal.add_field_note("Forest Trail: bunny camouflage observed near dense cover.")
    captured = {}

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)

    app.status_strip.draw = fake_draw

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert app.journal.field_notes == ["Forest Trail: bunny camouflage observed near dense cover."]
    assert captured["interaction_prompt"] == "Observation already in field journal."
    app.shutdown()



def test_app_refreshes_visible_pond_fish_after_journal_reset():
    app = App(seed=0)
    app.world_panel.switch_area("pond")
    app.journal.open = True
    app.sim.tick()
    calls = []

    def fake_refresh(population):
        calls.append((app.sim.generation, len(population)))

    app.world_panel.pond_view.refresh = fake_refresh

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_r}))
    app.step_one_frame(0)

    assert app.sim.generation == 0
    assert calls == [(0, len(app.sim.population.creatures))]
    app.shutdown()


def test_app_refreshes_visible_pond_fish_after_manual_journal_step():
    app = App(seed=0)
    app.world_panel.switch_area("pond")
    app.journal.open = True
    app.journal.paused = True
    calls = []

    def fake_refresh(population):
        calls.append((app.sim.generation, len(population)))

    app.world_panel.pond_view.refresh = fake_refresh

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_n}))
    app.step_one_frame(0)

    assert app.sim.generation == 1
    assert calls == [(1, len(app.sim.population.creatures))]
    app.shutdown()


def test_app_manual_journal_step_clears_continuous_run_timer():
    app = App(seed=0)
    app.journal.open = True
    app.journal.paused = False
    app.step_one_frame(900)
    assert app.sim.generation == 0

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
    app.step_one_frame(0)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_n}))
    app.step_one_frame(0)
    assert app.sim.generation == 1

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
    app.step_one_frame(0)
    app.step_one_frame(100)

    assert app.sim.generation == 1
    app.shutdown()


def test_app_journal_reset_clears_continuous_run_timer():
    app = App(seed=0)
    app.journal.open = True
    app.journal.paused = False
    app.step_one_frame(900)
    assert app.sim.generation == 0

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_r}))
    app.step_one_frame(0)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
    app.step_one_frame(0)
    app.step_one_frame(100)

    assert app.sim.generation == 0
    app.shutdown()


def test_app_home_edge_paths_transition_to_field_areas():
    app = App(seed=0)
    app.player.pos = (app.world_panel.scene.tilemap.pixel_width - 20.0, 10 * 32.0)
    app.step_one_frame(0)
    assert app.world_panel.area_id == "pond"
    app.player.pos = app.world_panel.switch_area("home")
    app.player.pos = (15 * 32.0, app.world_panel.scene.tilemap.pixel_height - 20.0)
    app.step_one_frame(0)
    assert app.world_panel.area_id == "forest"
    app.shutdown()


def test_app_status_strip_shows_nearby_area_exit_hint():
    app = App(seed=0)
    captured = {}

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)

    app.status_strip.draw = fake_draw
    # Near enough to hint at the pond path, but not close enough to auto-transition.
    app.player.pos = (app.world_panel.scene.tilemap.pixel_width - 70.0, 10 * 32.0)
    app.step_one_frame(0)

    assert captured["interaction_prompt"] == "[E/Enter] Path to pond →"
    assert app.world_panel.area_id == "home"
    app.shutdown()


def test_app_e_key_uses_nearby_area_exit_hint():
    app = App(seed=0)
    # Near enough to use the path deliberately, but not close enough for auto-transition.
    app.player.pos = (app.world_panel.scene.tilemap.pixel_width - 70.0, 10 * 32.0)

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)

    assert app.world_panel.area_id == "pond"
    assert app.player.pos == app.world_panel.scene.entry_spawns["home"]
    app.shutdown()
