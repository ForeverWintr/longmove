import functools
import subprocess
from pathlib import Path

import trio


async def rsync_copy(src: str, target: str):
    command = [
        "rsync",
        "--archive",
        # "--progress",
        "--info=progress2",
        "--compress",
        # "--itemize-changes",
        "--partial",
        src,
        target,
    ]

    print("Running Command")
    print(" ".join(command))

    runner = functools.partial(
        trio.run_process,
        command=command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    async with trio.open_nursery() as nursery:
        # https://trio.readthedocs.io/en/stable/reference-io.html#trio.Process
        p = await nursery.start(runner)

        stdout = []
        async for bytes_ in p.stdout:
            stdout.append(bytes_.decode())
            print("Stdout:")
            print(bytes_)

        await p.wait()
        stderr = await p.stderr.receive_some()
        print("Stderr:")
        print(stderr)
        Path(f"/tmp/longmove_{Path(src).name}.txt").write_text("".join(stdout))
        return "".join(stdout)
