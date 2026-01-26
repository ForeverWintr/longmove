import functools
import subprocess

import trio


async def rsync_copy(src: str, target: str):
    command = [
        "rsync",
        "--archive",
        # "--progress",
        "--info=progress2",
        "--compress",
        "--itemize-changes",
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

        while p.returncode is None:
            stderr = await p.stderr.receive_some()
            stdout = await p.stdout.receive_some()
            print("Stderr:")
            print(stderr)
            print("Stdout:")
            print(stdout)
        return stdout
