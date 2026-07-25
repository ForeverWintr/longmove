import types
from pathlib import Path

import click
import pytest

from longmove import util
from longmove.config_file import ConfigFile

# A representative slice of GNU rsync's `rsync -VV` JSON output.
GNU_RSYNC_VV = """{
  "program": "rsync",
  "version": "3.4.4",
  "protocol": "32.0",
  "capabilities": {"file_bits": 64, "ACLs": true}
}"""

# openrsync (macOS) prints a plain-text banner from `-VV`, not JSON.
OPENRSYNC_VV = "openrsync: protocol version 29\nrsync version 2.6.9 compatible\n"


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


def test_parse_rsync_version() -> None:
    assert util._parse_rsync_version(GNU_RSYNC_VV) == (3, 4, 4)
    assert util._parse_rsync_version('{"version": "3.2.0"}') == (3, 2, 0)

    # Anything that isn't GNU rsync JSON is unparseable.
    for bad in (OPENRSYNC_VV, "", "not json", '{"protocol": "32.0"}'):
        with pytest.raises(util.RsyncError):
            util._parse_rsync_version(bad)


def test_get_rsync_command(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(stdout: str):
        return lambda *a, **k: types.SimpleNamespace(stdout=stdout)

    # A supported version returns the command to invoke.
    monkeypatch.setattr(util.subprocess, "run", fake_run(GNU_RSYNC_VV))
    assert util.get_rsync_command() == "rsync"

    # Parseable but below the minimum -> descriptive "too old" error.
    monkeypatch.setattr(util.subprocess, "run", fake_run('{"version": "3.1.0"}'))
    with pytest.raises(util.RsyncError, match="Please upgrade"):
        util.get_rsync_command()

    # openrsync's banner is unparseable.
    monkeypatch.setattr(util.subprocess, "run", fake_run(OPENRSYNC_VV))
    with pytest.raises(util.RsyncError):
        util.get_rsync_command()

    # rsync not installed at all -> distinct "not found" error.
    def raise_fnf(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr(util.subprocess, "run", raise_fnf)
    with pytest.raises(util.RsyncError, match="not found"):
        util.get_rsync_command()
