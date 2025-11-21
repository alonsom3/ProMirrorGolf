import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "ui": {
        "theme": "dark",
        "simple_mode": True,
    },
    "cameras": {
        "dtl_id": 0,
        "face_id": 1,
        "fps": 60,
        "resolution": [1920, 1080],
    },
    "shot_listener": {
        "host": "127.0.0.1",
        "port": 5556,
    },
    "storage": {
        "clips_dir": "data/clips",
        "database": "data/promirror.db",
        "buffer_seconds": 5,
    },
    "springbok_bridge": {
        "enabled": False,
        "listen_port": 922,
        "gspro_host": "127.0.0.1",
        "gspro_port": 921,
        "promirror_host": "127.0.0.1",
        "promirror_port": 5556,
    },
    "springbok_connector": {
        "path": "",
    },
}


class ConfigManager:
    """Load/save JSON config with defaults."""

    def __init__(self, path: str | Path = "config.json") -> None:
        self.path = Path(path)
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load config from file or create with defaults."""
        if not self.path.exists():
            self.data = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save()
            logger.debug("Config file created with defaults at %s", self.path)
            return

        try:
            with self.path.open("r", encoding="utf-8") as f:
                user_cfg = json.load(f)
        except json.JSONDecodeError as exc:
            logger.warning("Config parse error (%s). Using defaults.", exc)
            user_cfg = {}

        self.data = self._merge(DEFAULT_CONFIG, user_cfg)

    def _merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge override into base."""
        merged: Dict[str, Any] = json.loads(json.dumps(base))
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str, default: Any | None = None) -> Any:
        cursor: Any = self.data
        for part in key.split("."):
            if not isinstance(cursor, dict) or part not in cursor:
                return default
            cursor = cursor[part]
        return cursor

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        cursor = self.data
        parts = key.split(".")
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = value
        if persist:
            self.save()

