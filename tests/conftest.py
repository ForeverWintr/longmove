import contextlib
from pathlib import Path

import pytest

from longmove.config_file import ConfigFile
from longmove import constants


@pytest.fixture
def basic_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Creates a basic config file, and both returns it and sets it in ENV so that cli
    methods use it automatically."""

    fp = tmp_path / "longmove.toml"
    c = ConfigFile(config_location=fp)
    c.to_file()
    monkeypatch.setenv(constants.CONFIG_ENV_VAR, fp)
    return fp
