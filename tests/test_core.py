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

    assert not await tgt.exists()
    await core.rsync_copy(source_files, tgt)

    assert await tgt.exists()
    for f in await source_files.iterdir():
        ft = tgt / f.name

        fs = await f.stat()
        fts = await f.stat()
        assert fs == fts
