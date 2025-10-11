from pathlib import Path

import pytest
import click
from click.testing import CliRunner

from longmove import main


def test_register(tmp_path: Path, basic_config: Path) -> None:
    runner = CliRunner()

    file = tmp_path / "test.txt"
    file.write_text("")
    args = f"register {file}"

    result = runner.invoke(main.cli, args.split())

    assert 0
