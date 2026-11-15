from dataclasses import dataclass
from typing import Dict, Tuple
import pygame
from src.utils.math_helpers import snap_angle_90


@dataclass
class CheckpointState:
    x: float
    y: float
    vy: float
    angle: float
    mode: str
    on_ground: bool


class Player:
    """Geometry Dash player supporting Cube and Ship physics modes."""

    def __init__(self, start_x: float, ground_y: float, size: int, physics_cfg: Dict[str, float]) -> None:
        self.start_x = start_x
        self.ground_y = ground_y
        self.size = size
        self.physics = physics_cfg

        self.x = start_x
        self.y = ground_y - size
        self.vy = 0.0
        self.angle = 0.0
        self.mode = "cube"  # "cube" or "ship"
        self.on_ground = True
        self.is_dead = False
        self.jump_buffer_timer = 0.0
        self.orb_consumed_this_press = False

    def reset(self, checkpoint: CheckpointState = None) -> None:
        if checkpoint is not None:
            self.x = checkpoint.x
            self.y = checkpoint.y
            self.vy = checkpoint.vy
            self.angle = checkpoint.angle
            self.mode = checkpoint.mode
            self.on_ground = checkpoint.on_ground
        else:
            self.x = self.start_x
            self.y = self.ground_y - self.size
            self.vy = 0.0
            self.angle = 0.0
            self.mode = "cube"
            self.on_ground = True

        self.is_dead = False
        self.jump_buffer_timer = 0.0
        self.orb_consumed_this_press = False

    def create_checkpoint(self) -> CheckpointState:
        return CheckpointState(
            x=self.x,
            y=self.y,
            vy=self.vy,
            angle=self.angle,
            mode=self.mode,
            on_ground=self.on_ground,
        )

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    @property
    def hazard_hitbox(self) -> pygame.Rect:
        # Forgiving inner hitbox matching Geometry Dash feel
        inset = int(self.size * 0.22)
        return pygame.Rect(
            int(self.x) + inset,
            int(self.y) + inset,
            self.size - inset * 2,
            self.size - inset * 2,
        )

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.size * 0.5, self.y + self.size * 0.5)

    def request_jump(self) -> None:
        self.jump_buffer_timer = 0.11

    def trigger_orb(self) -> None:
        self.vy = float(self.physics.get("orb_velocity", -880.0))
        self.on_ground = False
        self.jump_buffer_timer = 0.0
        self.orb_consumed_this_press = True

    def trigger_pad(self) -> None:
        self.vy = float(self.physics.get("pad_velocity", -1180.0))
        self.on_ground = False
        self.jump_buffer_timer = 0.0

    def set_mode(self, new_mode: str) -> bool:
        if new_mode in ("cube", "ship") and self.mode != new_mode:
            self.mode = new_mode
            if new_mode == "cube":
                self.angle = snap_angle_90(self.angle)
            return True
        return False

    def update(self, dt: float, jump_held: bool) -> bool:
        """Advances physics by dt seconds. Returns True if a ground/buffer jump occurred."""
        if self.is_dead:
            return False

        jumped = False
        speed = float(self.physics.get("player_speed", 490.0))
        self.x += speed * dt

        if not jump_held:
            self.orb_consumed_this_press = False

        if self.jump_buffer_timer > 0.0:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)

        if self.mode == "cube":
            jumped = self._update_cube(dt, jump_held)
        else:
            self._update_ship(dt, jump_held)

        # Floor clamping
        if self.y + self.size >= self.ground_y:
            self.y = self.ground_y - self.size
            self.vy = 0.0
            if not self.on_ground:
                self.angle = snap_angle_90(self.angle)
            self.on_ground = True

        # Ceiling safety clamp (for ship mode)
        ceiling_y = -240.0
        if self.y < ceiling_y:
            self.y = ceiling_y
            if self.vy < 0:
                self.vy = 0.0

        return jumped

    def _update_cube(self, dt: float, jump_held: bool) -> bool:
        jumped = False
        if self.on_ground and (jump_held or self.jump_buffer_timer > 0.0):
            self.vy = float(self.physics.get("jump_velocity", -860.0))
            self.on_ground = False
            self.jump_buffer_timer = 0.0
            jumped = True

        if not self.on_ground:
            gravity = float(self.physics.get("gravity", 2750.0))
            terminal = float(self.physics.get("terminal_velocity", 1350.0))
            rot_speed = float(self.physics.get("rotation_speed", 415.0))
            self.vy = min(terminal, self.vy + gravity * dt)
            self.y += self.vy * dt
            self.angle = (self.angle - rot_speed * dt) % 360.0
        else:
            self.angle = snap_angle_90(self.angle)

        return jumped

    def _update_ship(self, dt: float, jump_held: bool) -> None:
        ship_grav = float(self.physics.get("ship_gravity", 1350.0))
        ship_thrust = float(self.physics.get("ship_thrust", -1650.0))
        max_vy = float(self.physics.get("ship_max_vy", 750.0))

        accel = ship_thrust if jump_held else ship_grav
        self.vy = max(-max_vy, min(max_vy, self.vy + accel * dt))
        self.y += self.vy * dt
        if self.y + self.size < self.ground_y:
            self.on_ground = False

        # Tilt ship nose smoothly based on vertical speed
        self.angle = max(-32.0, min(32.0, -(self.vy / max_vy) * 30.0))

    def draw(
        self,
        surface: pygame.Surface,
        camera_x: float,
        camera_y: float,
        primary: Tuple[int, int, int],
        secondary: Tuple[int, int, int],
        outline: Tuple[int, int, int],
    ) -> None:
        if self.is_dead:
            return

        icon_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        if self.mode == "cube":
            self._render_cube_icon(icon_surf, primary, secondary, outline)
        else:
            self._render_ship_icon(icon_surf, primary, secondary, outline)

        rotated = pygame.transform.rotate(icon_surf, self.angle)
        cx, cy = self.center
        draw_rect = rotated.get_rect(center=(int(cx - camera_x), int(cy - camera_y)))
        surface.blit(rotated, draw_rect.topleft)

    def _render_cube_icon(
        self,
        surf: pygame.Surface,
        primary: Tuple[int, int, int],
        secondary: Tuple[int, int, int],
        outline: Tuple[int, int, int],
    ) -> None:
        s = self.size
        pygame.draw.rect(surf, primary, (0, 0, s, s), border_radius=5)
        pygame.draw.rect(surf, outline, (0, 0, s, s), width=3, border_radius=5)

        # Inner accent frame
        inset = 7
        pygame.draw.rect(surf, secondary, (inset, inset, s - inset * 2, s - inset * 2), border_radius=3)
        pygame.draw.rect(surf, outline, (inset, inset, s - inset * 2, s - inset * 2), width=2, border_radius=3)

        # Classic GD icon eyes & mouth
        eye_y = int(s * 0.34)
        pygame.draw.rect(surf, outline, (int(s * 0.25), eye_y, 7, 7))
        pygame.draw.rect(surf, outline, (int(s * 0.60), eye_y, 7, 7))
        pygame.draw.rect(surf, outline, (int(s * 0.28), int(s * 0.62), int(s * 0.44), 6))

    def _render_ship_icon(
        self,
        surf: pygame.Surface,
        primary: Tuple[int, int, int],
        secondary: Tuple[int, int, int],
        outline: Tuple[int, int, int],
    ) -> None:
        s = self.size
        # Mini pilot cube inside cockpit
        mini = int(s * 0.46)
        mini_x = int(s * 0.24)
        mini_y = int(s * 0.14)
        pygame.draw.rect(surf, primary, (mini_x, mini_y, mini, mini), border_radius=3)
        pygame.draw.rect(surf, outline, (mini_x, mini_y, mini, mini), width=2, border_radius=3)

        # Sleek ship hull
        hull_pts = [
            (4, int(s * 0.48)),
            (int(s * 0.72), int(s * 0.48)),
            (s - 2, int(s * 0.68)),
            (int(s * 0.76), s - 4),
            (10, s - 4),
            (2, int(s * 0.72)),
        ]
        pygame.draw.polygon(surf, secondary, hull_pts)
        pygame.draw.polygon(surf, outline, hull_pts, width=3)
