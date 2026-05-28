import random

import pygame

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.sim.recorder import GenerationRecord
from evogame.ui.journal import Journal


def test_journal_starts_closed(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    assert journal.open is False


def test_journal_open_close_toggle(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.toggle()
    assert journal.open is True
    journal.toggle()
    assert journal.open is False


def test_journal_click_outside_panel_closes(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": (journal.panel_rect.left - 2, journal.panel_rect.top - 2)},
    ))

    assert journal.open is False


def test_journal_click_inside_panel_stays_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": journal.panel_rect.center},
    ))

    assert journal.open is True


def test_journal_close_button_closes_panel(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": journal.close_button_rect.center},
    ))

    assert journal.open is False


def test_journal_escape_key_closes_panel(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))

    assert journal.open is False


def test_journal_j_key_closes_panel(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_j}))

    assert journal.open is False


def test_journal_predator_toggle_affects_sim(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    # Mouse-click on the predator toggle's rect.
    rect = journal.predator_toggle.rect
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": rect.center},
    )
    assert sim.pressure.predator_on is False
    journal.handle_event(event)
    assert sim.pressure.predator_on is True


def test_journal_space_key_toggles_research_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
    assert journal.paused is False
    assert journal.pause_button.label == "Stop"

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
    assert journal.paused is True
    assert journal.pause_button.label == "Start"


def test_journal_space_restart_after_extinction_refreshes_chart(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    sim.extinct = True
    sim.generation = 4
    calls = []

    def fake_update(log):
        calls.append((len(log.records), sim.generation, sim.extinct))

    journal.chart_panel.update = fake_update

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

    assert sim.generation == 0
    assert sim.extinct is False
    assert journal.paused is False
    assert calls == [(1, 0, False)]


def test_journal_space_key_ignored_when_closed(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

    assert journal.paused is True


def test_journal_p_key_toggles_predator_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_p}))
    assert sim.pressure.predator_on is True
    assert journal.predator_toggle.state is True

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_p}))
    assert sim.pressure.predator_on is False
    assert journal.predator_toggle.state is False


def test_journal_g_key_cycles_chart_gene_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_g}))

    assert journal.chart_panel.gene == "fin_length"
    assert journal.chart_panel.figure.axes[0].get_title() == "fin_length alleles"


def test_journal_number_keys_select_chart_gene_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_3}))

    assert journal.chart_panel.gene == "temp_tolerance"
    assert journal.chart_panel.figure.axes[0].get_title() == "temp_tolerance alleles"


def test_journal_keypad_number_keys_select_chart_gene_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_KP4}))

    assert journal.chart_panel.gene == "body_size"
    assert journal.chart_panel.figure.axes[0].get_title() == "body_size alleles"


def test_journal_exposes_chart_gene_button_rects(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    rects = journal.chart_gene_button_rects()

    assert tuple(rects) == journal.chart_genes
    assert all(rect.width > 0 and rect.height > 0 for rect in rects.values())
    assert rects["color"].top == rects["fin_length"].top
    assert rects["color"].right < rects["fin_length"].left


def test_journal_click_chart_gene_button_selects_gene_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": journal.chart_gene_button_rects()["temp_tolerance"].center},
    ))

    assert journal.chart_panel.gene == "temp_tolerance"
    assert journal.chart_panel.figure.axes[0].get_title() == "temp_tolerance alleles"


def test_journal_click_chart_gene_button_ignored_when_closed(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    journal.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": journal.chart_gene_button_rects()["temp_tolerance"].center},
    ))

    assert journal.chart_panel.gene == "color"


def test_journal_exposes_dedicated_bird_page_tab(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    assert journal.page_labels()["birds"] == "Birds"
    assert "birds" in journal.page_tab_rects()


def test_journal_clicking_bird_tab_selects_bird_page(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": journal.page_tab_rects()["birds"].center},
    ))

    assert journal.current_page == "birds"


def test_journal_plus_minus_keys_adjust_generation_speed_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_EQUALS}))
    assert journal.gens_per_second == 1.5

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_MINUS}))
    assert journal.gens_per_second == 1.0


