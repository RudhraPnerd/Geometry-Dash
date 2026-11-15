import random
from typing import Tuple
from src.utils.math_helpers import lerp


class Camera:
    """Manages horizontal scrolling, vertical tracking, and impact screen shake."""

    def __init__(self, screen_width: int, screen_height: int, anchor_x: int) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.anchor_x = anchor_x
        self.x = 0.0
        self.y = 0.0
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.shake_offset: Tuple[int, int] = (0, 0)

    def reset(self, player_x: float = 0.0) -> None:
        self.x = max(0.0, player_x - self.anchor_x)
        self.y = 0.0
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.shake_offset = (0, 0)

    def trigger_shake(self, duration: float = 0.25, intensity: float = 10.0) -> None:
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_intensity = max(self.shake_intensity, intensity)

    def update(self, dt: float, player_x: float, player_y: float, ground_y: float) -> None:
        self.x = player_x - self.anchor_x

        # Smooth vertical camera follow when player climbs high
        desired_y = 0.0
        upper_threshold = ground_y - self.screen_height * 0.55
        if player_y < upper_threshold:
            desired_y = player_y - upper_threshold
        self.y = lerp(self.y, desired_y, min(1.0, dt * 6.5))

        if self.shake_timer > 0.0:
            self.shake_timer -= dt
            mag = int(self.shake_intensity * max(0.0, self.shake_timer / 0.25))
            self.shake_offset = (
                random.randint(-mag, mag) if mag > 0 else 0,
                random.randint(-mag, mag) if mag > 0 else 0,
            )
        else:
            self.shake_offset = (0, 0)
            self.shake_intensity = 0.0

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        sx = int(world_x - self.x + self.shake_offset[0])
        sy = int(world_y - self.y + self.shake_offset[1])
        return sx, sy
