import pathlib

import pytest
import trio


@pytest.fixture
async def trio_path(tmp_path: pathlib.Path) -> trio.Path:
    return trio.Path(tmp_path)


async def test_rsync_copy(tmp_path: trio.Path):
    assert 0
