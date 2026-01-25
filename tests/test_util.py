from pathlib import Path

import click
import pytest

from longmove import util
from longmove.config_file import ConfigFile


def test_localpath(tmp_path: Path) -> None:
    r = util.LocalPath()

    home = r("~/..").name.casefold()
    assert "user" in home or "home" in home

    # convert existing path is noop.
    assert tmp_path == r(tmp_path)
    assert tmp_path == r(str(tmp_path))

    with pytest.raises(click.BadParameter):
        r(tmp_path / "doesntexist")

    # relative paths not allowed
    with pytest.MonkeyPatch.context() as m:
        m.chdir(tmp_path)
        p = r(".")
        assert p == tmp_path


def test_configfile(tmp_path: Path) -> None:
    lc = util.LongmoveConfig()

    with pytest.raises(click.BadParameter):
        lc(tmp_path / "doesntexist")

    exists = tmp_path / "config.toml"
    cf = ConfigFile(exists)
    cf.to_file()

    assert lc(exists) == cf
