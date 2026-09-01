import os
import shutil
import subprocess
from pathlib import Path

import PyInstaller.__main__


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BINARY_DIR = PROJECT_ROOT / "desktop/src-tauri/binaries"
WORK_DIR = PROJECT_ROOT / "build/pyinstaller"


def main() -> None:
    target_triple = subprocess.check_output(
        ["rustc", "--print", "host-tuple"],
        text=True,
    ).strip()
    executable_suffix = ".exe" if "windows" in target_triple else ""
    binary_name = f"inventory-vault-backend-{target_triple}{executable_suffix}"

    BINARY_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    PyInstaller.__main__.run(
        [
            str(PROJECT_ROOT / "app/desktop_backend.py"),
            "--name",
            binary_name,
            "--onefile",
            "--noconfirm",
            "--paths",
            str(PROJECT_ROOT),
            "--distpath",
            str(BINARY_DIR),
            "--workpath",
            str(WORK_DIR / "work"),
            "--specpath",
            str(WORK_DIR),
            "--add-data",
            f"{PROJECT_ROOT / 'alembic.ini'}{os.pathsep}.",
            "--add-data",
            f"{PROJECT_ROOT / 'app/db/migrations'}{os.pathsep}app/db/migrations",
        ]
    )

    generated_spec = WORK_DIR / f"{binary_name}.spec"
    if generated_spec.exists():
        generated_spec.unlink()
    shutil.rmtree(WORK_DIR / "work", ignore_errors=True)

    print(f"Built desktop backend: {BINARY_DIR / binary_name}")


if __name__ == "__main__":
    main()
