"""Build the Career OS desktop application.

Steps:
  1. Frontend: typecheck + production Vite bundle (dist/).
  2. Electron packaging via electron-builder.
     Default: unpacked directory (fast smoke test of packaging).
     --installer: full NSIS installer for the current platform.

The backend ships as source; it runs from `backend/.venv` via uvicorn
(see scripts/dev.py) and is not bundled into the Electron binary.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def run(command: list[str], cwd: Path) -> None:
    print(f"[build] {' '.join(command)}  (cwd={cwd.name})")
    result = subprocess.run(command, cwd=str(cwd))
    if result.returncode != 0:
        print(f"[build] command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def npm_command(script: str) -> list[str]:
    npm = "npm.cmd" if os.name == "nt" else "npm"
    return [npm, "run", script]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip the frontend vitest suite before building",
    )
    parser.add_argument(
        "--installer",
        action="store_true",
        help="Produce a full NSIS installer instead of an unpacked directory",
    )
    args = parser.parse_args()

    node_modules = FRONTEND / "node_modules"
    if not node_modules.exists():
        run(["npm.cmd" if os.name == "nt" else "npm", "install"], FRONTEND)

    if not args.skip_tests:
        run(npm_command("test"), FRONTEND)

    # Typecheck + production bundle into dist/.
    run(npm_command("build"), FRONTEND)

    builder = ["npx.cmd" if os.name == "nt" else "npx"]
    if args.installer:
        run(builder + ["electron-builder"], FRONTEND)
    else:
        run(builder + ["electron-builder", "--dir"], FRONTEND)

    print("[build] done. Output in frontend/dist_electron/ (or dist/ per config).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
