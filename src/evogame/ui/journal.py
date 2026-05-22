import pygame

from evogame.sim.controller import SimController
from evogame.ui.chart_panel import ChartPanel
from evogame.ui.widgets import Button, Slider, Toggle

_BACKDROP = (0, 0, 0, 160)
_PANEL_BG = (28, 28, 38)
_FG = (220, 220, 220)
_GENE_BUTTON_BG = (49, 62, 74)
_GENE_BUTTON_ACTIVE = (255, 222, 89)
_GENE_BUTTON_BORDER = (185, 205, 190)
_PAPER = (238, 224, 183)
_INK = (54, 42, 31)
_PAGE_SHADOW = (141, 111, 73)
_JOURNAL_PAGES = ("fish", "bunnies", "observations")
_PAGE_LABELS = {"fish": "Fish Frequencies", "bunnies": "Bunnies", "observations": "Observations"}


def _wrap_text_to_width(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wrap text into lines that fit within ``max_width`` pixels."""
    if font.render(text, True, _FG).get_width() <= max_width:
        return [text]
    words = text.split()
    if not words:
        return [text]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.render(candidate, True, _FG).get_width() <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


class Journal:
    def __init__(self, screen_rect: pygame.Rect, sim: SimController):
        self.screen_rect = screen_rect
        self.sim = sim
        self.open = False
        self.paused = True
        self.population_refresh_requested = False
        self.observation_scroll = 0
        self.chart_genes = tuple(gene.name for gene in sim.schema.genes)
        self.field_notes: list[str] = []
        self.current_page = "fish"

        # Panel = 80% of screen, centered.
        margin_x = int(screen_rect.width * 0.10)
        margin_y = int(screen_rect.height * 0.10)
        self.panel_rect = pygame.Rect(
            screen_rect.left + margin_x,
            screen_rect.top + margin_y,
            screen_rect.width - 2 * margin_x,
            screen_rect.height - 2 * margin_y,
        )
        self.close_button_rect = pygame.Rect(
            self.panel_rect.right - 36,
            self.panel_rect.top + 10,
            24,
            24,
        )

        left_content, right_content = self.page_content_rects()
        self.chart_panel = ChartPanel(pygame.Rect(
            left_content.left, left_content.top + 74,
            left_content.width, left_content.height - 86,
        ))

        controls_x = right_content.left
        ctrl_y = right_content.top + 132
        self.predator_toggle = Toggle(
            pygame.Rect(controls_x, ctrl_y, 24, 24),
            "Predator",
            initial=sim.pressure.predator_on,
        )
        self.speed_slider = Slider(
            pygame.Rect(controls_x, ctrl_y + 50, 180, 20),
            min_value=0.5, max_value=5.0, initial=1.0,
        )
        self.pause_button = Button(
            pygame.Rect(controls_x, ctrl_y + 100, 100, 28),
            "Start",
            self._toggle_pause,
        )
        self._sync_pause_button_label()
        self.chart_panel.update(self.sim.log)

    @property
    def gens_per_second(self) -> float:
        return self.speed_slider.value

    def speed_label_text(self) -> str:
        return f"Speed: {self.gens_per_second:.1f} generations/sec"

    def controls_hint_text(self) -> str:
        return "Tab/←/→ pages • Space start/stop • N step • G/1-4 chart gene • +/- or wheel speed • PgUp/PgDn notes • Home/End jump • P predator • R reset • J/ESC close"

    def toggle(self) -> None:
        self.open = not self.open

    def _sync_pause_button_label(self) -> None:
        if self.sim.extinct:
            self.pause_button.label = "Restart"
        else:
            self.pause_button.label = "Start" if self.paused else "Stop"

    def _reset_research_run(self, *, paused: bool) -> None:
        self.sim.reset()
        self.predator_toggle.state = False
        self.speed_slider.value = 1.0
        self.paused = paused
        self._sync_pause_button_label()
        self.chart_panel.update(self.sim.log)
        self.population_refresh_requested = True

    def _toggle_pause(self) -> None:
        if self.sim.extinct:
            self._reset_research_run(paused=False)
            return
        self.paused = not self.paused
        self._sync_pause_button_label()

    def _step_one_generation(self) -> None:
        if not self.paused or self.sim.extinct:
            return
        self.sim.tick()
        self.on_sim_tick()
        self.population_refresh_requested = True

    def _select_chart_gene(self, index: int) -> None:
        if index < 0 or index >= len(self.chart_genes):
            return
        self.chart_panel.gene = self.chart_genes[index]
        self.chart_panel.update(self.sim.log)

    def book_rect(self) -> pygame.Rect:
        return self.panel_rect.inflate(-28, -46).move(0, 12)

    def left_page_rect(self) -> pygame.Rect:
        book = self.book_rect()
        return pygame.Rect(book.left, book.top, book.width // 2 - 6, book.height)

    def right_page_rect(self) -> pygame.Rect:
        book = self.book_rect()
        return pygame.Rect(book.centerx + 6, book.top, book.width // 2 - 6, book.height)

    def book_spine_rect(self) -> pygame.Rect:
        book = self.book_rect()
        return pygame.Rect(book.centerx - 6, book.top, 12, book.height)

    def page_content_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        return self.left_page_rect().inflate(-28, -36), self.right_page_rect().inflate(-28, -36)

    def page_labels(self) -> dict[str, str]:
        return dict(_PAGE_LABELS)

    def page_tab_rects(self) -> dict[str, pygame.Rect]:
        tab_w, tab_h, gap = 150, 24, 6
        x = self.panel_rect.left + 180
        y = self.panel_rect.top + 10
        return {page: pygame.Rect(x + i * (tab_w + gap), y, tab_w, tab_h) for i, page in enumerate(_JOURNAL_PAGES)}

    def _select_page(self, page: str) -> None:
        if page in _JOURNAL_PAGES:
            self.current_page = page

    def _select_page_at_pos(self, pos: tuple[int, int]) -> bool:
        for page, rect in self.page_tab_rects().items():
            if rect.collidepoint(pos):
                self._select_page(page)
                return True
        return False

    def _cycle_page(self, direction: int = 1) -> None:
        idx = _JOURNAL_PAGES.index(self.current_page) if self.current_page in _JOURNAL_PAGES else 0
        self.current_page = _JOURNAL_PAGES[(idx + direction) % len(_JOURNAL_PAGES)]

    def chart_gene_button_rects(self) -> dict[str, pygame.Rect]:
        """Return fish-page chart gene tabs, in the same order as keyboard shortcuts."""
        button_w = 82
        button_h = 22
        gap = 4
        left_content, _ = self.page_content_rects()
        x = left_content.left
        y = left_content.top + 38
        return {
            gene: pygame.Rect(x + index * (button_w + gap), y, button_w, button_h)
            for index, gene in enumerate(self.chart_genes)
        }

    def _select_chart_gene_at_pos(self, pos: tuple[int, int]) -> bool:
        for index, rect in enumerate(self.chart_gene_button_rects().values()):
            if rect.collidepoint(pos):
                self._select_chart_gene(index)
                return True
        return False

    def _cycle_chart_gene(self) -> None:
        if not self.chart_genes:
            return
        current = self.chart_panel.gene
        try:
            index = self.chart_genes.index(current)
        except ValueError:
            index = -1
        self._select_chart_gene((index + 1) % len(self.chart_genes))

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.open:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_button_rect.collidepoint(event.pos):
                self.open = False
                return
            if not self.panel_rect.collidepoint(event.pos):
                self.open = False
                return
            if self._select_page_at_pos(event.pos):
                return
            if self.current_page == "fish" and self._select_chart_gene_at_pos(event.pos):
                return
        if event.type == pygame.MOUSEWHEEL:
            self.speed_slider.adjust(0.5 * event.y)
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_j):
                self.open = False
                return
            if event.key == pygame.K_TAB:
                self._cycle_page(1)
                return
            if event.key == pygame.K_RIGHT:
                self._cycle_page(1)
                return
            if event.key == pygame.K_LEFT:
                self._cycle_page(-1)
                return
            if event.key == pygame.K_SPACE:
                self._toggle_pause()
                return
            if event.key == pygame.K_p:
                self.predator_toggle.state = not self.predator_toggle.state
                self.sim.set_predator(self.predator_toggle.state)
                return
            if event.key == pygame.K_g:
                self._cycle_chart_gene()
                return
            if event.key == pygame.K_PAGEDOWN:
                self._scroll_observation_lines(1)
                return
            if event.key == pygame.K_PAGEUP:
                self._scroll_observation_lines(-1)
                return
            if event.key == pygame.K_END:
                self.observation_scroll = self._max_observation_scroll()
                return
            if event.key == pygame.K_HOME:
                self.observation_scroll = 0
                return
            number_keys = {
                pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3,
                pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2, pygame.K_KP4: 3,
            }
            if event.key in number_keys:
                self._select_chart_gene(number_keys[event.key])
                return
            if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.speed_slider.adjust(0.5)
                return
            if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.speed_slider.adjust(-0.5)
                return
            if event.key == pygame.K_r:
                self._reset_research_run(paused=True)
                return
            if event.key == pygame.K_n:
                self._step_one_generation()
                return
        prior = self.predator_toggle.state
        self.predator_toggle.handle_event(event)
        if self.predator_toggle.state != prior:
            self.sim.set_predator(self.predator_toggle.state)
        self.speed_slider.handle_event(event)
        self.pause_button.handle_event(event)

    def on_sim_tick(self) -> None:
        self.chart_panel.update(self.sim.log)

    def add_field_note(self, note: str) -> bool:
        note = note.strip()
        if not note or note in self.field_notes:
            return False
        self.field_notes.append(note)
        return True
    def _shorten_note(self, note: str, max_chars: int = 72) -> str:
        if len(note) <= max_chars:
            return note
        return note[:max_chars - 1].rstrip() + "…"

    def field_notes_by_category(self) -> dict[str, list[str]]:
        groups = {"home": [], "pond": [], "forest": [], "bunnies": [], "other": []}
        for note in self.field_notes:
            lower = note.lower()
            if "bunny" in lower:
                groups["bunnies"].append(note)
            elif note.startswith("Home Base"):
                groups["home"].append(note)
            elif note.startswith("Pond Study Site"):
                groups["pond"].append(note)
            elif note.startswith("Forest Trail"):
                groups["forest"].append(note)
            else:
                groups["other"].append(note)
        return groups

    def bunny_field_notes(self) -> list[str]:
        return self.field_notes_by_category()["bunnies"]

    def fish_summary_cards(self) -> list[str]:
        if not self.sim.log.records:
            return ["No fish samples yet", "Press Space/N to record generations", "Predator: Off"]
        record = self.sim.log.records[-1]
        cards = [f"Generation {record.gen}", f"Population {record.population_size}", f"Predator: {'On' if record.predator_on else 'Off'}"]
        freqs = record.allele_freqs.get(self.chart_panel.gene, {})
        if freqs:
            allele, freq = max(freqs.items(), key=lambda item: (item[1], item[0]))
            cards.append(f"Top {self.chart_panel.gene}: {allele} {freq * 100:.0f}%")
        return [self._shorten_note(card, 44) for card in cards]

    def bunny_page_summary_text(self) -> str:
        count = len(self.bunny_field_notes())
        if count == 0:
            return "No bunny observations yet — explore the forest and press E near bunnies."
        return f"Bunny observations: {count}"

    def bunny_page_cards(self) -> list[str]:
        notes = list(reversed(self.bunny_field_notes()))[:5]
        if not notes:
            return ["Look for bunnies near cover and pond banks."]
        return [self._shorten_note(note, 68) for note in notes]

    def observation_checklist_items(self) -> list[tuple[str, bool, str]]:
        groups = self.field_notes_by_category()
        return [
            ("Home documented", bool(groups["home"]), f"{len(groups['home'])} notes"),
            ("Pond documented", bool(groups["pond"]), f"{len(groups['pond'])} notes"),
            ("Forest documented", bool(groups["forest"]), f"{len(groups['forest'])} notes"),
            ("Bunny observed", bool(groups["bunnies"]), f"{len(groups['bunnies'])} sightings"),
        ]

    def observation_page_sections(self) -> dict[str, list[str]]:
        groups = self.field_notes_by_category()
        return {label.title(): [self._shorten_note(note, 66) for note in reversed(notes[-3:])] for label, notes in groups.items() if notes}


    def _field_note_site_counts(self) -> dict[str, int]:
        counts = {"Home": 0, "Pond": 0, "Forest": 0}
        for note in self.field_notes:
            if note.startswith("Home Base"):
                counts["Home"] += 1
            elif note.startswith("Pond Study Site"):
                counts["Pond"] += 1
            elif note.startswith("Forest Trail"):
                counts["Forest"] += 1
        return counts

    def field_note_coverage_text(self) -> str:
        """Return a compact count of saved notes by field site."""
        counts = self._field_note_site_counts()
        return (
            "Field note coverage: "
            f"Home {counts['Home']} • Pond {counts['Pond']} • Forest {counts['Forest']}"
        )

    def field_note_site_progress(self) -> tuple[int, int]:
        """Return documented field-site count and total required sites."""
        counts = self._field_note_site_counts()
        sites = ("Home", "Pond", "Forest")
        return sum(1 for site in sites if counts[site] > 0), len(sites)

    def field_note_coverage_complete(self) -> bool:
        """Return True once every field site has at least one saved note."""
        documented, total = self.field_note_site_progress()
        return documented == total

    def field_note_goal_text(self) -> str:
        """Return checklist-style guidance for completing field-site notes."""
        counts = self._field_note_site_counts()
        missing = [site for site in ("Home", "Pond", "Forest") if counts[site] == 0]
        if not missing:
            return "Field note milestone: all field sites documented."
        if len(missing) == 1:
            missing_text = missing[0]
        elif len(missing) == 2:
            missing_text = " and ".join(missing)
        else:
            missing_text = f"{missing[0]}, {missing[1]}, and {missing[2]}"
        return f"Next field note goal: document {missing_text}."

    def _append_field_note_lines(self, lines: list[str]) -> None:
        if self.field_notes:
            count = len(self.field_notes)
            heading = f"Field notes (latest {count})" if count <= 3 else f"Field notes (latest 3 of {count})"
            lines.append(self.field_note_coverage_text())
            lines.append(self.field_note_goal_text())
            lines.append(heading)
            lines.extend(reversed(self.field_notes[-3:]))
        else:
            lines.append("Field notes: none yet — press E near ponds, wildlife, or home base.")
            lines.append(self.field_note_goal_text())

    def color_phenotype_summary_text(self) -> str | None:
        """Return current visible color phenotype counts for field observations."""
        counts = {"red": 0, "pink": 0, "white": 0}
        for creature in self.sim.population.creatures:
            category = creature.phenotype["color"].category
            counts[category] = counts.get(category, 0) + 1
        total = sum(counts.values())
        if total == 0:
            return None
        ordered = [f"{category} {counts[category]}" for category in ("red", "pink", "white")]
        return "Color phenotypes: " + ", ".join(ordered)

    def body_size_summary_text(self) -> str | None:
        """Return the current average body-size phenotype for field observations."""
        values = [float(creature.phenotype["body_size"].value) for creature in self.sim.population.creatures]
        if not values:
            return None
        return f"Average body size phenotype: {sum(values) / len(values):.1f}"

    def latest_observation_lines(self) -> list[str]:
        """Human-readable snapshot for the journal's field notes panel."""
        if not self.sim.log.records:
            lines = ["Latest observation", "No samples recorded yet."]
            self._append_field_note_lines(lines)
            return lines
        record = self.sim.log.records[-1]
        predator = "On" if record.predator_on else "Off"
        lines = [
            "Latest observation",
            f"Generation {record.gen}   Population {record.population_size}   Predator {predator}",
        ]
        if self.sim.extinct or record.population_size <= 0:
            lines.append("Population extinct — press Space to restart a new research run.")
        if len(self.sim.log.records) >= 2:
            previous = self.sim.log.records[-2]
            delta = record.population_size - previous.population_size
            sign = "+" if delta > 0 else ""
            lines.append(f"Population trend: {sign}{delta} since last generation")
        color_freqs = record.allele_freqs.get("color", {})
        if color_freqs:
            allele, freq = max(color_freqs.items(), key=lambda item: (item[1], item[0]))
            lines.append(f"Most common color allele: {allele} ({freq * 100:.0f}%)")
            heterozygosity = 1.0 - sum(freq ** 2 for freq in color_freqs.values())
            lines.append(f"Color diversity (expected heterozygosity): {heterozygosity * 100:.0f}%")
            phenotype_summary = self.color_phenotype_summary_text()
            if phenotype_summary is not None:
                lines.append(phenotype_summary)
            body_size_summary = self.body_size_summary_text()
            if body_size_summary is not None:
                lines.append(body_size_summary)
            if heterozygosity < 0.20:
                lines.append(
                    "Diversity warning: color variation is low; the population may be less resilient."
                )
            if len(self.sim.log.records) >= 2:
                previous_freq = self.sim.log.records[-2].allele_freqs.get("color", {}).get(allele, 0.0)
                delta_points = round((freq - previous_freq) * 100)
                sign = "+" if delta_points > 0 else ""
                lines.append(f"Color allele {allele} trend: {sign}{delta_points} percentage points")
                if record.predator_on and delta_points < 0:
                    lines.append(
                        f"Selection note: color allele {allele} is falling while predators are present."
                    )
        selected_gene = self.chart_panel.gene
        selected_freqs = record.allele_freqs.get(selected_gene, {})
        if selected_gene != "color" and selected_freqs:
            allele, freq = max(selected_freqs.items(), key=lambda item: (item[1], item[0]))
            lines.append(
                f"Selected gene {selected_gene}: allele {allele} is most common ({freq * 100:.0f}%)"
            )
            if len(self.sim.log.records) >= 2:
                previous_freq = self.sim.log.records[-2].allele_freqs.get(selected_gene, {}).get(allele, 0.0)
                delta_points = round((freq - previous_freq) * 100)
                sign = "+" if delta_points > 0 else ""
                lines.append(f"{selected_gene} allele {allele} trend: {sign}{delta_points} percentage points")
        if record.predator_on:
            lines.append(
                "Selection pressure: predators are active, so camouflaged white fish have higher survival."
            )
        else:
            lines.append(
                "Selection pressure: no predators, so bright red fish have higher mating success."
            )
        rare_alleles = [
            (freq, gene, allele)
            for gene, freqs in record.allele_freqs.items()
            for allele, freq in freqs.items()
            if freq > 0.0
        ]
        if rare_alleles:
            freq, gene, allele = min(rare_alleles)
            lines.append(f"Rare allele watch: {gene} {allele} ({freq * 100:.0f}%)")
        self._append_field_note_lines(lines)
        return lines

    def _max_visible_observation_lines(self) -> int:
        """Return how many note lines fit above the journal controls hint."""
        notes_y = self.pause_button.rect.bottom + 28
        return max(1, (self.panel_rect.bottom - 30 - notes_y) // 20)

    def _max_observation_scroll(self) -> int:
        lines = self.latest_observation_lines()
        return max(0, len(lines) - self._max_visible_observation_lines())

    def _clamp_observation_scroll(self) -> None:
        self.observation_scroll = max(0, min(self.observation_scroll, self._max_observation_scroll()))

    def _scroll_observation_lines(self, direction: int) -> None:
        page = max(1, self._max_visible_observation_lines() - 1)
        if direction > 0 and self.observation_scroll == 0:
            self.observation_scroll = self._max_observation_scroll()
        elif direction < 0:
            self.observation_scroll = 0
        else:
            self.observation_scroll += direction * page
        self._clamp_observation_scroll()

    def visible_observation_lines(self) -> list[str]:
        """Return observation lines clipped to the space above the controls hint."""
        lines = self.latest_observation_lines()
        max_lines = self._max_visible_observation_lines()
        self._clamp_observation_scroll()
        if len(lines) <= max_lines:
            return lines
        if self.observation_scroll == 0:
            if max_lines == 1:
                return ["… more journal lines"]
            omitted = len(lines) - (max_lines - 1)
            return [*lines[:max_lines - 1], f"… {omitted} more journal lines"]
        window = lines[self.observation_scroll:self.observation_scroll + max_lines]
        window[0] = f"↑ {self.observation_scroll} earlier journal lines"
        remaining = len(lines) - (self.observation_scroll + max_lines)
        if remaining > 0:
            window[-1] = f"↓ {remaining} more journal lines"
        return window

    def observation_text_max_width(self) -> int:
        """Return the right-column text width so notes do not spill into the chart/fish area."""
        return max(40, self.panel_rect.right - 18 - self.pause_button.rect.left)

    def visible_observation_lines_for_width(self, font: pygame.font.Font) -> list[str]:
        """Return visible notes wrapped to the right control column's pixel width."""
        wrapped: list[str] = []
        max_width = self.observation_text_max_width()
        for line in self.visible_observation_lines():
            wrapped.extend(_wrap_text_to_width(line, font, max_width))
        return wrapped[:self._max_visible_observation_lines()]

    def _draw_text_lines(self, surface: pygame.Surface, font: pygame.font.Font, lines: list[str], start: tuple[int, int], color: tuple[int, int, int] = _INK, step: int = 22) -> None:
        x, y = start
        for line in lines:
            surface.blit(font.render(line, True, color), (x, y))
            y += step

    def _draw_book(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, _PANEL_BG, self.panel_rect)
        pygame.draw.rect(surface, _FG, self.panel_rect, 2)
        for rect in (self.left_page_rect(), self.right_page_rect()):
            pygame.draw.rect(surface, _PAGE_SHADOW, rect.move(4, 4), border_radius=10)
            pygame.draw.rect(surface, _PAPER, rect, border_radius=10)
            pygame.draw.rect(surface, (152, 120, 76), rect, 2, border_radius=10)
        pygame.draw.rect(surface, (108, 79, 54), self.book_spine_rect(), border_radius=4)
        pygame.draw.rect(surface, (48, 48, 62), self.close_button_rect)
        pygame.draw.rect(surface, _FG, self.close_button_rect, 1)
        close_label = font.render("×", True, _FG)
        surface.blit(close_label, close_label.get_rect(center=self.close_button_rect.center))
        title = font.render("Field Journal", True, _FG)
        surface.blit(title, (self.panel_rect.left + 16, self.panel_rect.top + 12))

    def _draw_page_tabs(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        for page, rect in self.page_tab_rects().items():
            active = page == self.current_page
            fill = _GENE_BUTTON_ACTIVE if active else _GENE_BUTTON_BG
            text_color = (42, 67, 45) if active else _FG
            pygame.draw.rect(surface, fill, rect, border_radius=6)
            pygame.draw.rect(surface, _GENE_BUTTON_BORDER, rect, 1, border_radius=6)
            label = font.render(_PAGE_LABELS[page], True, text_color)
            surface.blit(label, label.get_rect(center=rect.center))

    def _draw_gene_tabs(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        for index, (gene, rect) in enumerate(self.chart_gene_button_rects().items(), start=1):
            active = gene == self.chart_panel.gene
            fill = _GENE_BUTTON_ACTIVE if active else (204, 187, 142)
            text_color = _INK
            pygame.draw.rect(surface, fill, rect, border_radius=5)
            pygame.draw.rect(surface, (117, 91, 55), rect, 1, border_radius=5)
            label = font.render(f"{index} {gene.replace('_', ' ')}", True, text_color)
            surface.blit(label, label.get_rect(center=rect.center))

    def _draw_fish_page(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        left, right = self.page_content_rects()
        self._draw_text_lines(surface, font, ["Fish Frequencies"], (left.left, left.top), _INK, 24)
        self._draw_gene_tabs(surface, font)
        self.chart_panel.draw(surface)
        self._draw_text_lines(surface, font, ["At a glance", *self.fish_summary_cards()], (right.left, right.top), _INK, 24)
        self.predator_toggle.draw(surface, font)
        speed_label = font.render(self.speed_label_text(), True, _INK)
        surface.blit(speed_label, (self.speed_slider.rect.left, self.speed_slider.rect.top - 20))
        self.speed_slider.draw(surface, font)
        self._sync_pause_button_label()
        self.pause_button.draw(surface, font)

    def _draw_bunnies_page(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        left, right = self.page_content_rects()
        self._draw_text_lines(surface, font, ["Bunnies", self.bunny_page_summary_text(), "", "Captured bunnies will later seed the home pen."], (left.left, left.top), _INK, 24)
        pygame.draw.ellipse(surface, (180, 135, 92), pygame.Rect(left.left + 40, left.top + 130, 82, 46))
        pygame.draw.ellipse(surface, (180, 135, 92), pygame.Rect(left.left + 52, left.top + 92, 18, 54))
        pygame.draw.ellipse(surface, (180, 135, 92), pygame.Rect(left.left + 86, left.top + 92, 18, 54))
        self._draw_text_lines(surface, font, ["Latest sightings", *self.bunny_page_cards()], (right.left, right.top), _INK, 24)

    def _draw_observations_page(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        left, right = self.page_content_rects()
        lines = ["Observations"]
        for label, done, status in self.observation_checklist_items():
            lines.append(f"{'✓' if done else '□'} {label} — {status}")
        self._draw_text_lines(surface, font, lines, (left.left, left.top), _INK, 24)
        section_lines = ["Field note cards"]
        for title, notes in self.observation_page_sections().items():
            section_lines.append(title)
            section_lines.extend(f"• {note}" for note in notes[:2])
        if len(section_lines) == 1:
            section_lines.append("No notes yet. Press E near field sites.")
        self._draw_text_lines(surface, font, section_lines[:15], (right.left, right.top), _INK, 22)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.open:
            return
        backdrop = pygame.Surface(self.screen_rect.size, pygame.SRCALPHA)
        backdrop.fill(_BACKDROP)
        surface.blit(backdrop, self.screen_rect.topleft)
        self._draw_book(surface, font)
        self._draw_page_tabs(surface, font)
        if self.current_page == "fish":
            self._draw_fish_page(surface, font)
        elif self.current_page == "bunnies":
            self._draw_bunnies_page(surface, font)
        else:
            self._draw_observations_page(surface, font)
        hint = font.render(self.controls_hint_text(), True, _FG)
        surface.blit(hint, (self.panel_rect.left + 16, self.panel_rect.bottom - 24))
