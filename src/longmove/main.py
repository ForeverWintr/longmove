from pathlib import Path

import click
import trio

from longmove import constants
from longmove import core
from longmove import util
from longmove.config_file import ConfigFile
from longmove.config_file import get_default_config_path


@click.group()
@click.option("-v", "--verbose", count=True, help="display debug output")
def cli(verbose: int) -> None:
    util.configure_logging(verbose)


config_option = click.option(
    "--config-file",
    type=util.LongmoveConfig(),
    default=get_default_config_path(),
    help="Path to a config file to use",
    show_default=True,
    envvar=constants.CONFIG_ENV_VAR,
)


@cli.command()
@click.option(
    "--server",
    help="The remote server url",
)
@click.option(
    "--remote-root",
    help="The root directory on the server in which to store offloaded files",
)
@click.option(
    "--config-file",
    type=Path,
    default=get_default_config_path(),
    show_default=True,
    help="Path to a config file to use",
    envvar=constants.CONFIG_ENV_VAR,
)
def configure(
    server: str | None,
    remote_root: str | None,
    config_file: Path,
) -> None:
    """Create or update a longmove config file"""
    try:
        cf = ConfigFile.from_file(config_file)
    except FileNotFoundError:
        cf = ConfigFile()

    if server is None:
        server = click.prompt(
            text="Please enter a server URL",
            show_default=True,
            default=cf.remote_name,
        )

    if remote_root is None:
        remote_root = click.prompt(
            text="Please specify the server directory to use",
            show_default=True,
            default=cf.remote_root,
        )
    c = ConfigFile(
        config_location=config_file,
        remote_name=server,
        remote_root=remote_root,
    )
    c.to_file()
    click.echo(f"Wrote config file at {config_file}")


@cli.command()
@click.argument("path", type=util.LocalPath())
@config_option
def register(path: Path, config_file: ConfigFile) -> None:
    """Register a file to be offloaded."""
    remote = config_file.register(path)
    config_file.to_file()

    click.echo(f"Registered {path.name} to:")
    click.echo(f"remote:{remote}")


@cli.command()
@config_option
def offload(config_file: ConfigFile) -> None:
    """Transfer tracked files to remote"""
    raise NotImplementedError("WIP")


@cli.command()
@click.argument(
    "source",
    type=click.Path(exists=True, readable=True, resolve_path=True, path_type=Path),
)
@click.argument("dest")
@click.option(
    "--rate-limit", help="Limit transfer rate. Passed to rsync's bwlimit argument"
)
def send(source: Path, dest: str, rate_limit: str | None) -> None:
    """Send the specified local file SOURCE to the specified destination DEST. DEST is a
    remote destination, e.g: username@server:/path/to/dir/
    """
    trio.run(core.send_with_progress, str(source), dest, rate_limit)


if __name__ == "__main__":
    cli()
