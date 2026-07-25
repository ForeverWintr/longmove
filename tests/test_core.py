import functools
import subprocess
from pathlib import Path

import pytest
import trio

from longmove import core


async def test_rsync_copy(trio_path: trio.Path, source_files: Path):
    tgt = trio_path / "target"
    source_files = trio.Path(source_files)

    assert not await tgt.exists()
    async for out in core.rsync_copy(str(source_files), str(tgt), rate_limit="100"):
        assert isinstance(out, core.ProgressData)

    assert await tgt.exists()
    for f in await source_files.iterdir():
        tgt / f.name

        fs = await f.stat()
        fts = await f.stat()
        assert fs == fts


def test_progress_from_rsync_line():
    P = core.ProgressData

    fn = "test"

    line_to_expected = {
        "100  25%    0.00kB/s    0:00:00": P(
            file_path=fn,
            bytes_=100,
            pct=25,
            speed="0.00kB/s",
            time_remaining="0:00:00",
            transfer_num=None,
            to_send=None,
            total=None,
            total_known=False,
        ),
        "100  25%    0.00kB/s    0:00:00 (xfr#1, to-chk=3/5)": P(
            file_path=fn,
            bytes_=100,
            pct=25,
            speed="0.00kB/s",
            time_remaining="0:00:00",
            transfer_num=1,
            to_send=3,
            total=5,
            total_known=True,
        ),
        "200  50%   97.66kB/s    0:00:00 (xfr#2, to-chk=2/5)": P(
            file_path=fn,
            bytes_=200,
            pct=50,
            speed="97.66kB/s",
            time_remaining="0:00:00",
            transfer_num=2,
            to_send=2,
            total=5,
            total_known=True,
        ),
        "3,356,292,837  99%  148.37MB/s    0:00:21 (xfr#28130, ir-chk=1292/33839)": P(
            file_path=fn,
            bytes_=3_356_292_837,
            pct=99,
            speed="148.37MB/s",
            time_remaining="0:00:21",
            transfer_num=28130,
            to_send=1292,
            total=33839,
            total_known=False,
        ),
    }

    for line, expected in line_to_expected.items():
        result = P.from_rsync_line(fn, line)
        assert result == expected


def test_send_with_progress(
    tmp_path: Path,
    source_files: Path,
    capsys: pytest.CaptureFixture,
):
    out_dir = tmp_path / "output"
    trio.run(core.send_with_progress, str(source_files), f"{out_dir}")
    out, err = capsys.readouterr()
    assert not err


async def test_progress_data_gen_from_rsync_process() -> None:
    test_output = Path(__file__).parent / "progress_output.txt"

    runner = functools.partial(
        trio.run_process,
        command=["cat", str(test_output)],
        stdout=subprocess.PIPE,
    )
    result = []
    async with trio.open_nursery() as n:
        p = await n.start(runner)
        async for r in core.ProgressData.gen_from_rsync_process(p):
            result.append(r)

    assert result[0] == core.ProgressData(
        file_path="longmove/progress_output.txt",
        bytes_=10,
        pct=100,
        speed="0.00kB/s",
        time_remaining="0:00:00",
        transfer_num=None,
        to_send=None,
        total=None,
        total_known=False,
    )
    assert result[-1] == core.ProgressData(
        file_path="longmove/tests/__pycache__/test_util.cpython-313-pytest-8.4.1.pyc",
        bytes_=7305,
        pct=100,
        speed="12.85kB/s",
        time_remaining="0:00:00",
        transfer_num=1905,
        to_send=0,
        total=2567,
        total_known=True,
    )


async def test_render_progress() -> None:
    test_output = Path(__file__).parent / "progress_output.txt"

    runner = functools.partial(
        trio.run_process,
        command=["cat", str(test_output)],
        stdout=subprocess.PIPE,
    )

    ui = core._build_progress()
    with ui:
        async with trio.open_nursery() as n:
            p = await n.start(runner)
            await core.render_progress(ui, core.ProgressData.gen_from_rsync_process(p))

    overall, current = ui.tasks

    # The saved output ends at file 1905 with to-chk=0/2567, so the overall bar
    # finishes at all 2567 files and the current-file bar at 100% of the last file.
    assert overall.total == 2567
    assert overall.completed == 2567
    assert current.total == 100
    assert current.completed == 100
    assert current.description == (
        "longmove/tests/__pycache__/test_util.cpython-313-pytest-8.4.1.pyc"
    )
