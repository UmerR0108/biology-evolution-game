import pygame

_BG = (25, 25, 35)
_FG = (220, 220, 220)
_AREA_DISPLAY_NAMES = {
    "home": "Home Base",
    "pond": "Pond Study Site",
    "forest": "Forest Trail",
}


class StatusStrip:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect

    def fit_text_to_width(self, text: str, font: pygame.font.Font) -> str:
        """Return text shortened with an ellipsis so it fits inside the strip."""
        max_width = max(0, self.rect.width - 24)
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "…"
        if font.size(ellipsis)[0] > max_width:
            return ""
        low = 0
        high = len(text)
        while low < high:
            mid = (low + high + 1) // 2
            candidate = text[:mid].rstrip() + ellipsis
            if font.size(candidate)[0] <= max_width:
                low = mid
            else:
                high = mid - 1
        return text[:low].rstrip() + ellipsis

    def format_text(self, *, generation: int, population: int, gens_per_second: float,
                    extinct: bool, journal_open: bool, journal_paused: bool = True,
                    area_id: str = "home", predator_on: bool = False,
                    visited_areas: int | None = None, total_areas: int | None = None,
                    interaction_prompt: str | None = None,
                    field_notes: int | None = None,
                    field_note_sites: int | None = None,
                    total_field_note_sites: int | None = None) -> str:
        area_name = _AREA_DISPLAY_NAMES.get(area_id, area_id.replace("_", " ").title())
        predator_state = "On" if predator_on else "Off"
        exploration = ""
        objective = ""
        notes = "" if field_notes is None else f"   Notes {field_notes}"
        if field_note_sites is not None and total_field_note_sites is not None:
            notes += f"   Sites {field_note_sites}/{total_field_note_sites}"
        if visited_areas is not None and total_areas is not None:
            exploration = f"   Explored {visited_areas}/{total_areas}"
            if visited_areas < total_areas:
                objective = "   Objective: visit all field sites"
            elif (
                field_note_sites is not None
                and total_field_note_sites is not None
                and field_note_sites >= total_field_note_sites
            ):
                objective = "   Objective complete: field journal ready"
            else:
                objective = "   Objective: collect field notes with E/J"
        prompt_is_world_control = interaction_prompt is not None and interaction_prompt.startswith("[")
        prompt_text = (
            f"   {interaction_prompt}"
            if interaction_prompt is not None and (not journal_open or not prompt_is_world_control)
            else ""
        )
        text = (
            f"Area {area_name}{exploration}{notes}{prompt_text}   Gen {generation}   Pop {population}   "
            f"Predator {predator_state}   Speed {gens_per_second:.1f}/s"
        )
        if extinct:
            text += "   EXTINCT"
        if journal_open:
            research_state = "Paused" if journal_paused else "Running"
            text += f"   Research {research_state}   [Space] Start/Stop   [N] Step   [+/-/Wheel] Speed   [P] Predator   [G] Chart Gene   [1-4] Genes   [R] Reset   [ESC] Close"
        elif interaction_prompt is not None:
            pass
        else:
            text += objective
            text += "   [WASD/Arrows] Move   [E/Enter] Interact   [J] Journal   [Shift] Sprint   [1] Home [2] Pond [3] Forest   [Tab] Next Site   Click map/signs"
        return text

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, *,
             generation: int, population: int, gens_per_second: float,
             extinct: bool, journal_open: bool, journal_paused: bool = True,
             area_id: str = "home", predator_on: bool = False,
             visited_areas: int | None = None, total_areas: int | None = None,
             interaction_prompt: str | None = None,
             field_notes: int | None = None,
             field_note_sites: int | None = None,
             total_field_note_sites: int | None = None) -> None:
        pygame.draw.rect(surface, _BG, self.rect)
        text = self.format_text(
            generation=generation,
            population=population,
            gens_per_second=gens_per_second,
            extinct=extinct,
            journal_open=journal_open,
            journal_paused=journal_paused,
            area_id=area_id,
            predator_on=predator_on,
            visited_areas=visited_areas,
            total_areas=total_areas,
            interaction_prompt=interaction_prompt,
            field_notes=field_notes,
            field_note_sites=field_note_sites,
            total_field_note_sites=total_field_note_sites,
        )
        visible_text = self.fit_text_to_width(text, font)
        surface.blit(font.render(visible_text, True, _FG), (self.rect.left + 12, self.rect.top + 5))
