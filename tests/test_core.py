from pathlib import Path

import trio

from longmove import core


async def test_rsync_copy(trio_path: trio.Path, source_files: Path):
    tgt = trio_path / "target"
    source_files = trio.Path(source_files)

    assert not await tgt.exists()
    async for out in core.rsync_copy(str(source_files), str(tgt)):
        assert isinstance(out, core.ProgressData)

    assert await tgt.exists()
    for f in await source_files.iterdir():
        tgt / f.name

        fs = await f.stat()
        fts = await f.stat()
        assert fs == fts


def test_progress_from_rsync_line():
    from longmove.core import ProgressData as P

    line_to_expected = {
        "100  25%    0.00kB/s    0:00:00": P(
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
        result = P.from_rsync_line(line)
        assert result == expected


# @pytest.mark.skip
def test_sent_with_progress(tmp_path: Path, source_files_big: Path):
    out_dir = tmp_path / "output"
    trio.run(core.send_with_progress, str(source_files_big), f"{out_dir}")
    assert 0
