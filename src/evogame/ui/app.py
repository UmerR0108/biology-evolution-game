import random

import pygame

from evogame.genetics import BUNNY_SCHEMA, GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.sim.habitat import CaptiveHabitat
from evogame.ui.bird_capture import BirdCaptureMinigame
from evogame.ui.bunny_capture import BunnyCaptureMinigame
from evogame.ui.fishing import FishingMinigame, attract_visible_fish_to_bobber, draw_fishing_rod, fishing_rod_geometry
from evogame.ui.hud import StatusStrip
from evogame.ui.journal import Journal
from evogame.ui.player import Player
from evogame.ui.world_panel import WorldPanel

_WINDOW_W = 1000
_WINDOW_H = 620
_STATUS_H = 24
_INITIAL_POP = 30
_CARRYING_CAPACITY = 60

_TUTORIAL_LINES = (
    "Welcome, teacher and field researcher! Your goal is to investigate how populations change over generations.",
    "Move around the field site with the arrow keys or WASD; switch areas with Tab, 1/2/3, or H/P/F.",
    "Use E/Enter to interact: inspect home base, sample ponds, observe wildlife, or use area exits.",
    "Press J for the field journal and graphs to run/pause generations, inspect traits, and track allele frequencies.",
    "Catch creatures through fishing and capture minigames, then compare founders in home habitats.",
    "Habitats, crops, predators, and survival pressures change allele frequency evolution over time.",
    "Dismiss this help with Enter, E, Space, or Escape. Reopen it anytime with ?.",
)


