import pygame

from evogame.ui.hud import StatusStrip


def test_status_strip_draws(pygame_surface):
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    font = pygame.font.SysFont("arial", 12)
    strip.draw(pygame_surface, font, generation=5, population=42, gens_per_second=1.5,
               extinct=False, journal_open=False)


def test_status_strip_shows_extinct_label(pygame_surface):
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    font = pygame.font.SysFont("arial", 12)
    strip.draw(pygame_surface, font, generation=5, population=0, gens_per_second=1.0,
               extinct=True, journal_open=False)


def test_status_strip_formats_current_area_and_shortcuts():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=3,
        population=27,
        gens_per_second=2.5,
        extinct=False,
        journal_open=False,
        area_id="pond",
    )
    assert "Area Pond Study Site" in text
    assert "[E/Enter] Interact" in text
    assert "[1] Home" in text
    assert "[2] Pond" in text
    assert "[3] Forest" in text
    assert "[Tab] Next Site" in text
    assert "[WASD/Arrows] Move" in text
    assert "[Shift] Sprint" in text
    assert "Click map/signs" in text


def test_status_strip_uses_field_site_display_names():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))

    home_text = strip.format_text(
        generation=0,
        population=30,
        gens_per_second=1.0,
        extinct=False,
        journal_open=False,
        area_id="home",
    )
    forest_text = strip.format_text(
        generation=0,
        population=30,
        gens_per_second=1.0,
        extinct=False,
        journal_open=False,
        area_id="forest",
    )

    assert "Area Home Base" in home_text
    assert "Area Forest Trail" in forest_text


def test_status_strip_formats_journal_controls_when_open():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=3,
        population=27,
        gens_per_second=2.5,
        extinct=False,
        journal_open=True,
        area_id="pond",
    )
    assert "Research Paused" in text
    assert "[Space] Start/Stop" in text
    assert "[+/-/Wheel] Speed" in text
    assert "[P] Predator" in text
    assert "[G] Chart Gene" in text
    assert "[1-4] Genes" in text
    assert "[ESC] Close" in text
    assert "[1] Home" not in text


def test_status_strip_shows_saved_note_message_when_journal_open():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=3,
        population=27,
        gens_per_second=2.5,
        extinct=False,
        journal_open=True,
        area_id="pond",
        interaction_prompt="Pond sample saved to field journal.",
    )
    assert "Pond sample saved to field journal." in text
    assert "Research Paused" in text


def test_status_strip_formats_running_research_state_when_unpaused():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=3,
        population=27,
        gens_per_second=2.5,
        extinct=False,
        journal_open=True,
        journal_paused=False,
        area_id="pond",
    )
    assert "Research Running" in text


def test_status_strip_shows_exploration_progress_when_available():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=3,
        population=27,
        gens_per_second=2.5,
        extinct=False,
        journal_open=False,
        area_id="forest",
        visited_areas=2,
        total_areas=3,
    )
    assert "Explored 2/3" in text


def test_status_strip_guides_exploration_until_all_sites_visited():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=0,
        population=30,
        gens_per_second=1.0,
        extinct=False,
        journal_open=False,
        area_id="home",
        visited_areas=1,
        total_areas=3,
    )
    assert "Objective: visit all field sites" in text


def test_status_strip_guides_note_collection_after_exploration_complete():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=0,
        population=30,
        gens_per_second=1.0,
        extinct=False,
        journal_open=False,
        area_id="forest",
        visited_areas=3,
        total_areas=3,
    )
    assert "Objective: collect field notes with E/J" in text


def test_status_strip_celebrates_complete_field_journal_objective():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=0,
        population=30,
        gens_per_second=1.0,
        extinct=False,
        journal_open=False,
        area_id="forest",
        visited_areas=3,
        total_areas=3,
        field_note_sites=3,
        total_field_note_sites=3,
    )
    assert "Objective complete: field journal ready" in text
    assert "Objective: collect field notes" not in text


def test_status_strip_shows_predator_state():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    off_text = strip.format_text(
        generation=3,
        population=27,
        gens_per_second=2.5,
        extinct=False,
        journal_open=False,
        area_id="pond",
        predator_on=False,
    )
    on_text = strip.format_text(
        generation=3,
        population=27,
        gens_per_second=2.5,
        extinct=False,
        journal_open=False,
        area_id="pond",
        predator_on=True,
    )
    assert "Predator Off" in off_text
    assert "Predator On" in on_text


def test_status_strip_prioritizes_interaction_prompt_when_available():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=0,
        population=10,
        gens_per_second=1.0,
        extinct=False,
        journal_open=False,
        area_id="home",
        interaction_prompt="[E] Field Journal",
    )
    assert "[E] Field Journal" in text
    assert text.index("[E] Field Journal") < text.index("Gen 0")
    assert "[1] Home" not in text


def test_status_strip_shows_field_note_count_when_available():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=0,
        population=10,
        gens_per_second=1.0,
        extinct=False,
        journal_open=False,
        area_id="forest",
        field_notes=4,
    )
    assert "Notes 4" in text


def test_status_strip_shows_documented_field_site_progress_when_available():
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    text = strip.format_text(
        generation=0,
        population=10,
        gens_per_second=1.0,
        extinct=False,
        journal_open=False,
        area_id="forest",
        field_notes=4,
        field_note_sites=2,
        total_field_note_sites=3,
    )
    assert "Notes 4" in text
    assert "Sites 2/3" in text


def test_status_strip_abbreviates_long_text_to_fit_rect(pygame_surface):
    strip = StatusStrip(pygame.Rect(0, 0, 180, 24))
    font = pygame.font.SysFont("arial", 12)
    text = strip.format_text(
        generation=12,
        population=58,
        gens_per_second=4.5,
        extinct=False,
        journal_open=False,
        area_id="pond",
        visited_areas=3,
        total_areas=3,
        field_notes=6,
    )

    visible = strip.fit_text_to_width(text, font)

    assert visible.endswith("…")
    assert len(visible) < len(text)
    assert font.size(visible)[0] <= strip.rect.width - 24
