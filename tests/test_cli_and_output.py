"""Tests voor de command-line uitvoer."""

import json
import subprocess
import sys
from pathlib import Path


def test_output_dir_optie(tmp_path):
    """Doel / Input: Scenario1 en tijdelijke map / Verwacht: beide bestanden."""
    root = Path(__file__).parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "run.py"), "Scenario1", "--output-dir", str(tmp_path)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "plan.json").exists()
    assert (tmp_path / "statistics.txt").exists()
    assert isinstance(json.loads((tmp_path / "plan.json").read_text()), list)
