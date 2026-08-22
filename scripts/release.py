"""Create a Career OS release package.

Runs the full build (tests + bundle + NSIS installer) and zips the
resulting artifacts into releases/<version>/.
"""

import hashlib
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
RELEASES = ROOT / "releases"


def run(command: list[str], cwd: Path) -> None:
    print(f"[release] {' '.join(command)}  (cwd={cwd.name})")
    result = subprocess.run(command, cwd=str(cwd))
    if result.returncode != 0:
        print(f"[release] command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    version = "0.1.0"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target_dir = RELEASES / f"v{version}-{stamp}"
    target_dir.mkdir(parents=True, exist_ok=True)

    npm = "npm.cmd" if os.name == "nt" else "npm"
    # Full build including installer artifacts.
    run([npm, "run", "dist"], FRONTEND)

    dist_electron = FRONTEND / "dist_electron"
    installers = [
        path
        for path in list(dist_electron.glob("*.exe"))
        + list(dist_electron.glob("*.zip"))
        if not path.name.endswith(("unpacked", ":zone.identifier"))
    ]
    # Fallback: older builds may have written into frontend/dist.
    if not installers:
        dist_dir = FRONTEND / "dist"
        installers = [
            path
            for path in list(dist_dir.glob("*.exe"))
            if not path.name.endswith("unpacked")
        ]

    if not installers:
        print("[release] no installer artifacts found; nothing to package")
        return 1

    manifest_lines = [f"# Career OS v{version} — {stamp}", ""]
    for artifact in installers:
        destination = target_dir / artifact.name
        destination.write_bytes(artifact.read_bytes())
        checksum = sha256(destination)
        manifest_lines.append(
            f"- {artifact.name}  \n  sha256: `{checksum}`"
        )
        print(f"[release] packaged {artifact.name}")

    manifest_path = target_dir / "MANIFEST.md"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    archive_base = target_dir / f"career-os-v{version}"
    with zipfile.ZipFile(
        f"{archive_base}.zip", "w", zipfile.ZIP_DEFLATED
    ) as bundle:
        for file_path in target_dir.iterdir():
            if file_path.is_file():
                bundle.write(file_path, arcname=file_path.name)

    print(f"[release] complete -> {archive_base}.zip")
    return 0


if __name__ == "__main__":
    import os

    sys.exit(main())
