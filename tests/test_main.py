import dataclasses
from pathlib import Path

import pytest
from click.testing import CliRunner

from longmove import core
from longmove import main
from longmove import util
from longmove.config_file import ConfigFile


def test_register(tmp_path: Path, basic_config: ConfigFile) -> None:
    runner = CliRunner()

    file = tmp_path / "test.txt"
    file.write_text("")
    args = f"register {file}"

    result = runner.invoke(main.cli, args.split())

    assert result.exit_code == 0


def test_configure(basic_config: ConfigFile) -> None:
    runner = CliRunner()
    result = runner.invoke(main.cli, ["configure"], input="name\nroot")
    assert result.exit_code == 0

    conf = ConfigFile.from_file(basic_config.config_location)
    assert conf.remote_name == "name"
    assert conf.remote_root == "root"

    # Make sure this works when config file doesn't exist.
    basic_config.config_location.unlink()

    result = runner.invoke(main.cli, ["configure"], input="name\nroot")
    assert result.exit_code == 0

    conf = ConfigFile.from_file(basic_config.config_location)
    assert conf.remote_name == "name"
    assert conf.remote_root == "root"


def test_send_surfaces_rsync_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An RsyncError from the transfer is reported as a clean CLI error, not a
    traceback."""

    async def boom(*args: object, **kwargs: object) -> None:
        raise util.RsyncError("descriptive msg")

    monkeypatch.setattr(core, "send_with_progress", boom)

    file = tmp_path / "test.txt"
    file.write_text("")

    runner = CliRunner()
    result = runner.invoke(main.cli, ["send", str(file), "dest"])

    assert result.exit_code != 0
    assert "descriptive msg" in result.output


@pytest.mark.skip("wip")
def test_offload(tmp_path: Path, source_files: Path, basic_config: ConfigFile) -> None:
    target = tmp_path / "target"
    target.mkdir()

    conf = dataclasses.replace(basic_config, remote_root=str(target))
    for f in source_files.iterdir():
        conf.register(f)

    runner = CliRunner()
    runner.invoke(main.cli, ["offload"])

    assert 0
