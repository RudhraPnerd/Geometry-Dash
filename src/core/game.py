from typing import List
import pygame
from src.core.audio_manager import AudioManager
from src.core.camera import Camera
from src.entities.obstacles import LevelObject
from src.entities.particles import ParticleSystem
from src.entities.player import CheckpointState, Player
from src.level.collision import CollisionSystem
from src.level.level_loader import LevelBuilder
from src.ui.renderer import Renderer
from src.utils.config_manager import ConfigManager


class GeometryDashGame:
    """Main game loop and state controller."""

    def __init__(self, base_dir: str, config_path: str) -> None:
        pygame.init()
        self.base_dir = base_dir
        self.config = ConfigManager(config_path)

        win_cfg = self.config.data["window"]
        self.width = int(win_cfg.get("width", 1280))
        self.height = int(win_cfg.get("height", 720))
        self.fps = int(win_cfg.get("fps", 60))

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(win_cfg.get("title", "Geometry Dash"))
        self.clock = pygame.time.Clock()

        self.audio = AudioManager(self.base_dir, self.config)
        self.renderer = Renderer(self.screen, self.config.data.get("colors", {}))

        gameplay_cfg = self.config.data["gameplay"]
        self.tile_size = int(gameplay_cfg.get("tile_size", 48))
        self.ground_height = int(gameplay_cfg.get("ground_height", 144))
        self.ground_y = float(self.height - self.ground_height)
        self.player_start_x = float(gameplay_cfg.get("player_start_x", 260))
        self.checkpoint_interval = float(gameplay_cfg.get("checkpoint_interval_px", 1800))

        self.player = Player(
            start_x=self.player_start_x,
            ground_y=self.ground_y,
            size=self.tile_size,
            physics_cfg=self.config.data["physics"],
        )
        self.camera = Camera(self.width, self.height, anchor_x=int(self.player_start_x))
        self.particles = ParticleSystem()
        self.collision = CollisionSystem()
        self.level_builder = LevelBuilder(self.tile_size, self.ground_y)

        self.objects: List[LevelObject] = []
        self.finish_x: float = 10000.0
        self.checkpoints: List[CheckpointState] = []
        self.next_auto_cp_x: float = self.player_start_x + self.checkpoint_interval

        self.state = "MENU"  # MENU, PLAYING, PAUSED, RESPAWNING, VICTORY
        self.practice_mode = bool(gameplay_cfg.get("practice_mode_default", False))
        self.attempt = int(self.config.get("progress", "total_attempts", 0))
        self.respawn_timer = 0.0
        self.elapsed_time = 0.0
        self.last_run_new_best = False
        self.running = True

        self._load_level()
        self.audio.play_music("music_home", loop=True)

    def _load_level(self) -> None:
        self.objects, self.finish_x = self.level_builder.build_stereo_madness()
        self.checkpoints.clear()
        self.next_auto_cp_x = self.player_start_x + self.checkpoint_interval
        self.player.reset()
        self.camera.reset(self.player.x)
        self.particles.clear()

    def _start_new_run(self, keep_checkpoints: bool = False) -> None:
        self.attempt = self.config.record_attempt()
        if not keep_checkpoints:
            self.checkpoints.clear()
            self.next_auto_cp_x = self.player_start_x + self.checkpoint_interval
            self.player.reset()
        else:
            active_cp = self.checkpoints[-1] if self.checkpoints else None
            self.player.reset(active_cp)

        self.camera.reset(self.player.x)
        self.particles.clear()
        self.state = "PLAYING"
        self.audio.play_sfx("start")

        music_key = "music_practice" if self.practice_mode else "music_level"
        self.audio.play_music(music_key, loop=True, force_restart=(not keep_checkpoints))

    def _place_checkpoint(self) -> None:
        if not self.practice_mode or self.state != "PLAYING":
            return
        self.checkpoints.append(self.player.create_checkpoint())
        self.audio.play_sfx("checkpoint")

    def _compute_progress_percent(self) -> float:
        span = max(1.0, self.finish_x - self.player_start_x)
        pct = ((self.player.x - self.player_start_x) / span) * 100.0
        return max(0.0, min(100.0, pct))

    def _handle_player_death(self) -> None:
        self.player.is_dead = True
        self.state = "RESPAWNING"
        self.respawn_timer = 0.65

        cx, cy = self.player.center
        p_prim = tuple(self.config.data["colors"].get("player_primary", [125, 255, 50]))
        p_sec = tuple(self.config.data["colors"].get("player_secondary", [0, 235, 255]))
        self.particles.emit_death_explosion(cx, cy, p_prim, p_sec)
        self.camera.trigger_shake(duration=0.28, intensity=12.0)

        self.audio.play_sfx("death")
        if not self.practice_mode:
            self.audio.stop_music()

        pct = self._compute_progress_percent()
        self.config.update_high_score(pct, practice_mode=self.practice_mode)

    def _handle_level_victory(self) -> None:
        self.state = "VICTORY"
        self.last_run_new_best = self.config.update_high_score(100.0, practice_mode=self.practice_mode)
        self.audio.play_sfx("win")

    def _process_events(self) -> bool:
        jump_just_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == "MENU":
                    self._start_new_run(keep_checkpoints=False)
                elif self.state == "PLAYING":
                    jump_just_pressed = True
                    self.player.request_jump()
                elif self.state == "VICTORY":
                    self._start_new_run(keep_checkpoints=False)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.audio.toggle_mute()

                elif self.state == "MENU":
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w, pygame.K_RETURN):
                        self._start_new_run(keep_checkpoints=False)
                    elif event.key == pygame.K_TAB:
                        self.practice_mode = not self.practice_mode
                        self.config.set_value("gameplay", "practice_mode_default", self.practice_mode)
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

                elif self.state == "PLAYING":
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        jump_just_pressed = True
                        self.player.request_jump()
                    elif event.key == pygame.K_z and self.practice_mode:
                        self._place_checkpoint()
                    elif event.key == pygame.K_r:
                        self._start_new_run(keep_checkpoints=self.practice_mode)
                    elif event.key == pygame.K_p:
                        self.state = "PAUSED"
                        self.audio.pause_music()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        self.audio.play_music("music_home", loop=True)

                elif self.state == "PAUSED":
                    if event.key in (pygame.K_p, pygame.K_SPACE):
                        self.state = "PLAYING"
                        self.audio.unpause_music()
                    elif event.key == pygame.K_r:
                        self._start_new_run(keep_checkpoints=self.practice_mode)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        self.audio.play_music("music_home", loop=True)

                elif self.state == "VICTORY":
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self._start_new_run(keep_checkpoints=False)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        self.audio.play_music("music_home", loop=True)

        return jump_just_pressed

    def _is_jump_held(self) -> bool:
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        return bool(keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w] or mouse_pressed)

    def _update(self, dt: float, jump_just_pressed: bool) -> None:
        self.elapsed_time += dt

        if self.state == "MENU":
            self.camera.x += 120.0 * dt
            return

        if self.state == "PAUSED" or self.state == "VICTORY":
            self.particles.update(dt)
            return

        if self.state == "RESPAWNING":
            self.particles.update(dt)
            self.camera.update(dt, self.player.x, self.player.y, self.ground_y)
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self._start_new_run(keep_checkpoints=self.practice_mode)
            return

        # Active gameplay update
        jump_held = self._is_jump_held()
        prev_bottom = self.player.y + self.player.size

        jumped = self.player.update(dt, jump_held)
        if jumped:
            self.config.record_jump()
            self.audio.play_sfx("jump")
            p_sec = tuple(self.config.data["colors"].get("player_secondary", [0, 235, 255]))
            self.particles.emit_jump_dust(self.player.x + self.player.size * 0.4, self.player.y + self.player.size, p_sec)

        outcome = self.collision.resolve(
            player=self.player,
            objects=self.objects,
            prev_bottom=prev_bottom,
            jump_just_pressed=jump_just_pressed,
            jump_held=jump_held,
        )

        if outcome.activated_orb is not None:
            self.config.record_jump()
            self.audio.play_sfx("orb")
            orb_col = tuple(self.config.data["colors"].get("orb_yellow", [255, 225, 40]))
            self.particles.emit_orb_burst(
                outcome.activated_orb.x + outcome.activated_orb.width * 0.5,
                outcome.activated_orb.y + outcome.activated_orb.height * 0.5,
                orb_col,
            )

        if outcome.activated_pad is not None:
            self.audio.play_sfx("pad")
            pad_col = tuple(self.config.data["colors"].get("pad_yellow", [255, 200, 30]))
            self.particles.emit_orb_burst(
                outcome.activated_pad.x + outcome.activated_pad.width * 0.5,
                outcome.activated_pad.y + outcome.activated_pad.height * 0.8,
                pad_col,
            )

        if outcome.switched_mode is not None:
            self.audio.play_sfx("portal")

        if outcome.died:
            self._handle_player_death()
            return

        if outcome.finished:
            self._handle_level_victory()
            return

        # Automatic practice mode checkpoints
        if self.practice_mode and self.player.x >= self.next_auto_cp_x and self.player.on_ground:
            self._place_checkpoint()
            self.next_auto_cp_x = self.player.x + self.checkpoint_interval

        # Trail particles
        trail_col = tuple(self.config.data["colors"].get("player_primary", [125, 255, 50]))
        self.particles.emit_trail(self.player.x, self.player.y + self.player.size * 0.75, trail_col, dt)
        self.particles.update(dt)
        self.camera.update(dt, self.player.x, self.player.y, self.ground_y)

    def _render(self) -> None:
        self.renderer.draw_world(
            player=self.player,
            objects=self.objects,
            particles=self.particles,
            checkpoints=self.checkpoints if self.practice_mode else [],
            camera_x=self.camera.x,
            camera_y=self.camera.y,
            ground_y=self.ground_y,
            time_sec=self.elapsed_time,
        )

        high_score = float(self.config.get("progress", "high_score_percent", 0.0))
        practice_high_score = float(self.config.get("progress", "practice_high_score_percent", 0.0))
        total_attempts = int(self.config.get("progress", "total_attempts", 0))
        muted = bool(self.config.get("audio", "muted", False))

        if self.state == "MENU":
            self.renderer.draw_menu_overlay(
                high_score=high_score,
                practice_high_score=practice_high_score,
                total_attempts=total_attempts,
                practice_mode=self.practice_mode,
                muted=muted,
            )
        else:
            best = practice_high_score if self.practice_mode else high_score
            self.renderer.draw_hud(
                progress_pct=self._compute_progress_percent(),
                best_pct=best,
                attempt=self.attempt,
                practice_mode=self.practice_mode,
                muted=muted,
            )
            if self.state == "PAUSED":
                self.renderer.draw_pause_overlay()
            elif self.state == "VICTORY":
                self.renderer.draw_victory_overlay(self.attempt, self.last_run_new_best)

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = min(0.05, self.clock.tick(self.fps) / 1000.0)
            jump_just_pressed = self._process_events()
            self._update(dt, jump_just_pressed)
            self._render()

        self.config.save()
        pygame.quit()
