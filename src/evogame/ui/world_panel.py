import random as _rand_module
from typing import TYPE_CHECKING

import pygame

from evogame.ui.assets import load_cottage_sprite, load_decoration_sprite, load_tree_sprite
from evogame.ui.pond import PondView
from evogame.ui.tilemap import (
    TILE_PIXELS,
    Scene,
    build_deep_forest_scene,
    build_forest_scene,
    build_home_scene,
)
from evogame.ui.wildlife import Bunny

if TYPE_CHECKING:
    from evogame.ui.player import Player


class WorldPanel:
    COTTAGE_INTERACT_RADIUS = 64
    COTTAGE_CLICK_MARGIN = 8
    COTTAGE_TILE_SIZE = (7, 6)
    POND_INTERACT_RADIUS = 56
    POND_CLICK_MARGIN = 8
    WILDLIFE_OBSERVATION_RADIUS = 72
    AREA_ORDER = ("home", "pond", "forest")
    MINIMAP_CURRENT = (255, 222, 89)
    MINIMAP_VISITED = (205, 230, 196)
    MINIMAP_UNVISITED = (92, 116, 88)
    MINIMAP_BG = (18, 32, 24, 172)
    AREA_CARD_BG = (18, 32, 24, 172)
    AREA_CARD_BORDER = (236, 246, 221)
    EXIT_MARKER_FILL = (255, 222, 89)
    EXIT_MARKER_BORDER = (42, 67, 45)
    EXIT_MARKER_CLICK_MARGIN = 6
    AREA_GUIDANCE: dict[str, tuple[str, str]] = {
        "home": (
            "Home Base",
            "Check the cottage journal, then follow paths to study sites.",
        ),
        "pond": (
            "Pond Study Site",
            "Watch guppies here; press E near water to open research data.",
        ),
        "forest": (
            "Forest Trail",
            "Explore wildlife and use the northern trail to return home.",
        ),
    }

    def __init__(self, rect: pygame.Rect,
                 pond_rng: _rand_module.Random | None = None,
                 wildlife_rng: _rand_module.Random | None = None):
        self.rect = rect
        self.scenes: dict[str, Scene] = {
            "home": build_home_scene(),
            "pond": build_forest_scene(),
            "forest": build_deep_forest_scene(),
        }
        self.area_id = "home"
        self.scene = self.scenes[self.area_id]
        self.visited_area_ids: set[str] = {self.area_id}
        self._object_surfs: dict[str, pygame.Surface] | None = None
        self._wildlife_rng = wildlife_rng or _rand_module.Random(7)
        self.pond_view = PondView(
            bounds=self._pond_bounds_in_panel(),
            max_visible=10,
            rng=pond_rng or _rand_module.Random(0),
        )

        self.wildlife: list[Bunny] = self._spawn_wildlife(self.scene)

    def _spawn_wildlife(self, scene: Scene) -> list[Bunny]:
        wildlife: list[Bunny] = []
        if scene.area_id == "home":
            return wildlife
        count = 4 if scene.area_id == "forest" else 3
        for _ in range(count):
            for _attempt in range(20):
                x = self._wildlife_rng.uniform(0, scene.tilemap.pixel_width)
                y = self._wildlife_rng.uniform(0, scene.tilemap.pixel_height)
                if scene.is_walkable_at_pixel(x, y):
                    wildlife.append(Bunny(pos=(x, y), scene=scene, rng=self._wildlife_rng))
                    break
        return wildlife

    def switch_area(self, area_id: str, from_area: str | None = None) -> tuple[float, float]:
        if area_id not in self.scenes:
            raise ValueError(f"Unknown area {area_id!r}; expected one of {sorted(self.scenes)}")
        if area_id == self.area_id:
            return self.scene.entry_spawns.get(from_area, self.scene.spawn)
        self.area_id = area_id
        self.visited_area_ids.add(area_id)
        self.scene = self.scenes[area_id]
        self.pond_view.bounds = self._pond_bounds_in_panel()
        self.pond_view.fish = []
        self.wildlife = self._spawn_wildlife(self.scene)
        return self.scene.entry_spawns.get(from_area, self.scene.spawn)

    def _pond_bounds_in_panel(self) -> pygame.Rect:
        b = self.scene.pond_swim_bounds()
        return pygame.Rect(self.rect.left + b.left, self.rect.top + b.top, b.width, b.height)

    def update_wildlife(self, dt_ms: float) -> None:
        for b in self.wildlife:
            b.update(dt_ms)

    def _ensure_objects(self) -> dict[str, pygame.Surface]:
        if self._object_surfs is None:
            objects: dict[str, pygame.Surface] = {}
            for tree_id in ("1", "2", "3", "4", "5", "6", "7", "10", "11", "12", "13", "14"):
                objects[f"tree_{tree_id}"] = load_tree_sprite(tree_id, "green")
            for kind in (
                "bush", "yellow_bush", "rock", "small_rock", "flower_red",
                "flower_yellow", "stump", "log", "mushroom",
            ):
                objects[kind] = load_decoration_sprite(kind)
            cottage = load_cottage_sprite()
            objects["cottage"] = pygame.transform.scale(
                cottage,
                (TILE_PIXELS * self.COTTAGE_TILE_SIZE[0],
                 TILE_PIXELS * self.COTTAGE_TILE_SIZE[1]),
            )
            self._object_surfs = objects
        return self._object_surfs

    def cottage_in_range(self, player: "Player") -> bool:
        cottage = next((o for o in self.scene.objects if o.kind == "cottage"), None)
        if cottage is None:
            return False
        cx = cottage.col * TILE_PIXELS + TILE_PIXELS * self.COTTAGE_TILE_SIZE[0] / 2
        cy = cottage.row * TILE_PIXELS + TILE_PIXELS * self.COTTAGE_TILE_SIZE[1] / 2
        px = player.pos[0] + player.size[0] / 2
        py = player.pos[1] + player.size[1] / 2
        return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 <= self.COTTAGE_INTERACT_RADIUS

    def area_exit_for_player(self, player: "Player") -> str | None:
        x = player.pos[0] + player.size[0] / 2
        y = player.pos[1] + player.size[1] / 2
        edge = TILE_PIXELS // 2
        if self.area_id == "home":
            if x >= self.scene.tilemap.pixel_width - edge:
                return "pond"
            if y >= self.scene.tilemap.pixel_height - edge:
                return "forest"
        if self.area_id == "pond" and x <= edge:
            return "home"
        if self.area_id == "forest" and y <= edge:
            return "home"
        return None

    def area_exit_target_for_player(self, player: "Player") -> str | None:
        x = player.pos[0] + player.size[0] / 2
        y = player.pos[1] + player.size[1] / 2
        edge = TILE_PIXELS * 2
        if self.area_id == "home":
            if x >= self.scene.tilemap.pixel_width - edge:
                return "pond"
            if y >= self.scene.tilemap.pixel_height - edge:
                return "forest"
        if self.area_id == "pond" and x <= edge:
            return "home"
        if self.area_id == "forest" and y <= edge:
            return "home"
        return None

    def area_exit_hint_for_player(self, player: "Player") -> str | None:
        target = self.area_exit_target_for_player(player)
        if target == "pond":
            return "[E/Enter] Path to pond →"
        if target == "forest":
            return "[E/Enter] Trail to forest ↓"
        if target == "home" and self.area_id == "pond":
            return "[E/Enter] Path home ←"
        if target == "home" and self.area_id == "forest":
            return "[E/Enter] Trail home ↑"
        return None

    def pond_in_range(self, player: "Player") -> bool:
        if self.area_id != "pond":
            return False
        bounds = self.scene.pond_pixel_bounds()
        if bounds.width <= 0 or bounds.height <= 0:
            return False
        px = player.pos[0] + player.size[0] / 2
        py = player.pos[1] + player.size[1] / 2
        return bounds.inflate(self.POND_INTERACT_RADIUS, self.POND_INTERACT_RADIUS).collidepoint(px, py)

    def observable_wildlife_screen_positions(self, player: "Player") -> list[tuple[int, int]]:
        """Return screen-space centers for wildlife close enough to observe."""
        px = player.pos[0] + player.size[0] / 2
        py = player.pos[1] + player.size[1] / 2
        positions: list[tuple[int, int]] = []
        for bunny in self.wildlife:
            if ((px - bunny.pos[0]) ** 2 + (py - bunny.pos[1]) ** 2) ** 0.5 <= self.WILDLIFE_OBSERVATION_RADIUS:
                positions.append((self.rect.left + int(bunny.pos[0]), self.rect.top + int(bunny.pos[1])))
        return positions

    def wildlife_observation_for_player(self, player: "Player") -> str | None:
        if self.observable_wildlife_screen_positions(player):
            return "Bunny nearby: observe camouflage and foraging"
        return None

    def _wildlife_field_note(self) -> str:
        title, _guidance = self.area_title_and_guidance()
        if self.area_id == "pond":
            return (
                f"{title}: bunny browsing near the bank; compare camouflage "
                "with guppy predator pressure."
            )
        return f"{title}: bunny camouflage observed near dense cover."

    def wildlife_field_note_for_player(self, player: "Player") -> str | None:
        if self.wildlife_observation_for_player(player) is None:
            return None
        return self._wildlife_field_note()

    def wildlife_field_note_at_screen_pos(self, pos: tuple[int, int]) -> str | None:
        world_x = pos[0] - self.rect.left
        world_y = pos[1] - self.rect.top
        for bunny in self.wildlife:
            if ((world_x - bunny.pos[0]) ** 2 + (world_y - bunny.pos[1]) ** 2) ** 0.5 <= 18:
                return self._wildlife_field_note()
        return None

    def interaction_prompt_for_player(self, player: "Player") -> str | None:
        if self.pond_in_range(player):
            return "[E/Enter] Research Pond"
        if self.cottage_in_range(player):
            return "[E/Enter] Field Journal"
        if self.wildlife_observation_for_player(player) is not None:
            return "[E/Enter] Observe bunny: camouflage and foraging"
        return None

    def interaction_prompt_anchor_for_player(self, player: "Player", prompt: str | None) -> tuple[int, int] | None:
        if prompt is None:
            return None
        if prompt == "[E/Enter] Research Pond":
            bounds = self.scene.pond_pixel_bounds()
            return (self.rect.left + bounds.centerx - 52, self.rect.top + bounds.top - 18)
        if prompt == "[E/Enter] Field Journal":
            cottage = next((o for o in self.scene.objects if o.kind == "cottage"), None)
            if cottage is not None:
                return (
                    self.rect.left + cottage.col * TILE_PIXELS,
                    self.rect.top + cottage.row * TILE_PIXELS - 18,
                )
        if prompt.startswith("[E/Enter] Observe bunny"):
            return (
                self.rect.left + int(player.pos[0]) - 52,
                self.rect.top + int(player.pos[1]) - 18,
            )
        return None

    def interaction_prompt_rect_for_player(
        self,
        player: "Player",
        prompt: str | None,
        font: pygame.font.Font,
    ) -> pygame.Rect | None:
        """Return the current prompt's clickable screen rect, if any."""
        prompt_pos = self.interaction_prompt_anchor_for_player(player, prompt)
        if prompt is None or prompt_pos is None:
            return None
        text = font.render(prompt, True, (255, 255, 255))
        return pygame.Rect(prompt_pos[0], prompt_pos[1], text.get_width() + 6, text.get_height() + 4)

    def pond_at_screen_pos(self, pos: tuple[int, int]) -> bool:
        if self.area_id != "pond":
            return False
        bounds = self.scene.pond_pixel_bounds()
        if bounds.width <= 0 or bounds.height <= 0:
            return False
        screen_bounds = bounds.move(self.rect.left, self.rect.top)
        return screen_bounds.inflate(self.POND_CLICK_MARGIN * 2, self.POND_CLICK_MARGIN * 2).collidepoint(pos)

    def cottage_at_screen_pos(self, pos: tuple[int, int]) -> bool:
        if self.area_id != "home":
            return False
        cottage = next((o for o in self.scene.objects if o.kind == "cottage"), None)
        if cottage is None:
            return False
        bounds = pygame.Rect(
            self.rect.left + cottage.col * TILE_PIXELS,
            self.rect.top + cottage.row * TILE_PIXELS,
            self.COTTAGE_TILE_SIZE[0] * TILE_PIXELS,
            self.COTTAGE_TILE_SIZE[1] * TILE_PIXELS,
        )
        return bounds.inflate(self.COTTAGE_CLICK_MARGIN * 2, self.COTTAGE_CLICK_MARGIN * 2).collidepoint(pos)

    def _draw_forest_mood(self, surface: pygame.Surface) -> None:
        if self.area_id != "forest":
            return
        overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.ellipse(overlay, (108, 178, 91, 18), pygame.Rect(250, 172, 420, 255))
        pygame.draw.ellipse(overlay, (108, 178, 91, 12), pygame.Rect(330, 280, 260, 140))
        surface.blit(overlay, self.rect.topleft)

    def area_exit_marker_rects(self) -> dict[str, pygame.Rect]:
        """Return screen-space signpost rects for exits from the current area."""
        marker_size = (74, 24)
        if self.area_id == "home":
            return {
                "pond": pygame.Rect(
                    self.rect.right - 12 - marker_size[0],
                    self.rect.centery - marker_size[1] // 2,
                    *marker_size,
                ),
                "forest": pygame.Rect(
                    self.rect.centerx - marker_size[0] // 2,
                    self.rect.bottom - 12 - marker_size[1],
                    *marker_size,
                ),
            }
        if self.area_id == "pond":
            return {
                "home": pygame.Rect(
                    self.rect.left + 12,
                    self.rect.centery - marker_size[1] // 2,
                    *marker_size,
                )
            }
        if self.area_id == "forest":
            return {
                "home": pygame.Rect(
                    self.rect.centerx - marker_size[0] // 2,
                    self.rect.top + 12,
                    *marker_size,
                )
            }
        return {}

    def area_exit_marker_labels(self) -> dict[str, str]:
        """Return directional labels for currently visible area signposts."""
        if self.area_id == "home":
            return {"pond": "POND →", "forest": "FOREST ↓"}
        if self.area_id == "pond":
            return {"home": "← HOME"}
        if self.area_id == "forest":
            return {"home": "HOME ↑"}
        return {}

    def area_at_exit_marker_pos(self, pos: tuple[int, int]) -> str | None:
        margin = self.EXIT_MARKER_CLICK_MARGIN
        for target, rect in self.area_exit_marker_rects().items():
            if rect.inflate(margin * 2, margin * 2).collidepoint(pos):
                return target
        return None

    def area_minimap_node_rects(self) -> dict[str, pygame.Rect]:
        """Return screen-space node rects for the area guide/minimap."""
        box = pygame.Rect(self.rect.right - 154, self.rect.top + 12, 136, 68)
        return {
            "home": pygame.Rect(box.left + 54, box.top + 18, 14, 14),
            "pond": pygame.Rect(box.left + 103, box.top + 18, 14, 14),
            "forest": pygame.Rect(box.left + 54, box.top + 45, 14, 14),
        }

    def area_minimap_hit_rects(self) -> dict[str, pygame.Rect]:
        """Return generous click targets for minimap nodes and their labels."""
        nodes = self.area_minimap_node_rects()
        return {
            area_id: pygame.Rect(rect.centerx - 24, rect.top - 5, 48, 31)
            for area_id, rect in nodes.items()
        }

    def area_at_minimap_pos(self, pos: tuple[int, int]) -> str | None:
        for area_id, rect in self.area_minimap_hit_rects().items():
            if rect.collidepoint(pos):
                return area_id
        return None

    def area_minimap_labels(self) -> dict[str, str]:
        """Return minimap labels with keyboard shortcuts for quick travel."""
        return {"home": "1 Home", "pond": "2 Pond", "forest": "3 Forest"}

    def area_title_and_guidance(self) -> tuple[str, str]:
        """Return display copy for the current area title card."""
        return self.AREA_GUIDANCE[self.area_id]

    def area_progress_text(self) -> str:
        """Return concise exploration progress for the title card."""
        return f"Field sites discovered: {len(self.visited_area_ids)}/{len(self.AREA_ORDER)}"

    def _draw_area_title_card(self, surface: pygame.Surface, font: pygame.font.Font | None) -> None:
        if font is None:
            return
        title, guidance = self.area_title_and_guidance()
        title_surface = font.render(title, True, (255, 242, 168))
        guidance_surface = font.render(guidance, True, (247, 250, 232))
        progress_surface = font.render(self.area_progress_text(), True, (205, 230, 196))
        width = max(title_surface.get_width(), guidance_surface.get_width(), progress_surface.get_width()) + 18
        box = pygame.Rect(self.rect.left + 12, self.rect.top + 10, width, 60)
        overlay = pygame.Surface(box.size, pygame.SRCALPHA)
        overlay.fill(self.AREA_CARD_BG)
        surface.blit(overlay, box.topleft)
        pygame.draw.rect(surface, self.AREA_CARD_BORDER, box, 1, border_radius=5)
        surface.blit(title_surface, (box.left + 9, box.top + 6))
        surface.blit(guidance_surface, (box.left + 9, box.top + 24))
        surface.blit(progress_surface, (box.left + 9, box.top + 42))

    def _draw_area_exit_markers(self, surface: pygame.Surface, font: pygame.font.Font | None) -> None:
        labels = self.area_exit_marker_labels()
        for target, rect in self.area_exit_marker_rects().items():
            pygame.draw.rect(surface, self.EXIT_MARKER_FILL, rect, border_radius=6)
            pygame.draw.rect(surface, self.EXIT_MARKER_BORDER, rect, 2, border_radius=6)
            if font is None:
                continue
            text = font.render(labels[target], True, self.EXIT_MARKER_BORDER)
            surface.blit(text, text.get_rect(center=rect.center))

    def _draw_area_minimap(self, surface: pygame.Surface, font: pygame.font.Font | None) -> None:
        nodes = self.area_minimap_node_rects()
        box = pygame.Rect(self.rect.right - 154, self.rect.top + 12, 136, 68)
        overlay = pygame.Surface(box.size, pygame.SRCALPHA)
        overlay.fill(self.MINIMAP_BG)
        surface.blit(overlay, box.topleft)
        pygame.draw.rect(surface, (236, 246, 221), box, 1, border_radius=5)
        pygame.draw.line(surface, (236, 246, 221), nodes["home"].center, nodes["pond"].center, 2)
        pygame.draw.line(surface, (236, 246, 221), nodes["home"].center, nodes["forest"].center, 2)
        for area_id, rect in nodes.items():
            if area_id == self.area_id:
                color = self.MINIMAP_CURRENT
            elif area_id in self.visited_area_ids:
                color = self.MINIMAP_VISITED
            else:
                color = self.MINIMAP_UNVISITED
            pygame.draw.ellipse(surface, color, rect)
            pygame.draw.ellipse(surface, (42, 67, 45), rect, 1)
        if font is not None:
            labels = self.area_minimap_labels()
            for area_id, rect in nodes.items():
                text = font.render(labels[area_id], True, (247, 250, 232))
                label_pos = (rect.centerx - text.get_width() // 2, rect.bottom + 1)
                surface.blit(text, label_pos)

    def draw(self, surface: pygame.Surface, player: "Player | None" = None, font: pygame.font.Font | None = None) -> None:
        # The playfield is 1000x596, which is intentionally not an exact
        # multiple of the 32px tile size. Fill the panel first so the partial
        # right/bottom gutters still read as terrain instead of black screen.
        surface.fill((94, 143, 72), self.rect)
        self.scene.tilemap.draw(surface, origin=(self.rect.left, self.rect.top))
        self._draw_forest_mood(surface)
        # is_walkable / collision — only visuals change here.
        objs = self._ensure_objects()
        for obj in sorted(self.scene.objects, key=lambda item: item.row):
            sprite = objs.get(obj.kind)
            if sprite is None:
                continue
            x = self.rect.left + obj.col * TILE_PIXELS
            if obj.kind.startswith("tree_"):
                # Anchor tree at cell's bottom edge so the canopy rises
                # above the cell. (sprite.height - TILE_PIXELS) lifts the
                # blit origin upward by the canopy overhang.
                y = self.rect.top + obj.row * TILE_PIXELS - (sprite.get_height() - TILE_PIXELS)
            elif obj.kind != "cottage" and sprite.get_height() > TILE_PIXELS:
                y = self.rect.top + obj.row * TILE_PIXELS - (sprite.get_height() - TILE_PIXELS)
            else:
                y = self.rect.top + obj.row * TILE_PIXELS
            surface.blit(sprite, (x, y))
        # Bunnies drawn after objects, before pond fish (so a bunny near a tree appears in front of the tree).
        for b in self.wildlife:
            b.draw(surface, origin=(self.rect.left, self.rect.top))
        if player is not None:
            for center in self.observable_wildlife_screen_positions(player):
                pygame.draw.circle(surface, (255, 242, 168), center, 16, 2)
                pygame.draw.circle(surface, (42, 67, 45), center, 18, 1)
        # Pond fish (after objects, before player so fish go behind player).
        self.pond_view.draw(surface, origin=(0, 0))
        self._draw_area_exit_markers(surface, font)
        self._draw_area_title_card(surface, font)
        self._draw_area_minimap(surface, font)
        if player is not None:
            player.draw(surface, origin=(self.rect.left, self.rect.top))
        if player is not None and font is not None:
            prompt = self.interaction_prompt_for_player(player)
            prompt_pos = self.interaction_prompt_anchor_for_player(player, prompt)
            if prompt is None:
                prompt = self.area_exit_hint_for_player(player)
                if prompt is not None:
                    text_probe = font.render(prompt, True, (255, 255, 255))
                    prompt_pos = (
                        self.rect.centerx - text_probe.get_width() // 2,
                        self.rect.bottom - text_probe.get_height() - 12,
                    )
            if prompt is not None and prompt_pos is not None:
                text = font.render(prompt, True, (255, 255, 255))
                shadow = pygame.Surface((text.get_width() + 6, text.get_height() + 4), pygame.SRCALPHA)
                shadow.fill((0, 0, 0, 160))
                surface.blit(shadow, prompt_pos)
                surface.blit(text, (prompt_pos[0] + 3, prompt_pos[1] + 2))
