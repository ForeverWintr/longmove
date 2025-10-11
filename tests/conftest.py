import contextlib
from pathlib import Path

import pytest

from longmove.config_file import ConfigFile
from longmove import constants


@pytest.fixture
def basic_config(tmp_path: Path) -> Path:
    fp = tmp_path / "longmove.toml"
    c = ConfigFile()
    c.to_file(fp)
    return fp


@pytest.fixture
def basic_config_env(monkeypatch: pytest.MonkeyPatch, basic_config: Path) -> None:
    monkeypatch.setenv(constants.CONFIG_ENV_VAR, basic_config)
