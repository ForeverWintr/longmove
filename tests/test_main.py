from pathlib import Path

import pytest
import click
from click.testing import CliRunner

from longmove import main
from longmove.config_file import ConfigFile


def test_register(tmp_path: Path, basic_config: Path) -> None:
    runner = CliRunner()

    file = tmp_path / "test.txt"
    file.write_text("")
    args = f"register {file}"

    result = runner.invoke(main.cli, args.split())

    assert result.exit_code == 0


def test_cli(basic_config: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main.cli, ["configure"], input="name\nroot")
    assert result.exit_code == 0

    conf = ConfigFile.from_file(basic_config)
    assert conf.remote_name == "name"
    assert conf.remote_root == "root"

    # Make sure this works when config file doesn't exist.
    basic_config.unlink()

    result = runner.invoke(main.cli, ["configure"], input="name\nroot")
    assert result.exit_code == 0

    conf = ConfigFile.from_file(basic_config)
    assert conf.remote_name == "name"
    assert conf.remote_root == "root"
