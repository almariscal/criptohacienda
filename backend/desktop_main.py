from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

# Ensure the project root is on sys.path when running as a standalone script/binary.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    port = int(os.environ.get("CRIPTOHACIENDA_DESKTOP_PORT", os.environ.get("PORT", "8000")))
    host = os.environ.get("CRIPTOHACIENDA_DESKTOP_HOST", "127.0.0.1")
    log_level = os.environ.get("CRIPTOHACIENDA_LOG_LEVEL", "info")
    uvicorn.run("backend.app.main:app", host=host, port=port, log_level=log_level, reload=False)


if __name__ == "__main__":
    main()
