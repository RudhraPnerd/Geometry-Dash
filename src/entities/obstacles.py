from dataclasses import dataclass
from typing import Dict, Tuple
import pygame
from src.utils.math_helpers import pulse_scale


@dataclass
class LevelObject:
    """Represents a single interactive or solid object inside a level."""

    obj_type: str  # block, slab, spike, spike_down, orb, pad, portal_ship, portal_cube, finish
    x: float
    y: float
    width: int
    height: int
    triggered: bool = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    @property
    def hazard_rect(self) -> pygame.Rect:
        # Spikes have a tighter triangular-approximated inner hitbox
        if self.obj_type in ("spike", "spike_down"):
            w_pad = int(self.width * 0.30)
            h_pad = int(self.height * 0.24)
            return pygame.Rect(
                int(self.x) + w_pad,
                int(self.y) + h_pad,
                max(6, self.width - w_pad * 2),
                max(6, self.height - h_pad * 2),
            )
        return self.rect

    def draw(
        self,
        surface: pygame.Surface,
        camera_x: float,
        camera_y: float,
        colors: Dict[str, Tuple[int, int, int]],
        time_sec: float,
    ) -> None:
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        r = pygame.Rect(sx, sy, self.width, self.height)

        if self.obj_type in ("block", "slab"):
            fill = tuple(colors.get("block_fill", (22, 34, 72)))
            outline = tuple(colors.get("block_outline", (110, 220, 255)))
            pygame.draw.rect(surface, fill, r)
            pygame.draw.rect(surface, outline, r, width=2)
            inner = r.inflate(-10, -10)
            if inner.width > 4 and inner.height > 4:
                pygame.draw.rect(surface, outline, inner, width=1)

        elif self.obj_type == "spike":
            fill = tuple(colors.get("spike_fill", (20, 22, 30)))
            outline = tuple(colors.get("spike_outline", (255, 255, 255)))
            pts = [
                (sx + self.width // 2, sy + 2),
                (sx + self.width - 2, sy + self.height - 1),
                (sx + 2, sy + self.height - 1),
            ]
            pygame.draw.polygon(surface, fill, pts)
            pygame.draw.polygon(surface, outline, pts, width=2)

        elif self.obj_type == "spike_down":
            fill = tuple(colors.get("spike_fill", (20, 22, 30)))
            outline = tuple(colors.get("spike_outline", (255, 255, 255)))
            pts = [
                (sx + 2, sy + 1),
                (sx + self.width - 2, sy + 1),
                (sx + self.width // 2, sy + self.height - 2),
            ]
            pygame.draw.polygon(surface, fill, pts)
            pygame.draw.polygon(surface, outline, pts, width=2)

        elif self.obj_type == "orb":
            col = tuple(colors.get("orb_yellow", (255, 225, 40)))
            scale = pulse_scale(time_sec, speed=7.5, amplitude=0.14)
            cx = sx + self.width // 2
            cy = sy + self.height // 2
            radius = int((self.width * 0.36) * scale)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), radius + 4, width=2)
            pygame.draw.circle(surface, col, (cx, cy), radius)

        elif self.obj_type == "pad":
            col = tuple(colors.get("pad_yellow", (255, 200, 30)))
            pad_h = max(10, self.height // 4)
            pad_rect = pygame.Rect(sx + 4, sy + self.height - pad_h, self.width - 8, pad_h)
            pygame.draw.rect(surface, col, pad_rect, border_radius=4)
            pygame.draw.rect(surface, (255, 255, 255), pad_rect, width=2, border_radius=4)

        elif self.obj_type in ("portal_ship", "portal_cube"):
            is_ship = self.obj_type == "portal_ship"
            col = tuple(colors.get("portal_ship" if is_ship else "portal_cube", (255, 85, 205)))
            pygame.draw.ellipse(surface, col, r, width=6)
            inner_r = r.inflate(-14, -18)
            if inner_r.width > 4 and inner_r.height > 4:
                pygame.draw.ellipse(surface, (255, 255, 255), inner_r, width=2)

        elif self.obj_type == "finish":
            pygame.draw.rect(surface, (255, 235, 90), r)
            pygame.draw.rect(surface, (255, 255, 255), r, width=3)
