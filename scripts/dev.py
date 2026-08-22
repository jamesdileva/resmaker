"""Start the Career OS development environment.

Launches the FastAPI backend (uvicorn on :8000) and, unless --backend-only
is passed, the Vite + Electron frontend via `npm run electron:dev`.
Ctrl+C shuts both down.
"""

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def backend_command() -> list[str]:
    venv_python = BACKEND / ".venv" / "Scripts" / "python.exe"
    python = str(venv_python) if venv_python.exists() else sys.executable
    return [
        python,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]


def frontend_command() -> list[str]:
    npm = "npm.cmd" if os.name == "nt" else "npm"
    return [npm, "run", "electron:dev"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Skip the frontend and run just the API server",
    )
    args = parser.parse_args()

    processes: list[subprocess.Popen] = []

    def shutdown(*_args) -> None:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()

    processes.append(
        subprocess.Popen(backend_command(), cwd=str(BACKEND))
    )
    print(f"[dev] backend  -> http://127.0.0.1:8000 (pid {processes[-1].pid})")

    if not args.backend_only:
        env = {**os.environ, "CAREER_OS_DEV": "1"}
        processes.append(
            subprocess.Popen(
                frontend_command(),
                cwd=str(FRONTEND),
                env=env,
            )
        )
        print(f"[dev] frontend -> http://127.0.0.1:5173 (pid {processes[-1].pid})")

    try:
        signal.signal(signal.SIGINT, lambda *_: shutdown())
    except ValueError:
        pass

    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
