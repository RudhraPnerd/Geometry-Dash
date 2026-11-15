from typing import Dict, List, Tuple
import pygame
from src.entities.obstacles import LevelObject
from src.entities.particles import ParticleSystem
from src.entities.player import CheckpointState, Player
from src.utils.math_helpers import lerp_color


class Renderer:
    """Renders parallax backgrounds, tiled floor, level objects, player, and HUD."""

    def __init__(self, screen: pygame.Surface, colors: Dict[str, List[int]]) -> None:
        self.screen = screen
        self.colors = colors
        self.width = screen.get_width()
        self.height = screen.get_height()

        self.font_title = pygame.font.SysFont("arial", 64, bold=True)
        self.font_large = pygame.font.SysFont("arial", 40, bold=True)
        self.font_med = pygame.font.SysFont("arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18, bold=True)

    def draw_background(self, camera_x: float, mode: str) -> None:
        if mode == "ship":
            top_col = tuple(self.colors.get("ship_bg_top", [95, 22, 110]))
            bot_col = tuple(self.colors.get("ship_bg_bottom", [185, 45, 130]))
        else:
            top_col = tuple(self.colors.get("bg_top", [18, 42, 115]))
            bot_col = tuple(self.colors.get("bg_bottom", [38, 92, 210]))

        # Banded vertical gradient for crisp 60 FPS rendering
        bands = 24
        band_h = self.height // bands + 1
        for i in range(bands):
            col = lerp_color(top_col, bot_col, i / max(1, bands - 1))
            pygame.draw.rect(self.screen, col, (0, i * band_h, self.width, band_h))

        # Parallax background geometric squares
        grid_spacing = 160
        offset_x = int(camera_x * 0.25) % grid_spacing
        parallax_col = lerp_color(top_col, (255, 255, 255), 0.12)
        for gx in range(-grid_spacing, self.width + grid_spacing, grid_spacing):
            for gy in range(40, self.height - 160, grid_spacing):
                rect = pygame.Rect(gx - offset_x, gy, 96, 96)
                pygame.draw.rect(self.screen, parallax_col, rect, width=2)

    def draw_ground(self, camera_x: float, camera_y: float, ground_y: float) -> None:
        screen_gy = int(ground_y - camera_y)
        ground_fill = tuple(self.colors.get("ground_fill", [12, 26, 78]))
        ground_line = tuple(self.colors.get("ground_line", [120, 210, 255]))

        if screen_gy < self.height:
            pygame.draw.rect(
                self.screen,
                ground_fill,
                (0, screen_gy, self.width, self.height - screen_gy),
            )
            # Scrolling floor tile grid
            tile = 64
            offset = int(camera_x) % tile
            grid_col = lerp_color(ground_fill, ground_line, 0.25)
            for x in range(-tile, self.width + tile, tile):
                pygame.draw.line(
                    self.screen,
                    grid_col,
                    (x - offset, screen_gy),
                    (x - offset, self.height),
                    2,
                )
            pygame.draw.line(self.screen, ground_line, (0, screen_gy), (self.width, screen_gy), 4)

    def draw_checkpoints(self, checkpoints: List[CheckpointState], camera_x: float, camera_y: float) -> None:
        for cp in checkpoints:
            sx = int(cp.x - camera_x + 18)
            sy = int(cp.y - camera_y + 18)
            pts = [(sx, sy - 14), (sx + 12, sy), (sx, sy + 14), (sx - 12, sy)]
            pygame.draw.polygon(self.screen, (60, 255, 160), pts)
            pygame.draw.polygon(self.screen, (255, 255, 255), pts, width=2)

    def draw_world(
        self,
        player: Player,
        objects: List[LevelObject],
        particles: ParticleSystem,
        checkpoints: List[CheckpointState],
        camera_x: float,
        camera_y: float,
        ground_y: float,
        time_sec: float,
    ) -> None:
        self.draw_background(camera_x, player.mode)

        for obj in objects:
            if obj.x + obj.width < camera_x - 64 or obj.x > camera_x + self.width + 64:
                continue
            obj.draw(self.screen, camera_x, camera_y, self.colors, time_sec)

        if checkpoints:
            self.draw_checkpoints(checkpoints, camera_x, camera_y)

        particles.draw(self.screen, camera_x, camera_y)

        p_prim = tuple(self.colors.get("player_primary", [125, 255, 50]))
        p_sec = tuple(self.colors.get("player_secondary", [0, 235, 255]))
        p_out = tuple(self.colors.get("player_outline", [15, 20, 35]))
        player.draw(self.screen, camera_x, camera_y, p_prim, p_sec, p_out)

        self.draw_ground(camera_x, camera_y, ground_y)

    def draw_hud(
        self,
        progress_pct: float,
        best_pct: float,
        attempt: int,
        practice_mode: bool,
        muted: bool,
    ) -> None:
        # Top progress bar
        bar_w = 420
        bar_h = 16
        bar_x = (self.width - bar_w) // 2
        bar_y = 22
        pygame.draw.rect(self.screen, (15, 20, 45), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        fill_w = int(bar_w * max(0.0, min(1.0, progress_pct / 100.0)))
        bar_col = (70, 255, 160) if practice_mode else (125, 255, 50)
        if fill_w > 0:
            pygame.draw.rect(self.screen, bar_col, (bar_x, bar_y, fill_w, bar_h), border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=8)

        pct_txt = self.font_small.render(f"{progress_pct:.1f}%", True, (255, 255, 255))
        self.screen.blit(pct_txt, (bar_x + bar_w + 12, bar_y - 2))

        mode_label = "PRACTICE" if practice_mode else "NORMAL"
        info_txt = self.font_small.render(
            f"Attempt {attempt}  |  Mode: {mode_label}  |  Best: {best_pct:.1f}%",
            True,
            (225, 240, 255),
        )
        self.screen.blit(info_txt, (24, 20))

        mute_txt = self.font_small.render(
            f"[M] Audio: {'MUTED' if muted else 'ON'}  |  [P] Pause",
            True,
            (225, 240, 255),
        )
        self.screen.blit(mute_txt, (self.width - mute_txt.get_width() - 24, 20))

    def draw_menu_overlay(
        self,
        high_score: float,
        practice_high_score: float,
        total_attempts: int,
        practice_mode: bool,
        muted: bool,
    ) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((8, 14, 38, 155))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("GEOMETRY DASH", True, (125, 255, 50))
        subtitle = self.font_large.render("STEREO MADNESS", True, (0, 235, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 165)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, 225)))

        mode_str = "PRACTICE MODE (Checkpoints Enabled)" if practice_mode else "NORMAL MODE"
        mode_col = (70, 255, 160) if practice_mode else (255, 225, 60)
        mode_surf = self.font_med.render(mode_str, True, mode_col)
        self.screen.blit(mode_surf, mode_surf.get_rect(center=(self.width // 2, 300)))

        stats = self.font_med.render(
            f"Best: {high_score:.1f}%   |   Practice Best: {practice_high_score:.1f}%   |   Attempts: {total_attempts}",
            True,
            (255, 255, 255),
        )
        self.screen.blit(stats, stats.get_rect(center=(self.width // 2, 355)))

        controls = [
            "Press [SPACE] / [UP] / [CLICK] to Start & Jump (Hold in Ship Mode)",
            "Press [TAB] to Toggle Normal / Practice Mode",
            "Press [Z] in Practice Mode to Place Manual Checkpoint",
            f"Press [M] to Mute/Unmute Audio ({'MUTED' if muted else 'ON'})",
        ]
        for idx, line in enumerate(controls):
            line_surf = self.font_small.render(line, True, (210, 230, 255))
            self.screen.blit(line_surf, line_surf.get_rect(center=(self.width // 2, 435 + idx * 34)))

    def draw_pause_overlay(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 15, 35, 175))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("PAUSED", True, (255, 255, 255))
        hint = self.font_med.render("[P] Resume   |   [R] Restart   |   [ESC] Main Menu", True, (0, 235, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 30)))
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height // 2 + 35)))

    def draw_victory_overlay(self, attempts: int, is_new_best: bool) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 25, 45, 185))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("LEVEL COMPLETE!", True, (125, 255, 50))
        sub = self.font_large.render(
            "NEW RECORD - 100%!" if is_new_best else f"Completed in {attempts} Attempts!",
            True,
            (255, 230, 70),
        )
        hint = self.font_med.render("Press [SPACE] to Play Again   |   [ESC] Main Menu", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 60)))
        self.screen.blit(sub, sub.get_rect(center=(self.width // 2, self.height // 2 + 5)))
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height // 2 + 70)))