def test_journal_speed_label_reflects_current_generation_rate(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    assert journal.speed_label_text() == "Speed: 1.0 generations/sec"

    journal.speed_slider.adjust(1.5)
    assert journal.speed_label_text() == "Speed: 2.5 generations/sec"


def test_journal_mouse_wheel_adjusts_generation_speed_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True

    journal.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": 1}))
    assert journal.gens_per_second == 1.5

    journal.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": -1}))
    assert journal.gens_per_second == 1.0


def test_journal_mouse_wheel_ignored_when_closed(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    journal.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": 1}))

    assert journal.gens_per_second == 1.0


def test_journal_controls_hint_mentions_mouse_wheel_speed(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    assert "wheel speed" in journal.controls_hint_text().lower()


def test_journal_visible_observation_lines_fit_controls_column(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.add_field_note(
        "Pond Study Site: generation 123 guppy population sampled for allele frequencies "
        "with a very long field note that used to render across the chart/fish area."
    )
    font = pygame.font.SysFont("arial", 14)

    for line in journal.visible_observation_lines_for_width(font):
        assert font.render(line, True, (255, 255, 255)).get_width() <= journal.observation_text_max_width()


def test_journal_r_key_resets_research_run_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.set_predator(True)
    sim.tick()
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    journal.paused = False
    journal.predator_toggle.state = True
    journal.speed_slider.value = 3.5

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_r}))

    assert sim.generation == 0
    assert sim.pressure.predator_on is False
    assert journal.predator_toggle.state is False
    assert journal.gens_per_second == 1.0
    assert journal.paused is True
    assert len(sim.log.records) == 1


def test_journal_n_key_steps_one_generation_when_paused(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    journal.paused = True
    calls = []

    def fake_update(log):
        calls.append((sim.generation, len(log.records)))

    journal.chart_panel.update = fake_update

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_n}))

    assert sim.generation == 1
    assert journal.paused is True
    assert journal.population_refresh_requested is True
    assert calls == [(1, 2)]


def test_journal_n_key_ignored_while_running(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    journal.paused = False

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_n}))

    assert sim.generation == 0


def test_journal_speed_keys_are_ignored_when_closed(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_EQUALS}))

    assert journal.gens_per_second == 1.0


def test_journal_latest_observation_summarizes_population_state(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.set_predator(True)
    sim.tick()
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    assert lines[0] == "Latest observation"
    assert f"Generation {sim.generation}" in lines[1]
    assert f"Population {len(sim.population)}" in lines[1]
    assert "Predator On" in lines[1]
    assert lines[2].startswith("Population trend: ")
    assert lines[3].startswith("Most common color allele: ")
    assert "%" in lines[3]


def test_journal_latest_observation_explains_current_selection_pressure(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.60, "B": 0.40}}, predator_on=True, population_size=10),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    predator_lines = journal.latest_observation_lines()

    assert "Selection pressure: predators are active, so camouflaged white fish have higher survival." in predator_lines

    sim.log.records = [
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.60, "B": 0.40}}, predator_on=False, population_size=10),
    ]

    calm_lines = journal.latest_observation_lines()

    assert "Selection pressure: no predators, so bright red fish have higher mating success." in calm_lines


def test_journal_latest_observation_reports_population_trend(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=3, allele_freqs={"color": {"R": 0.40, "B": 0.60}}, predator_on=False, population_size=10),
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.70, "B": 0.30}}, predator_on=True, population_size=7),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    assert "Population trend: -3 since last generation" in lines


def test_journal_latest_observation_reports_color_diversity(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.50, "B": 0.50}}, predator_on=False, population_size=10),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    assert "Color diversity (expected heterozygosity): 50%" in lines


def test_journal_latest_observation_reports_color_phenotype_counts(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    phenotype_line = next(line for line in lines if line.startswith("Color phenotypes:"))
    counts = [int(part.rsplit(" ", 1)[1]) for part in phenotype_line.removeprefix("Color phenotypes: ").split(", ")]
    assert sum(counts) == len(sim.population)


def test_journal_latest_observation_reports_average_body_size(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    body_size_line = next(line for line in lines if line.startswith("Average body size phenotype:"))
    value = float(body_size_line.removeprefix("Average body size phenotype: "))
    assert 0.0 <= value <= 6.0


def test_journal_latest_observation_warns_when_color_diversity_is_low(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.95, "B": 0.05}}, predator_on=False, population_size=10),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    assert "Diversity warning: color variation is low; the population may be less resilient." in lines


def test_journal_latest_observation_flags_rarest_tracked_allele(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(
            gen=4,
            allele_freqs={
                "color": {"R": 0.85, "B": 0.15},
                "tail": {"S": 0.70, "L": 0.30},
            },
            predator_on=False,
            population_size=10,
        ),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    assert "Rare allele watch: color B (15%)" in lines


def test_journal_latest_observation_explains_extinction_restart(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 1.0}}, predator_on=True, population_size=0),
    ]
    sim.extinct = True
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    assert "Population extinct — press Space to restart a new research run." in lines


