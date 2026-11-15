import json
import os
from copy import deepcopy
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "window": {"title": "Geometry Dash - Stereo Madness", "width": 1280, "height": 720, "fps": 60},
    "physics": {
        "gravity": 2750.0,
        "ship_gravity": 1350.0,
        "ship_thrust": -1650.0,
        "ship_max_vy": 750.0,
        "jump_velocity": -860.0,
        "orb_velocity": -880.0,
        "pad_velocity": -1180.0,
        "terminal_velocity": 1350.0,
        "player_speed": 490.0,
        "rotation_speed": 415.0,
    },
    "gameplay": {
        "tile_size": 48,
        "ground_height": 144,
        "player_start_x": 260,
        "checkpoint_interval_px": 1800,
        "practice_mode_default": False,
    },
    "audio": {
        "master_volume": 0.85,
        "music_volume": 0.65,
        "sfx_volume": 0.85,
        "muted": False,
        "files": {},
    },
    "colors": {},
    "progress": {
        "high_score_percent": 0.0,
        "practice_high_score_percent": 0.0,
        "total_attempts": 0,
        "total_jumps": 0,
        "level_completed": False,
    },
}


class ConfigManager:
    """Loads, validates, updates, and persists config/config.json."""

    def __init__(self, config_path: str) -> None:
        self.config_path = config_path
        self.data: Dict[str, Any] = deepcopy(DEFAULT_CONFIG)
        self.load()

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            self.save()
            return self.data

        try:
            with open(self.config_path, "r", encoding="utf-8") as fp:
                loaded = json.load(fp)
            self._deep_merge(self.data, loaded)
        except (json.JSONDecodeError, OSError):
            self.save()
        return self.data

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as fp:
            json.dump(self.data, fp, indent=4)

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self.data.get(section, {}).get(key, default)

    def set_value(self, section: str, key: str, value: Any, auto_save: bool = True) -> None:
        if section not in self.data or not isinstance(self.data[section], dict):
            self.data[section] = {}
        self.data[section][key] = value
        if auto_save:
            self.save()

    def record_attempt(self) -> int:
        attempts = int(self.get("progress", "total_attempts", 0)) + 1
        self.set_value("progress", "total_attempts", attempts, auto_save=True)
        return attempts

    def record_jump(self) -> int:
        jumps = int(self.get("progress", "total_jumps", 0)) + 1
        self.set_value("progress", "total_jumps", jumps, auto_save=False)
        return jumps

    def update_high_score(self, percent: float, practice_mode: bool = False) -> bool:
        clamped = round(max(0.0, min(100.0, percent)), 2)
        key = "practice_high_score_percent" if practice_mode else "high_score_percent"
        current_best = float(self.get("progress", key, 0.0))
        is_new_best = clamped > current_best
        if is_new_best:
            self.set_value("progress", key, clamped, auto_save=False)
        if not practice_mode and clamped >= 100.0:
            self.set_value("progress", "level_completed", True, auto_save=False)
        self.save()
        return is_new_best
