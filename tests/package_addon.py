"""Compatibility entry point; use python release.py for new builds."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "release.py"), run_name="__main__")
