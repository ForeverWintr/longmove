import typing as tp
from pathlib import Path

import click

from longmove.config_file import ConfigFile


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
            )
