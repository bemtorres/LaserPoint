from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from . import APP_ID, APP_NAME

DEFAULTS: dict[str, Any] = {
    "hotkey": "ctrl+alt+l",
    "mode": "hold",
    "color": "#ff3b30",
    "size": 26,
    "shadow": 70,
    "opacity": 100,
    "shape": "dot",
    "fade_ms": 350,
    "speed_boost": 120,
    "trail": True,
    "tray_icon": "dot",
    "autostart": False,
    "show_widget": True,
    "bar_pos": None,
    "started_before": False,
}


def config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home())
        root = Path(base)
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        root = Path(base)
    path = root / APP_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return config_dir() / "config.json"


class Config:
    def __init__(self) -> None:
        self.path = config_path()
        self.data: dict[str, Any] = copy.deepcopy(DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(raw, dict):
            for key, value in raw.items():
                if key in DEFAULTS:
                    self.data[key] = value

    def save(self) -> None:
        payload = json.dumps(self.data, indent=2, ensure_ascii=False)
        try:
            fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp, self.path)
        except OSError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, DEFAULTS.get(key, default))

    def update(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            if key in DEFAULTS:
                self.data[key] = value

    def reset(self) -> None:
        self.data = copy.deepcopy(DEFAULTS)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value


def app_title() -> str:
    return APP_NAME
