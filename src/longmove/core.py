import functools
import subprocess

import trio


async def rsync_copy(src: str, target: str):
    runner = functools.partial(
        trio.run_process,
        command=[
            "rsync",
            "--archive",
            # "--progress",
            "--info=progress2",
            "--compress",
            "--itemize-changes",
            "--partial",
            src,
            target,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    async with trio.open_nursery() as nursery:
        p = await nursery.start(runner)
        stderr = await p.stderr.receive_some()
        stdout = await p.stdout.receive_some()
        print(stderr)
        return stdout
