import click

from longmove.config_file import ConfigFile, CONFIG_PATH


@click.group()
def main() -> None:
    print("hello")


@main.command(name="init")
@click.option("--server", help="The remote server url")
@click.option("--force", is_flag=True, help="Overwrite an existing config file")
def init(server: str | None, force: bool):
    if not force and CONFIG_PATH.exists():
        raise click.UsageError("")

    if server is None:
        server = click.prompt(text="Please enter a server URL")
    c = ConfigFile(remote_name=server)
    c.to_file(CONFIG_PATH)


if __name__ == "__main__":
    main()
