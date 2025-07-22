import trio


async def rsync_copy(src: str, target: str):
    await trio.run_process(["rsync", "-a", src, target])
    asdf
