#!/usr/bin/env python3
"""Setup script for Busca que Entende.

Install all dependencies and download the LAYA model so the application
can run locally with a single command.

Usage:
    python scripts/setup.py
"""

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements.txt"
VENV_DIR = ROOT / ".venv"
MODEL_CHECKPOINT = os.getenv("LAYA_MODEL", "laya-multilingual")


def python_executable() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def pip_executable() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def check_python_version() -> None:
    version = sys.version_info
    if version < (3, 10):
        logger.error("Python 3.10+ is required. Found: %s.%s.%s", version.major, version.minor, version.micro)
        raise SystemExit(1)
    logger.info("Python version: %s.%s.%s", version.major, version.minor, version.micro)


def ensure_venv() -> None:
    if VENV_DIR.exists():
        logger.info("Virtual environment already exists at %s", VENV_DIR)
        return
    logger.info("Creating virtual environment at %s", VENV_DIR)
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)


def upgrade_pip(python: Path) -> None:
    logger.info("Upgrading pip/setuptools/wheel inside venv")
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)


def install_requirements(python: Path) -> None:
    if not REQUIREMENTS.exists():
        logger.error("requirements.txt not found at %s", REQUIREMENTS)
        raise SystemExit(1)
    logger.info("Installing dependencies from %s", REQUIREMENTS)
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)


def install_dev_dependencies(python: Path) -> None:
    logger.info("Installing dev dependencies")
    subprocess.run(
        [str(python), "-m", "pip", "install", "pytest>=7.0.0", "pytest-cov>=4.0.0"],
        check=True,
    )


def download_laya_model() -> None:
    try:
        import laya  # noqa: F401
    except ImportError:
        logger.warning("LAYA package is not installed. Install it with: pip install laya")
        logger.warning("Skipping model download.")
        return
    try:
        import laya as laya_pkg

        if hasattr(laya_pkg, "download"):
            logger.info("Downloading LAYA model: %s", MODEL_CHECKPOINT)
            laya_pkg.download(MODEL_CHECKPOINT)
        else:
            logger.info("LAYA package found, but download helper not available.")
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("LAYA model download failed: %s", exc)


def smoke_test() -> None:
    python = python_executable()
    logger.info("Running smoke test...")
    cmd = [str(python), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "4111"]
    proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        import time

        time.sleep(5)
        import urllib.request

        with urllib.request.urlopen("http://127.0.0.1:4111/healthz", timeout=10) as resp:
            assert resp.status == 200
            data = __import__("json").load(resp)
            assert data.get("ok") is True
            assert data.get("engine") == "laya"
            logger.info("Smoke test passed. LAYA engine reported as loaded.")
    except Exception as exc:
        logger.warning("Smoke test failed: %s", exc)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> int:
    logger.info("Python: %s", sys.executable)
    logger.info("Platform: %s", platform.platform())
    check_python_version()
    ensure_venv()
    python = python_executable()
    upgrade_pip(python)
    install_requirements(python)
    install_dev_dependencies(python)
    download_laya_model()
    smoke_test()
    logger.info("Setup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
