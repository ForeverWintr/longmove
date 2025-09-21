import typing as tp

from pathlib import Path

import click


from longmove.config_file import ConfigFile, CONFIG_PATH



@click.group()
def main() -> None:
    print("hello")


@main.command(name="init", help='Initialize a new longmove config file')
@click.option(
    "--server",
    help="The remote server url",
)
@click.option(
    "--remote-root",
    help="The root directory on the server in which to store offloaded files",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite an existing config file",
)
def init(server: str | None, remote_root: str | None, force: bool):
    if not force and CONFIG_PATH.exists():
        raise click.BadOptionUsage(
            "--force", f"{CONFIG_PATH} already exists. Pass --force to overwrite."
        )

    if server is None:
        server = click.prompt(text="Please enter a server URL")

    if remote_root is None:
        remote_root = click.prompt(
            text="Please specify the absolute path to a directory to use for storage on the server"
        )
    c = ConfigFile(remote_name=server, remote_root=remote_root)
    c.to_file(CONFIG_PATH)
    click.echo(f"Wrote config file at {CONFIG_PATH}")

@main.command('register', help='Register a file to be offloaded.')
@click.argument('file', type=click.File)


if __name__ == "__main__":
    main()
