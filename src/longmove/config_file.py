import typing as tp
import dataclasses
from dataclasses import field
from pathlib import Path
from importlib import metadata
import functools

import tomlkit
import platformdirs


@functools.cache
def get_default_config_path() -> Path:
    dist = metadata.distribution("longmove")
    base = platformdirs.site_config_path(appname=dist.name)
    return base / "longmove.toml"


@dataclasses.dataclass(frozen=True)
class ConfigFile:
    config_location: Path = field(default_factory=get_default_config_path)
    remote_name: str = ""
    remote_root: str = ""
    path_map: list[tuple[Path, Path]] = field(default_factory=list)

    @classmethod
    def from_toml(cls, toml: str, config_location: Path) -> tp.Self:
        d = dict(tomlkit.parse(toml))
        d["path_map"] = [(Path(a), Path(b)) for a, b in d["path_map"]]
        d["config_location"] = config_location
        return cls(**d)

    @classmethod
    def from_file(cls, f: Path) -> tp.Self:
        return cls.from_toml(f.read_text(), config_location=f)

    def to_toml(self) -> str:
        d = dataclasses.asdict(self)
        d.pop("config_location")
        d["path_map"] = [(str(a), str(b)) for a, b in self.path_map]
        return tomlkit.dumps(d)

    def to_file(self) -> None:
        self.config_location.write_text(self.to_toml())
