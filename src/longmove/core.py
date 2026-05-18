import functools
import logging
import re
import subprocess
import typing as tp
from dataclasses import dataclass

import trio
from rich import progress

from longmove import util

log = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ProgressData:
    bytes_: int
    pct: float
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

    @classmethod
    def from_rsync_line(cls, line: str) -> tp.Self:
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
            # The transfer section is not always printed.
            transfer_num = int(transfer)
            total_known = match.group("check_kind") == "to-chk"
            to_send = int(match.group("to_send"))
            total = int(match.group("total"))

        return cls(
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
    ) -> tp.Iterator[tp.Self]:
        """Yield instances by parsing stdout from rsync_runner"""
        async for line in util.gen_lines(rsync_runner.stdout):
            raise NotImplementedError("WIP")
        yield 1


async def rsync_copy(
    src: str, target: str, rate_limit: str | None = None
) -> tp.Iterator[ProgressData]:
    args = [
        "--archive",
        "--info=progress2",
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

        accum = []
        async for r in ProgressData.gen_from_rsync_process(p):
            yield r
        async for bytes_ in p.stdout:
            for char in bytes_.decode():
                accum.append(char)
                if char == "\r" and len(accum) > 1:
                    line = "".join(accum)
                    log.debug(line)
                    accum.clear()
                    yield ProgressData.from_rsync_line(line)

        await p.wait()


async def send_with_progress(
    src: str, target: str, rate_limit: str | None = None
) -> None:
    """Send src to target"""

    with progress.Progress(
        *progress.Progress.get_default_columns(),
        progress.MofNCompleteColumn(),
    ) as ui:
        bar = ui.add_task("Sending...", start=False)

        async for data in rsync_copy(src, target, rate_limit=rate_limit):
            log.debug(data)
            ui.start_task(bar)
            completed = None
            if data.total is not None and data.to_send is not None:
                completed = data.total - data.to_send
            ui.update(
                bar,
                total=data.total,
                completed=completed,
                description=data.speed,
                total_known=data.total_known,
            )