def test_journal_latest_observation_reports_dominant_color_trend(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=3, allele_freqs={"color": {"R": 0.40, "B": 0.60}}, predator_on=False, population_size=10),
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.70, "B": 0.30}}, predator_on=True, population_size=7),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    assert "Color allele R trend: +30 percentage points" in lines


def test_journal_latest_observation_tracks_selected_chart_gene(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(
            gen=3,
            allele_freqs={
                "color": {"R": 0.50, "B": 0.50},
                "fin_length": {"L": 0.25, "S": 0.75},
            },
            predator_on=False,
            population_size=10,
        ),
        GenerationRecord(
            gen=4,
            allele_freqs={
                "color": {"R": 0.50, "B": 0.50},
                "fin_length": {"L": 0.45, "S": 0.55},
            },
            predator_on=False,
            population_size=10,
        ),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.chart_panel.gene = "fin_length"

    lines = journal.latest_observation_lines()

    assert "Selected gene fin_length: allele S is most common (55%)" in lines
    assert "fin_length allele S trend: -20 percentage points" in lines


def test_journal_latest_observation_adds_selection_note_under_predation(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=3, allele_freqs={"color": {"R": 0.70, "B": 0.30}}, predator_on=False, population_size=10),
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.50, "B": 0.50}}, predator_on=True, population_size=7),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    assert "Selection note: color allele R is falling while predators are present." in lines


def test_journal_latest_observation_prompts_for_field_notes_when_empty(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    lines = journal.latest_observation_lines()

    assert "Field notes: none yet — press E near ponds, birds, bunnies, or home base." in lines


def test_journal_tracks_bird_notes_separately_from_bunnies(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    bird_note = "Forest Trail: bird beak traits observed near dense cover."
    bunny_note = "Forest Trail: bunny camouflage observed near dense cover."

    journal.add_field_note(bird_note)
    journal.add_field_note(bunny_note)

    assert journal.bird_field_notes() == [bird_note]
    assert journal.bunny_field_notes() == [bunny_note]
    assert journal.bird_page_summary_text() == "Bird observations: 1"
    assert journal.bird_page_cards() == [bird_note]


def test_journal_observation_checklist_includes_birds(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.add_field_note("Forest Trail: bird beak traits observed near dense cover.")

    checklist = journal.observation_checklist_items()

    assert ("Bird observed", True, "1 sightings") in checklist



def test_journal_records_field_notes_in_latest_observation(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    added = journal.add_field_note("Forest Trail: bunny camouflage observed near dense cover.")
    duplicate_added = journal.add_field_note("Forest Trail: bunny camouflage observed near dense cover.")

    lines = journal.latest_observation_lines()

    assert added is True
    assert duplicate_added is False
    assert journal.field_notes == ["Forest Trail: bunny camouflage observed near dense cover."]
    assert "Field notes (latest 1)" in lines
    assert "Forest Trail: bunny camouflage observed near dense cover." in lines


def test_journal_sanitizes_field_notes_before_saving(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    added = journal.add_field_note("  Pond Study Site: sampled guppies.  ")
    duplicate_added = journal.add_field_note("Pond Study Site: sampled guppies.")
    blank_added = journal.add_field_note("   ")

    assert added is True
    assert duplicate_added is False
    assert blank_added is False
    assert journal.field_notes == ["Pond Study Site: sampled guppies."]



def test_journal_shows_field_notes_even_before_first_sample(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = []
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.add_field_note("Forest Trail: bunny camouflage observed near dense cover.")

    lines = journal.latest_observation_lines()

    assert lines[:2] == ["Latest observation", "No samples recorded yet."]
    assert "Field notes (latest 1)" in lines
    assert "Forest Trail: bunny camouflage observed near dense cover." in lines



def test_journal_shows_recent_field_notes_newest_first(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    for note in ("note 1", "note 2", "note 3", "note 4"):
        assert journal.add_field_note(note) is True

    lines = journal.latest_observation_lines()
    field_note_index = lines.index("Field notes (latest 3 of 4)")

    assert lines[field_note_index + 1:field_note_index + 4] == ["note 4", "note 3", "note 2"]
    assert "note 1" not in lines[field_note_index:]



def test_journal_summarizes_field_note_coverage_by_site(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.add_field_note("Home Base survey: checked equipment and journal access before field work.")
    journal.add_field_note("Pond Study Site: generation 0 guppy population sampled for allele frequencies.")
    journal.add_field_note("Forest Trail: bunny camouflage observed near dense cover.")
    journal.add_field_note("Pond Study Site: bunny browsing near the bank; compare camouflage with guppy predator pressure.")

    assert journal.field_note_coverage_text() == "Field note coverage: Home 1 • Pond 2 • Forest 1"
    assert journal.field_note_site_progress() == (3, 3)
    assert "Field note coverage: Home 1 • Pond 2 • Forest 1" in journal.latest_observation_lines()



def test_journal_field_note_goal_text_guides_site_completion(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    assert journal.field_note_goal_text() == "Next field note goal: document Home, Pond, and Forest."
    assert journal.field_note_coverage_complete() is False

    journal.add_field_note("Home Base survey: checked equipment.")
    journal.add_field_note("Pond Study Site: sampled guppies.")
    assert journal.field_note_goal_text() == "Next field note goal: document Forest."
    assert journal.field_note_coverage_complete() is False

    journal.add_field_note("Forest Trail: bunny camouflage observed.")
    assert journal.field_note_goal_text() == "Field note milestone: all field sites documented."
    assert journal.field_note_coverage_complete() is True
    assert "Field note milestone: all field sites documented." in journal.latest_observation_lines()



def test_journal_visible_observation_lines_fit_notes_panel(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=3, allele_freqs={"color": {"R": 0.70, "B": 0.30}}, predator_on=False, population_size=10),
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.50, "B": 0.50}}, predator_on=True, population_size=7),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    for index in range(6):
        journal.add_field_note(f"Pond Study Site: sample note {index}")

    lines = journal.visible_observation_lines()
    notes_y = journal.pause_button.rect.bottom + 28
    max_lines = (journal.panel_rect.bottom - 30 - notes_y) // 20

    assert len(lines) <= max_lines
    assert lines[0] == "Latest observation"
    assert lines[-1].startswith("… ")
    assert lines[-1].endswith("more journal lines")


def test_journal_page_keys_scroll_long_observation_notes_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=3, allele_freqs={"color": {"R": 0.70, "B": 0.30}}, predator_on=False, population_size=10),
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.50, "B": 0.50}}, predator_on=True, population_size=7),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    for index in range(8):
        journal.add_field_note(f"Pond Study Site: sample note {index}")

    before = journal.visible_observation_lines()
    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_PAGEDOWN}))
    after_page_down = journal.visible_observation_lines()

    assert journal.observation_scroll > 0
    assert after_page_down != before
    assert after_page_down[0].startswith("↑ ")
    assert any("sample note" in line for line in after_page_down)

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_PAGEUP}))

    assert journal.observation_scroll == 0
    assert journal.visible_observation_lines() == before


