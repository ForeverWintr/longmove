import pathlib

import pytest
import trio

from longmove import core


@pytest.fixture
async def trio_path(tmp_path: pathlib.Path) -> trio.Path:
    return trio.Path(tmp_path)


@pytest.fixture
async def source_files(trio_path: trio.Path) -> trio.Path:
    root = trio_path / "root"
    await root.mkdir()
    for char in "abcd":
        f = root / char
        await f.write_text(char * 100)
    return root


async def test_rsync_copy(trio_path: trio.Path, source_files: trio_path):
    tgt = trio_path / "target"
    await tgt.mkdir()

    await core.rsync_copy(source_files, tgt)
    assert 0
