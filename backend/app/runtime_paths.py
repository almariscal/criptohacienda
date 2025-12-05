from __future__ import annotations

import os
import sys
from pathlib import Path


def _default_runtime_root() -> Path:
    """
    Resolve the directory where persistent data should live.

    - When packaged as a desktop binary (PyInstaller), use the executable folder.
    - During development (module execution), fall back to the project root.
    """
    if getattr(sys, "frozen", False):  # type: ignore[attr-defined]
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def get_runtime_root() -> Path:
    """
    Base path for runtime artifacts. Can be overridden with CRIPTOHACIENDA_BASE_PATH.
    """
    override = os.environ.get("CRIPTOHACIENDA_BASE_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return _default_runtime_root()


def get_data_dir() -> Path:
    """
    Location used to persist session data and cache files.
    Defaults to <runtime_root>/data unless CRIPTOHACIENDA_DATA_DIR is set.
    """
    override = os.environ.get("CRIPTOHACIENDA_DATA_DIR")
    base = Path(override).expanduser() if override else get_runtime_root() / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base
