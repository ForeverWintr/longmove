import typing as tp
from pathlib import Path

import click


class LocalPath(click.ParamType):
    name = "local-path"

    def convert(
        self, value: tp.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> Path:
        p = Path(value).expanduser().absolute().resolve()
        if not p.exists():
            raise click.BadParameter(f"No such file or directory: {value}")
        return p
