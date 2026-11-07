"""Tests voor de command-line uitvoer."""

import json
import subprocess
import sys


def test_output_dir_optie(tmp_path):
    """Doel / Input: Scenario1 en tijdelijke map / Verwacht: beide bestanden."""
    result = subprocess.run(
        [sys.executable, "run.py", "Scenario1", "--output-dir", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "plan.json").exists()
    assert (tmp_path / "statistics.txt").exists()
    assert isinstance(json.loads((tmp_path / "plan.json").read_text()), list)
