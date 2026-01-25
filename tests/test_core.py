from pathlib import Path

import trio

from longmove import core


async def test_rsync_copy(trio_path: trio.Path, source_files: Path):
    tgt = trio_path / "target"
    source_files = trio.Path(source_files)

    assert not await tgt.exists()
    await core.rsync_copy(source_files, tgt)

    assert await tgt.exists()
    for f in await source_files.iterdir():
        tgt / f.name

        fs = await f.stat()
        fts = await f.stat()
        assert fs == fts