class App:
    def __init__(self, seed: int | None = None, *, show_tutorial: bool = True):
        pygame.init()
        pygame.display.set_caption("evogame — guppy field site")
        self.screen = pygame.display.set_mode((_WINDOW_W, _WINDOW_H))
        self.font = pygame.font.SysFont("arial", 14)
        self.small_font = pygame.font.SysFont("arial", 12)
        self.clock = pygame.time.Clock()
        self.running = True

        rng = random.Random(seed)
        self.sim = SimController(
            schema=GUPPY_SCHEMA,
            initial_size=_INITIAL_POP,
            carrying_capacity=_CARRYING_CAPACITY,
            rng=rng,
        )

        status_rect = pygame.Rect(0, 0, _WINDOW_W, _STATUS_H)
        world_rect = pygame.Rect(0, _STATUS_H, _WINDOW_W, _WINDOW_H - _STATUS_H)
        screen_rect = pygame.Rect(0, 0, _WINDOW_W, _WINDOW_H)

        self.status_strip = StatusStrip(status_rect)
        self.world_panel = WorldPanel(world_rect)
        self.journal = Journal(screen_rect, self.sim)
        self._gameplay_rng = random.Random(seed)
        self.home_fish_habitat = CaptiveHabitat("guppy", _CARRYING_CAPACITY, random.Random(seed))
        self.home_bird_habitat = CaptiveHabitat("bird", 40, random.Random(seed))
        self.home_bunny_habitat = CaptiveHabitat("bunny", 40, random.Random(seed))
        self.fishing_minigame: FishingMinigame | None = None
        self.capture_minigame: BunnyCaptureMinigame | BirdCaptureMinigame | None = None
        self.bunny_capture_minigame: BunnyCaptureMinigame | BirdCaptureMinigame | None = None
        self._active_capture_species: str | None = None
        self._active_capture_target = None

        scene = self.world_panel.scene
        self.player = Player(pos=scene.spawn)
        self.world_panel.pond_view.refresh(self.sim.population.creatures)
        self._gen_timer_ms = 0.0
        self.research_unlocked = False
        self._status_message: str | None = None
        self._status_message_ms = 0.0
        self.tutorial_open = show_tutorial
        self.tutorial_lines = _TUTORIAL_LINES

    def shutdown(self) -> None:
        pygame.quit()

    def _sync_after_journal_population_change(self) -> None:
        if not self.journal.population_refresh_requested:
            return
        self.world_panel.pond_view.refresh(self.sim.population.creatures)
        self.journal.population_refresh_requested = False
        self._gen_timer_ms = 0.0

    def _announce_area_entry(self) -> None:
        title, _guidance = self.world_panel.area_title_and_guidance()
        self._status_message = f"Entered {title}."
        self._status_message_ms = 2500.0

    def _area_survey_note(self, area_id: str) -> str:
        if area_id == "pond":
            return "Pond Study Site survey: marked guppy sampling water and nearby predator habitat."
        if area_id == "forest":
            return "Forest Trail survey: noted dense cover and wildlife habitat for camouflage observations."
        return "Home Base survey: checked equipment and journal access before field work."

    def _record_area_survey_if_new(self, area_id: str, was_new: bool) -> None:
        if was_new and area_id != "home":
            self.journal.add_field_note(self._area_survey_note(area_id))

    def _pond_sample_note(self) -> str:
        phenotype_summary = self.journal.color_phenotype_summary_text()
        body_size_summary = self.journal.body_size_summary_text()
        predator_pressure = "on" if self.sim.pressure.predator_on else "off"
        details = f"population {len(self.sim.population)}; predator pressure {predator_pressure}"
        if phenotype_summary is not None:
            details += f"; {phenotype_summary}"
        if body_size_summary is not None:
            details += f"; {body_size_summary}"
        return (
            f"Pond Study Site: generation {self.sim.generation} "
            f"guppy population sampled for allele frequencies ({details})."
        )

    def _set_note_status_message(self, *, added: bool, saved: str, duplicate: str) -> None:
        if added and self.journal.field_note_coverage_complete():
            self._status_message = "Field notes complete: all field sites documented."
        else:
            self._status_message = saved if added else duplicate
        self._status_message_ms = 2500.0

    def _record_pond_sample(self) -> None:
        added = self.journal.add_field_note(self._pond_sample_note())
        self._set_note_status_message(
            added=added,
            saved="Pond sample saved to field journal.",
            duplicate="Pond sample already in field journal.",
        )

    def _open_research_from_habitat(self, habitat_id: str) -> None:
        self.research_unlocked = True
        self.journal.open = True
        if habitat_id == "fish":
            self.journal.current_page = "fish"
            self._status_message = "Home pond research opened: press Start to run generations."
        elif habitat_id == "bird":
            self.journal.set_active_habitat(self.home_bird_habitat, label="Bird cage", page="birds")
            self._status_message = "Bird cage research opened: press Start to run generations."
        else:
            self.journal.set_active_habitat(self.home_bunny_habitat, label="Bunny pen", page="bunnies")
            self._status_message = "Bunny pen research opened: press Start to run generations."
        self._status_message_ms = 2500.0

    def _record_wildlife_observation(self, wildlife_note: str) -> None:
        added = self.journal.add_field_note(wildlife_note)
        self._set_note_status_message(
            added=added,
            saved="Observation saved to field journal.",
            duplicate="Observation already in field journal.",
        )

    def _current_fishing_geometry(self) -> dict[str, tuple[int, int]]:
        pond_bounds = self.world_panel.scene.pond_pixel_bounds().move(
            self.world_panel.rect.left,
            self.world_panel.rect.top,
        )
        player_rect = pygame.Rect(
            int(self.world_panel.rect.left + self.player.pos[0]),
            int(self.world_panel.rect.top + self.player.pos[1]),
            int(self.player.size[0]),
            int(self.player.size[1]),
        )
        return fishing_rod_geometry(pond_bounds, player_rect=player_rect)

    def _start_fishing(self) -> None:
        if not self.world_panel.pond_view.fish:
            self.world_panel.pond_view.refresh(self.sim.population.creatures)
        bobber = self._current_fishing_geometry()["bobber_center"]
        self.fishing_minigame = FishingMinigame(
            list(self.sim.population.creatures),
            self._gameplay_rng,
            bobber_pos=(float(bobber[0]), float(bobber[1])),
        )
        self._status_message = "Fishing started: wait for a fish to touch the bobber."
        self._status_message_ms = 2500.0

    def _set_capture_minigame(self, minigame: BunnyCaptureMinigame | BirdCaptureMinigame | None, species: str | None, target=None) -> None:
        self.capture_minigame = minigame
        # Backwards-compatible name for older tests/callers.
        self.bunny_capture_minigame = minigame
        self._active_capture_species = species
        self._active_capture_target = target

    def _start_bunny_capture(self) -> bool:
        bunny = self.world_panel.nearest_observable_bunny_for_player(self.player)
        if bunny is None or bunny.creature is None:
            return False
        self._set_capture_minigame(BunnyCaptureMinigame(bunny.creature, self._gameplay_rng), "bunny", bunny)
        self._status_message = "Bunny capture started: press Enter in the gold skill-check zone."
        self._status_message_ms = 2500.0
        return True

    def _start_bird_capture(self) -> bool:
        bird = self.world_panel.nearest_observable_bird_for_player(self.player)
        if bird is None or bird.creature is None:
            return False
        self._set_capture_minigame(BirdCaptureMinigame(bird.creature, self._gameplay_rng), "bird", bird)
        self._status_message = "Bird capture started: press Enter in the gold skill-check zone."
        self._status_message_ms = 2500.0
        return True

    def _start_wildlife_capture(self) -> bool:
        wildlife = self.world_panel.nearest_observable_wildlife_for_player(self.player)
        if wildlife is None:
            return False
        if self.world_panel.nearest_observable_bird_for_player(self.player) is wildlife:
            return self._start_bird_capture()
        return self._start_bunny_capture()

    def _remove_active_capture_target(self) -> None:
        target = self._active_capture_target
        if target is None:
            return
        self.world_panel.wildlife = [wildlife for wildlife in self.world_panel.wildlife if wildlife is not target]

    def _record_home_base_note(self) -> None:
        added = self.journal.add_field_note(self._area_survey_note("home"))
        self._set_note_status_message(
            added=added,
            saved="Home base note saved to field journal.",
            duplicate="Home base note already in field journal.",
        )

    def _switch_area_if_changed(self, area_id: str) -> None:
        from_area = self.world_panel.area_id
        if area_id == from_area:
            title, _guidance = self.world_panel.area_title_and_guidance()
            self._status_message = f"Already at {title}."
            self._status_message_ms = 1500.0
            return
        was_new = area_id not in self.world_panel.visited_area_ids
        self.player.pos = self.world_panel.switch_area(area_id, from_area=from_area)
        if area_id == "pond":
            self.world_panel.pond_view.refresh(self.sim.population.creatures)
        self._announce_area_entry()
        self._record_area_survey_if_new(area_id, was_new)

    def _cycle_to_next_area(self) -> None:
        order = self.world_panel.AREA_ORDER
        current_index = order.index(self.world_panel.area_id)
        self._switch_area_if_changed(order[(current_index + 1) % len(order)])

    def _home_habitat_in_range(self) -> str | None:
        if self.world_panel.area_id != "home":
            return None
        player_center = (
            int(self.world_panel.rect.left + self.player.pos[0] + self.player.size[0] / 2),
            int(self.world_panel.rect.top + self.player.pos[1] + self.player.size[1] / 2),
        )
        for habitat_id, rect in self.world_panel.home_habitat_rects().items():
            if rect.inflate(36, 36).collidepoint(player_center):
                return habitat_id
        return None

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if self.fishing_minigame is not None:
                self.fishing_minigame.handle_event(event)
            if self.capture_minigame is not None:
                self.capture_minigame.handle_event(event)
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type == pygame.KEYDOWN:
                if getattr(event, "unicode", "") == "?" or event.key == getattr(pygame, "K_QUESTION", -1):
                    self.tutorial_open = True
                    continue
                if self.tutorial_open and event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    self.tutorial_open = False
                    continue
                if self.journal.open and event.key not in (pygame.K_j, pygame.K_ESCAPE):
                    self.journal.handle_event(event)
                    self._sync_after_journal_population_change()
                    continue
                if event.key in (pygame.K_1, pygame.K_h):
                    self._switch_area_if_changed("home")
                    continue
                if event.key in (pygame.K_2, pygame.K_p):
                    self._switch_area_if_changed("pond")
                    continue
                if event.key in (pygame.K_3, pygame.K_f):
                    self._switch_area_if_changed("forest")
                    continue
                if event.key == pygame.K_TAB:
                    self._cycle_to_next_area()
                    continue
                if event.key == pygame.K_j:
                    self.journal.toggle()
                    continue
                if event.key in (pygame.K_e, pygame.K_RETURN):
                    near_cottage = self.world_panel.cottage_in_range(self.player)
                    near_pond = self.world_panel.pond_in_range(self.player)
                    if near_cottage:
                        self.journal.open = True
                        self._record_home_base_note()
                        self.world_panel.pond_view.refresh(self.sim.population.creatures)
                        continue
                    if near_pond:
                        self.research_unlocked = True
                        self._record_pond_sample()
                        if self.fishing_minigame is None:
                            self._start_fishing()
                        continue
                    nearby_habitat = self._home_habitat_in_range()
                    if nearby_habitat is not None:
                        self._open_research_from_habitat(nearby_habitat)
                        continue
                    wildlife_note = self.world_panel.wildlife_field_note_for_player(self.player)
                    if wildlife_note is not None:
                        self._record_wildlife_observation(wildlife_note)
                        saved_message = self._status_message
                        saved_message_ms = self._status_message_ms
                        if self.capture_minigame is None:
                            self._start_wildlife_capture()
                        self._status_message = saved_message
                        self._status_message_ms = saved_message_ms
                        continue
                    next_area = self.world_panel.area_exit_target_for_player(self.player)
                    if next_area is not None:
                        from_area = self.world_panel.area_id
                        was_new = next_area not in self.world_panel.visited_area_ids
                        self.player.pos = self.world_panel.switch_area(next_area, from_area=from_area)
                        if next_area == "pond":
                            self.world_panel.pond_view.refresh(self.sim.population.creatures)
                        self._announce_area_entry()
                        self._record_area_survey_if_new(next_area, was_new)
                        continue
                if event.key == pygame.K_ESCAPE:
                    if self.journal.open:
                        self.journal.open = False
                    else:
                        self.running = False
                    continue
            if (
                not self.journal.open
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                clicked_area = self.world_panel.area_at_exit_marker_pos(event.pos)
                if clicked_area is not None:
                    self._switch_area_if_changed(clicked_area)
                    continue
                clicked_area = self.world_panel.area_at_minimap_pos(event.pos)
                if clicked_area is not None:
                    self._switch_area_if_changed(clicked_area)
                    continue
                prompt = self.world_panel.interaction_prompt_for_player(self.player)
                prompt_rect = self.world_panel.interaction_prompt_rect_for_player(
                    self.player,
                    prompt,
                    self.small_font,
                )
                if (
                    prompt is not None
                    and prompt.startswith("[E/Enter] Observe ")
                    and prompt_rect is not None
                    and prompt_rect.collidepoint(event.pos)
                ):
                    wildlife_note = self.world_panel.wildlife_field_note_for_player(self.player)
                    if wildlife_note is not None:
                        self._record_wildlife_observation(wildlife_note)
                        saved_message = self._status_message
                        saved_message_ms = self._status_message_ms
                        if self.capture_minigame is None:
                            self._start_wildlife_capture()
                        self._status_message = saved_message
                        self._status_message_ms = saved_message_ms
                        continue
                wildlife_note = self.world_panel.wildlife_field_note_at_screen_pos(event.pos)
                if wildlife_note is not None:
                    self._record_wildlife_observation(wildlife_note)
                    continue
                clicked_pond = self.world_panel.pond_at_screen_pos(event.pos)
                clicked_cottage = self.world_panel.cottage_at_screen_pos(event.pos)
                clicked_habitat = self.world_panel.home_habitat_at_screen_pos(event.pos)
                if clicked_habitat is not None:
                    self._open_research_from_habitat(clicked_habitat)
                    continue
                if clicked_pond or clicked_cottage:
                    self.journal.open = True
                    if clicked_cottage:
                        self._record_home_base_note()
                    if clicked_pond:
                        self.research_unlocked = True
                        self._record_pond_sample()
                    self.world_panel.pond_view.refresh(self.sim.population.creatures)
                    continue
            if self.journal.open:
                self.journal.handle_event(event)
                self._sync_after_journal_population_change()

    def step_one_frame(self, dt_ms: float) -> None:
        self._handle_events()
        if self.fishing_minigame is not None:
            if not self.fishing_minigame.bite_detected:
                attract_visible_fish_to_bobber(
                    self.world_panel.pond_view.fish,
                    self.fishing_minigame.bobber_pos,
                    dt_ms,
                )
                self.fishing_minigame.check_for_bite([fish.pos for fish in self.world_panel.pond_view.fish])
            result = self.fishing_minigame.update(dt_ms)
            if result is not None:
                if result.success and result.creature is not None:
                    self.home_fish_habitat.add_founder(result.creature)
                    self.world_panel.pond_view.remove_one_visible_fish()
                    self._status_message = "Congrats, you caught a fish!"
                    self._status_message_ms = 1500.0
                else:
                    self._status_message = "The guppy got away."
                    self._status_message_ms = 2500.0
                self.fishing_minigame = None
        if self.capture_minigame is not None:
            result = self.capture_minigame.update(dt_ms)
            if result is not None:
                if result.success and result.creature is not None:
                    self._remove_active_capture_target()
                    if self._active_capture_species == "bird":
                        self.home_bird_habitat.add_founder(result.creature)
                        self._status_message = "Bird captured!"
                    else:
                        self.home_bunny_habitat.add_founder(result.creature)
                        self._status_message = "Bunny captured!"
                    self._status_message_ms = 1500.0
                else:
                    self._status_message = "The bird flew back into the canopy." if self._active_capture_species == "bird" else "The bunny bolted into the brush."
                    self._status_message_ms = 2500.0
                self._set_capture_minigame(None, None)
        if not self.journal.open and self.fishing_minigame is None and self.capture_minigame is None:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)
            self.player.update(dt_ms, self.world_panel.scene)
            next_area = self.world_panel.area_exit_for_player(self.player)
            if next_area is not None:
                from_area = self.world_panel.area_id
                was_new = next_area not in self.world_panel.visited_area_ids
                self.player.pos = self.world_panel.switch_area(next_area, from_area=from_area)
                if next_area == "pond":
                    self.world_panel.pond_view.refresh(self.sim.population.creatures)
                self._announce_area_entry()
                self._record_area_survey_if_new(next_area, was_new)
        if self.research_unlocked and self.journal.open and not self.journal.paused and not self.sim.extinct:
            interval_ms = 1000.0 / self.journal.gens_per_second
            self._gen_timer_ms += dt_ms
            while self._gen_timer_ms >= interval_ms:
                self._gen_timer_ms -= interval_ms
                if self.journal.active_habitat is None:
                    self.sim.tick()
                self.home_fish_habitat.tick()
                self.home_bird_habitat.tick()
                self.home_bunny_habitat.tick()
                self.journal.on_sim_tick()
                self.world_panel.pond_view.refresh(self.sim.population.creatures)
                if self.sim.extinct:
                    break
        # Drift fish every frame (even when paused or journal open).
        self.world_panel.pond_view.update(dt_ms)
        self.world_panel.update_wildlife(dt_ms)
        self._render()
        if self._status_message_ms > 0.0:
            self._status_message_ms = max(0.0, self._status_message_ms - dt_ms)
            if self._status_message_ms == 0.0:
                self._status_message = None

    def _render(self) -> None:
        self.screen.fill((10, 10, 15))
        home_fish_creatures = self.home_fish_habitat.population.creatures if self.home_fish_habitat.population is not None else self.home_fish_habitat.founders
        home_bird_creatures = self.home_bird_habitat.population.creatures if self.home_bird_habitat.population is not None else self.home_bird_habitat.founders
        home_bunny_creatures = self.home_bunny_habitat.population.creatures if self.home_bunny_habitat.population is not None else self.home_bunny_habitat.founders
        self.world_panel.draw(
            self.screen,
            player=self.player,
            font=self.small_font,
            home_fish_founders=len(self.home_fish_habitat.founders),
            home_fish_generation=self.home_fish_habitat.generation,
            home_bird_founders=len(self.home_bird_habitat.founders),
            home_bird_generation=self.home_bird_habitat.generation,
            home_bunny_founders=len(self.home_bunny_habitat.founders),
            home_bunny_generation=self.home_bunny_habitat.generation,
            home_fish_founder_creatures=self.home_fish_habitat.founders,
            home_bird_founder_creatures=self.home_bird_habitat.founders,
            home_bunny_founder_creatures=self.home_bunny_habitat.founders,
            home_fish_creatures=home_fish_creatures,
            home_bird_creatures=home_bird_creatures,
            home_bunny_creatures=home_bunny_creatures,
        )
        if self.fishing_minigame is not None:
            pond_bounds = self.world_panel.scene.pond_pixel_bounds().move(
                self.world_panel.rect.left,
                self.world_panel.rect.top,
            )
            draw_fishing_rod(self.screen, self._current_fishing_geometry())
            self.fishing_minigame.draw(self.screen, self.font, pond_bounds=pond_bounds)
        if self.capture_minigame is not None:
            self.capture_minigame.draw(self.screen, self.font)
        field_note_sites, total_field_note_sites = self.journal.field_note_site_progress()
        self.status_strip.draw(
            self.screen, self.small_font,
            generation=self.sim.generation,
            population=len(self.sim.population),
            gens_per_second=self.journal.gens_per_second,
            extinct=self.sim.extinct,
            journal_open=self.journal.open,
            journal_paused=self.journal.paused,
            area_id=self.world_panel.area_id,
            predator_on=self.sim.pressure.predator_on,
            visited_areas=len(self.world_panel.visited_area_ids),
            total_areas=len(self.world_panel.AREA_ORDER),
            field_notes=len(self.journal.field_notes),
            field_note_sites=field_note_sites,
            total_field_note_sites=total_field_note_sites,
            interaction_prompt=(
                self._status_message
                or self.world_panel.interaction_prompt_for_player(self.player)
                or self.world_panel.area_exit_hint_for_player(self.player)
            ),
        )
        self.journal.draw(self.screen, self.font)
        if self.tutorial_open:
            self._draw_tutorial_overlay()
        pygame.display.flip()

    def _draw_tutorial_overlay(self) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(120, 86, _WINDOW_W - 240, _WINDOW_H - 172)
        pygame.draw.rect(self.screen, (242, 239, 222), panel, border_radius=12)
        pygame.draw.rect(self.screen, (78, 93, 74), panel, width=3, border_radius=12)

        title = self.font.render("Field Researcher Quick Start", True, (31, 44, 35))
        self.screen.blit(title, (panel.x + 28, panel.y + 24))
        y = panel.y + 62
        for line in self.tutorial_lines:
            text = self.small_font.render(f"• {line}", True, (35, 42, 38))
            self.screen.blit(text, (panel.x + 30, y))
            y += 36

    def run(self) -> None:
        while self.running:
            dt_ms = self.clock.tick(60)
            self.step_one_frame(dt_ms)
        self.shutdown()

    def run_for_generations(self, target: int, max_frames: int = 1000) -> None:
        """Test helper: step until sim reaches the target generation or max_frames hits."""
        frames = 0
        while self.sim.generation < target and frames < max_frames:
            self.step_one_frame(100)
            frames += 1
