from pathlib import Path

import pytest
import click
from click.testing import CliRunner

from longmove import main


def test_register(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()

    file = tmp_path / "test.txt"
    file.write_text("")
    args = f"register {file}"

    result = runner.invoke(main.main, args.split())

    assert 0
