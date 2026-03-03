from pathlib import Path

import pytest

from longmove import constants
from longmove.config_file import ConfigFile


@pytest.fixture
def basic_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ConfigFile:
    """Creates a basic config file, and both returns it and sets it in ENV so that cli
    methods use it automatically."""

    fp = tmp_path / "longmove.toml"
    c = ConfigFile(config_location=fp)
    c.to_file()
    monkeypatch.setenv(constants.CONFIG_ENV_VAR, fp)
    return c


@pytest.fixture
def source_files(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    root.mkdir()
    for char in "abcd":
        f = root / f"{char}.txt"
        f.write_text(char * 100)
    return root


@pytest.fixture
def source_files_big(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    root.mkdir()
    for char in "abcd":
        f = root / f"{char}.txt"
        f.write_text(char * 1_000_000)
    return root
