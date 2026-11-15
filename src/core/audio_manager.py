import os
from typing import Dict, Optional
import pygame
from src.utils.config_manager import ConfigManager


class AudioManager:
    """Handles background music tracks and sound effects cleanly."""

    def __init__(self, base_dir: str, config: ConfigManager) -> None:
        self.base_dir = base_dir
        self.config = config
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.current_music_key: Optional[str] = None
        self.audio_available = False

        self._init_mixer()
        self._load_sfx()
        self.apply_volumes()

    def _init_mixer(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            self.audio_available = True
        except pygame.error:
            self.audio_available = False

    def _resolve_path(self, rel_path: str) -> str:
        return os.path.join(self.base_dir, rel_path)

    def _load_sfx(self) -> None:
        if not self.audio_available:
            return
        files = self.config.get("audio", "files", {})
        sfx_map = {
            "start": files.get("sfx_start", ""),
            "death": files.get("sfx_death", ""),
            "jump": files.get("sfx_jump", ""),
            "orb": files.get("sfx_orb", ""),
            "pad": files.get("sfx_pad", ""),
            "portal": files.get("sfx_portal", ""),
            "checkpoint": files.get("sfx_checkpoint", ""),
            "win": files.get("sfx_win", ""),
        }
        for name, rel_path in sfx_map.items():
            full_path = self._resolve_path(rel_path)
            if rel_path and os.path.exists(full_path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(full_path)
                except pygame.error:
                    pass

    def apply_volumes(self) -> None:
        if not self.audio_available:
            return
        muted = bool(self.config.get("audio", "muted", False))
        master = 0.0 if muted else float(self.config.get("audio", "master_volume", 0.85))
        music_vol = float(self.config.get("audio", "music_volume", 0.65)) * master
        sfx_vol = float(self.config.get("audio", "sfx_volume", 0.85)) * master

        pygame.mixer.music.set_volume(max(0.0, min(1.0, music_vol)))
        for sound in self.sounds.values():
            sound.set_volume(max(0.0, min(1.0, sfx_vol)))

    def play_sfx(self, name: str) -> None:
        if not self.audio_available:
            return
        if bool(self.config.get("audio", "muted", False)):
            return
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    def play_music(self, track_key: str, loop: bool = True, force_restart: bool = False) -> None:
        if not self.audio_available:
            return
        if self.current_music_key == track_key and not force_restart and pygame.mixer.music.get_busy():
            return

        files = self.config.get("audio", "files", {})
        rel_path = files.get(track_key, "")
        full_path = self._resolve_path(rel_path)

        if not rel_path or not os.path.exists(full_path):
            return

        try:
            pygame.mixer.music.load(full_path)
            self.apply_volumes()
            pygame.mixer.music.play(-1 if loop else 0)
            self.current_music_key = track_key
        except pygame.error:
            pass

    def stop_music(self) -> None:
        if self.audio_available:
            pygame.mixer.music.stop()
            self.current_music_key = None

    def pause_music(self) -> None:
        if self.audio_available:
            pygame.mixer.music.pause()

    def unpause_music(self) -> None:
        if self.audio_available:
            pygame.mixer.music.unpause()

    def toggle_mute(self) -> bool:
        new_muted = not bool(self.config.get("audio", "muted", False))
        self.config.set_value("audio", "muted", new_muted, auto_save=True)
        self.apply_volumes()
        return new_muted
