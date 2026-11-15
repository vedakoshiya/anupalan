#!/usr/bin/env python3
"""Unified Server Launcher for Anupalan Compliance Engine.

Starts the FastAPI production ASGI server via Uvicorn with auto-reload,
ensuring Windows UTF-8 stdout, database persistence, and clean diagnostics.
"""

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import uvicorn
except ImportError:
    print("[!] Uvicorn is not installed in the active environment.")
    print("    Install it via: pip install uvicorn")
    sys.exit(1)


def main():
    print("=" * 80)
    print("           ANUPALAN (અનુપાલન / अनुपालन) COMPLIANCE ENGINE")
    print("=" * 80)
    print("[*] Starting FastAPI ASGI server on http://127.0.0.1:8000 ...")
    print("    - Interactive Web UI:     http://127.0.0.1:8000/")
    print("    - Swagger API Docs:       http://127.0.0.1:8000/docs")
    print("    - Prometheus Metrics:     http://127.0.0.1:8000/metrics")
    print("    - Liveness Health Check:  http://127.0.0.1:8000/v1/health")
    print("-" * 80)
    print("[*] Press Ctrl+C to terminate.")
    print("=" * 80 + "\n")

    uvicorn.run(
        "services.api.src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
