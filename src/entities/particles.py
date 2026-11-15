import math
import random
from dataclasses import dataclass
from typing import List, Tuple
import pygame


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    size: float
    color: Tuple[int, int, int]
    life: float
    max_life: float
    gravity: float = 0.0
    shrink: bool = True


class ParticleSystem:
    """Manages cube trail sparks, jump bursts, orb rings, and shatter explosions."""

    def __init__(self) -> None:
        self.particles: List[Particle] = []
        self.trail_accumulator = 0.0

    def clear(self) -> None:
        self.particles.clear()
        self.trail_accumulator = 0.0

    def emit_trail(self, x: float, y: float, color: Tuple[int, int, int], dt: float) -> None:
        self.trail_accumulator += dt
        if self.trail_accumulator < 0.016:
            return
        self.trail_accumulator = 0.0
        self.particles.append(
            Particle(
                x=x + random.uniform(-4, 4),
                y=y + random.uniform(-6, 6),
                vx=random.uniform(-90, -30),
                vy=random.uniform(-25, 25),
                size=random.uniform(5, 9),
                color=color,
                life=0.26,
                max_life=0.26,
            )
        )

    def emit_jump_dust(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        for _ in range(8):
            self.particles.append(
                Particle(
                    x=x + random.uniform(-14, 14),
                    y=y,
                    vx=random.uniform(-160, 40),
                    vy=random.uniform(-130, -20),
                    size=random.uniform(5, 10),
                    color=color,
                    life=0.32,
                    max_life=0.32,
                    gravity=380.0,
                )
            )

    def emit_orb_burst(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        for i in range(16):
            angle = (2 * math.pi * i) / 16
            speed = random.uniform(140, 290)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    size=random.uniform(5, 9),
                    color=color,
                    life=0.35,
                    max_life=0.35,
                )
            )

    def emit_death_explosion(
        self,
        x: float,
        y: float,
        primary: Tuple[int, int, int],
        secondary: Tuple[int, int, int],
    ) -> None:
        for i in range(38):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(120, 620)
            col = primary if i % 2 == 0 else secondary
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed - 120,
                    size=random.uniform(6, 15),
                    color=col,
                    life=random.uniform(0.45, 0.85),
                    max_life=0.85,
                    gravity=980.0,
                )
            )

    def update(self, dt: float) -> None:
        alive: List[Particle] = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.particles = alive

    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float) -> None:
        for p in self.particles:
            ratio = max(0.0, p.life / p.max_life)
            size = max(1, int(p.size * ratio)) if p.shrink else int(p.size)
            sx = int(p.x - camera_x - size / 2)
            sy = int(p.y - camera_y - size / 2)
            rect = pygame.Rect(sx, sy, size, size)
            pygame.draw.rect(surface, p.color, rect)
