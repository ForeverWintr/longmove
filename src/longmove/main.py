import click

from longmove.config_file import ConfigFile


@click.group()
def main() -> None:
    print("hello")


@main.command(name="init")
@click.option(
    "--server", prompt="Please enter a server URL", help="The remote server url"
)
def init(server: str):
    ConfigFile(remote_name=server)
    pass