def test_journal_home_end_keys_jump_observation_notes_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    sim.log.records = [
        GenerationRecord(gen=3, allele_freqs={"color": {"R": 0.70, "B": 0.30}}, predator_on=False, population_size=10),
        GenerationRecord(gen=4, allele_freqs={"color": {"R": 0.50, "B": 0.50}}, predator_on=True, population_size=7),
    ]
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    for index in range(8):
        journal.add_field_note(f"Pond Study Site: sample note {index}")

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_END}))

    assert journal.observation_scroll == journal._max_observation_scroll()
    assert journal.visible_observation_lines()[0].startswith("↑ ")

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_HOME}))

    assert journal.observation_scroll == 0
    assert journal.visible_observation_lines()[0] == "Latest observation"


def test_journal_page_keys_ignored_when_closed(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    for index in range(8):
        journal.add_field_note(f"Pond Study Site: sample note {index}")

    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_PAGEDOWN}))
    journal.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_END}))

    assert journal.observation_scroll == 0


def test_journal_controls_hint_mentions_note_scrolling(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)

    assert "PgUp/PgDn notes" in journal.controls_hint_text()
    assert "Home/End jump" in journal.controls_hint_text()


def test_journal_controls_hint_wraps_inside_panel_width(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    font = pygame.font.SysFont("arial", 12)
    max_width = journal.panel_rect.width - 32

    lines = journal.controls_hint_lines_for_width(font)

    assert len(lines) >= 2
    assert all(font.render(line, True, (255, 255, 255)).get_width() <= max_width for line in lines)


def test_journal_draw_when_closed_no_op(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    font = pygame.font.SysFont("arial", 12)
    journal.draw(pygame_surface, font)  # no error


def test_journal_draw_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    font = pygame.font.SysFont("arial", 12)
    journal.draw(pygame_surface, font)


def test_journal_predator_label_explains_selection_pressure():
    from evogame.genetics import GUPPY_SCHEMA
    from evogame.sim.controller import SimController

    journal = Journal(pygame.Rect(0, 0, 1000, 620), SimController(GUPPY_SCHEMA, 10, 20, __import__("random").Random(1)))

    assert journal.predator_selection_hint_text() == "Preys on fish with small fins"
