import json
import logging
import subprocess
import typing as tp
from pathlib import Path

import click
from rich.logging import RichHandler
from trio.lowlevel import FdStream

from longmove import constants
from longmove.config_file import ConfigFile


class RsyncError(Exception):
    """Raised when a usable rsync binary can't be found. The message is
    user-facing: it describes why (missing, unsupported, or too old) and how to
    fix it."""


def _parse_rsync_version(output: str) -> tuple[int, ...]:
    """Parse the version tuple from `rsync -VV` JSON output.

    Only GNU rsync >= 3.2.0 emits JSON here; anything else (macOS's openrsync
    prints a plain-text banner, older rsync errors) fails to parse and raises
    RsyncError.
    """
    minimum = ".".join(map(str, constants.MINIMUM_RSYNC_VERSION))
    try:
        version = json.loads(output)["version"]
        return tuple(int(part) for part in version.split("."))
    except (json.JSONDecodeError, KeyError, AttributeError, ValueError) as e:
        raise RsyncError(
            f"Could not determine a supported rsync from `rsync -VV`. longmove "
            f"needs GNU rsync >= {minimum}. macOS's built-in openrsync is not "
            f"supported -- install GNU rsync, e.g. `brew install rsync`."
        ) from e


def get_rsync_command() -> str:
    """Return the rsync command to invoke, or raise RsyncError if the installed
    rsync is missing, unsupported, or too old.

    This is the single entry point for locating rsync -- every code path that
    shells out to rsync should get its command from here so the version check
    can't be bypassed.
    """
    minimum = ".".join(map(str, constants.MINIMUM_RSYNC_VERSION))
    try:
        result = subprocess.run(["rsync", "-VV"], capture_output=True, text=True)
    except FileNotFoundError as e:
        raise RsyncError(
            f"rsync was not found on your PATH. longmove needs GNU rsync "
            f">= {minimum} (on macOS: `brew install rsync`)."
        ) from e

    version = _parse_rsync_version(result.stdout)
    if version < constants.MINIMUM_RSYNC_VERSION:
        installed = ".".join(map(str, version))
        raise RsyncError(
            f"rsync {installed} is installed, but longmove needs "
            f">= {minimum}. Please upgrade."
        )
    return "rsync"


class LocalPath(click.ParamType):
    name = "local-path"

    def convert(
        self, value: tp.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> Path:
        p = Path(value).expanduser().absolute().resolve()
        if not p.exists():
            raise click.BadParameter(f"No such file or directory: {value}")
        return p


class LongmoveConfig(click.ParamType):
    name = "longmove-config"

    def convert(
        self, value: tp.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> Path:
        if isinstance(value, ConfigFile):
            return value

        try:
            return ConfigFile.from_file(Path(value))
        except IOError as e:
            from longmove.main import configure

            raise click.BadParameter(
                f"No config file found at {value}. To create one, run {configure.name}"
            ) from e


def configure_logging(verbosity: int) -> None:
    # Set up logging and add a rich handler.

    level = logging.INFO
    if verbosity:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click])],
    )


async def gen_lines(
    stream: FdStream,
    line_delimiters: frozenset[str] = frozenset(("\r", "\n")),
) -> tp.AsyncIterator[str]:
    """Consume and yield lines from stream"""
    accum: list[str] = []
    async for bytes_ in stream:
        for char in bytes_.decode():
            accum.append(char)
            if len(accum) > 1 and char in line_delimiters:
                yield "".join(accum)
                accum.clear()

    if accum:
        yield "".join(accum)
