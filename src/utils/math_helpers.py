import math
from typing import Tuple


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * clamp(t, 0.0, 1.0)


def lerp_color(
    color_a: Tuple[int, int, int],
    color_b: Tuple[int, int, int],
    t: float,
) -> Tuple[int, int, int]:
    t = clamp(t, 0.0, 1.0)
    return (
        int(lerp(color_a[0], color_b[0], t)),
        int(lerp(color_a[1], color_b[1], t)),
        int(lerp(color_a[2], color_b[2], t)),
    )


def snap_angle_90(angle_deg: float) -> float:
    return round(angle_deg / 90.0) * 90.0


def pulse_scale(time_sec: float, speed: float = 6.0, amplitude: float = 0.08) -> float:
    return 1.0 + math.sin(time_sec * speed) * amplitude
