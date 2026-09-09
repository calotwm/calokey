"""JSON config persistence at ``%APPDATA%\\CaloKey\\config.json``.

Persists the selected output port name and the last root/scale selection. Paths
are overridable for tests; by default the config lives in the per-user
application-data directory so it survives executable relocation.
"""

import json
import os
from pathlib import Path

APP_DIR_NAME = "CaloKey"
CONFIG_FILE_NAME = "config.json"

DEFAULT_CONFIG = {
    "output_port": None,
    "root": 0,
    "scale_type": 0,
}

_MAX_INDEX = 11


def config_dir() -> Path:
    """Return the config directory (``%APPDATA%\\CaloKey`` on Windows)."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_DIR_NAME
    return Path.home() / ".config" / APP_DIR_NAME


def config_path() -> Path:
    """Return the path to ``config.json``."""
    return config_dir() / CONFIG_FILE_NAME


def load_config(path: Path | str | None = None) -> dict:
    """Load the config dict; returns defaults on missing or corrupt files."""
    target = Path(path) if path is not None else config_path()
    if not target.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with target.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_CONFIG)
    if not isinstance(data, dict):
        return dict(DEFAULT_CONFIG)
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(data)
    return cfg


def save_config(config: dict, path: Path | str | None = None) -> None:
    """Write ``config`` to disk, creating the directory as needed."""
    target = Path(path) if path is not None else config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)


def _index_or_default(value, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    if not 0 <= value <= _MAX_INDEX:
        return default
    return value


def load_settings(path: Path | str | None = None) -> tuple[int, int, str | None]:
    """Return ``(root, scale_type, output_port)`` with validation/fallback."""
    cfg = load_config(path)
    root = _index_or_default(cfg.get("root"), 0)
    scale_type = _index_or_default(cfg.get("scale_type"), 0)
    output_port = cfg.get("output_port")
    return root, scale_type, output_port
