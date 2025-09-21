from pathlib import Path

import pytest
import click

from longmove import util


def test_localpath(tmp_path: Path) -> None:
    r = util.LocalPath()

    # Needs to be updated if supporting non macos.
    assert r("~/..") == Path("/Users")

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
