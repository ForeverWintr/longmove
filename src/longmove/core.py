import functools
import logging
import re
import subprocess
import typing as tp
from dataclasses import dataclass
from pathlib import Path

import trio
from rich import get_console
from rich import progress
from rich.console import Console
from rich.table import Column

from longmove import util

log = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ProgressData:
    file_path: str
    bytes_: int
    pct: int
    speed: str
    time_remaining: str
    transfer_num: int | None
    to_send: int | None
    total: int | None
    total_known: bool
    _LINE_PATTERN: tp.ClassVar[re.Pattern[str]] = re.compile(
        r"""
        ^\s*
        (?P<bytes>[\d,]+)\s+
        (?P<pct>\d+)%\s+
        (?P<speed>\S+)\s+
        (?P<time_remaining>\S+)
        (?:\s+
            \(\s*xfr\#(?P<transfer>\d+)\s*,\s*
            (?P<check_kind>to-chk|ir-chk)\s*=\s*
            (?P<to_send>\d+)\s*/\s*(?P<total>\d+)\s*\)
        )?
        \s*$
        """,
        re.VERBOSE,
    )

    @property
    def name(self) -> str:
        return Path(self.file_path).name

    @classmethod
    def from_rsync_line(cls, file_path: str, line: str) -> tp.Self:
        """Parse a single line of rsync output. Based on `man rsync` and this SO
        explanation: https://unix.stackexchange.com/a/261139/169944

        This section of the rsync manual, under the explanation of --progress, seems to
        describe the format:

            When the file transfer finishes, rsync replaces the progress line with a
            summary line that looks like this:

            1,238,099 100%  146.38kB/s    0:00:08  (xfr#5, to-chk=169/396)

            In this example, the file was 1,238,099 bytes long in total, the average
            rate of transfer for the whole file was 146.38 kilobytes per second over the
            8 seconds that it took to complete, it was the 5th transfer of a regular
            file during the current rsync session, and there are 169 more files for the
            receiver to check (to see if they are up-to-date or not) remaining out of
            the 396 total files in the file-list.

            In an incremental recursion scan, rsync won't know the total number of files
            in the file-list until it reaches the ends of the scan, but since it starts
            to transfer files during the scan, it will display a line with the text
            "ir-chk" (for incremental recursion check) instead of "to-chk" until the
            point that it knows the full size of the list, at which point it will switch
            to using "to-chk". Thus, seeing "ir-chk" lets you know that the total count
            of files in the file list is still going to increase (and each time it does,
            the count of files left to check will increase by the number of the files
            added to the list).
        """
        match = cls._LINE_PATTERN.match(line)
        if match is None:
            raise ValueError(f"Invalid rsync progress line: {line!r}")

        transfer = match.group("transfer")

        total_known = False
        to_send = None
        total = None
        transfer_num = None
        if transfer:
            # The transfer section is not printed for partial transfer reports. I.e. it
            # is only printed when a file transfer finishes.
            transfer_num = int(transfer)
            total_known = match.group("check_kind") == "to-chk"
            to_send = int(match.group("to_send"))
            total = int(match.group("total"))

        return cls(
            file_path=file_path,
            bytes_=int(match.group("bytes").replace(",", "")),
            pct=int(match.group("pct")),
            speed=match.group("speed"),
            time_remaining=match.group("time_remaining"),
            transfer_num=transfer_num,
            to_send=to_send,
            total=total,
            total_known=total_known,
        )

    @classmethod
    async def gen_from_rsync_process(
        cls, rsync_runner: trio.Process
    ) -> tp.AsyncIterator[tp.Self]:
        """Yield instances by parsing stdout from rsync_runner"""

        fp = ""
        async for line in util.gen_lines(rsync_runner.stdout):
            # Lines are either file_paths or progress lines. Progress lines are indented.
            if not line[0].isspace():
                fp = line.strip()
            else:
                yield cls.from_rsync_line(fp, line)


async def rsync_copy(
    src: str, target: str, rate_limit: str | None = None
) -> tp.AsyncIterator[ProgressData]:
    args = [
        "--archive",
        # Show per file progress and filename
        "--info=progress,NAME",
        "--compress",
        "--partial",
    ]
    if rate_limit:
        args.extend(
            [
                "--bwlimit",
                rate_limit,
            ]
        )
    command = [
        "rsync",
        *args,
        src,
        target,
    ]

    log.debug("Running Command")
    log.debug(" ".join(command))

    runner = functools.partial(
        trio.run_process,
        command=command,
        stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
    )
    async with trio.open_nursery() as nursery:
        # https://trio.readthedocs.io/en/stable/reference-io.html#trio.Process
        p = await nursery.start(runner)

        async for r in ProgressData.gen_from_rsync_process(p):
            yield r
        await p.wait()


def _build_progress(
    name_ratio: int = 2,
    bar_ratio: int = 3,
    console: Console | None = None,
) -> progress.Progress:
    # Give the bar bar_ratio/(name_ratio + bar_ratio) of the full terminal width
    # (so bar_ratio=3, name_ratio=2 -> 60%). The width is sized once from the
    # current terminal; the name column (ratio=1) absorbs the remaining space, so
    # it holds a fixed width regardless of filename length -- long names truncate
    # rather than pushing the bar around.
    # Fall back to rich's shared global console (not a fresh Console()) so the
    # progress Live display and the RichHandler logger write to the same console
    # -- that is what lets log output render above the bars instead of colliding.
    console = console or get_console()
    bar_fraction = bar_ratio / (name_ratio + bar_ratio)
    bar_width = int(console.width * bar_fraction)
    return progress.Progress(
        progress.TextColumn(
            "[progress.description]{task.description}",
            table_column=Column(
                no_wrap=True, overflow="ellipsis", ratio=1, min_width=6
            ),
        ),
        progress.BarColumn(bar_width=bar_width),
        progress.TaskProgressColumn(),
        progress.TimeRemainingColumn(),
        progress.MofNCompleteColumn(),
        console=console,
        expand=True,
    )


async def render_progress(
    ui: progress.Progress,
    data_stream: tp.AsyncIterator[ProgressData],
) -> None:
    """Drive two stacked progress bars from a stream of ProgressData: an overall
    file-count bar and, below it, a bar for the file currently transferring."""
    overall = ui.add_task("Total", start=False)
    current = ui.add_task("", start=False, visible=False)

    async for data in data_stream:
        log.debug(data)

        # Current-file bar: percent complete of the file transferring now. The
        # name column is fixed-width (see _build_progress), so long names are
        # truncated and the bar to its right stays put.
        ui.start_task(current)
        ui.update(
            current,
            description=data.name,
            total=100,
            completed=data.pct,
            visible=True,
        )

        # Overall bar: only the transfer-summary lines carry the file counts.
        if data.total is not None and data.to_send is not None:
            ui.start_task(overall)
            ui.update(
                overall,
                total=data.total,
                completed=data.total - data.to_send,
            )


async def send_with_progress(
    src: str, target: str, rate_limit: str | None = None
) -> None:
    """Send src to target"""

    with _build_progress() as ui:
        await render_progress(ui, rsync_copy(src, target, rate_limit=rate_limit))
