import typing as tp

import dataclasses
from pathlib import Path

import tomlkit

CONFIG_PATH = Path("~/.longmove.toml").expanduser()


@dataclasses.dataclass(frozen=True)
class ConfigFile:
    remote_name: str = ""
    remote_root: str = ""
    path_map: tuple[tuple[Path, Path]] = ()

    @classmethod
    def from_toml(cls, toml: str) -> tp.Self:
        d = dict(tomlkit.parse(toml))
        d["path_map"] = tuple((Path(a), Path(b)) for a, b in d["path_map"])
        return cls(**d)

    @classmethod
    def from_file(cls, f: Path) -> tp.Self:
        return cls.from_toml(f.read_text())

    def to_toml(self) -> str:
        d = dataclasses.asdict(self)
        d["path_map"] = tuple((str(a), str(b)) for a, b in self.path_map)
        return tomlkit.dumps(d)

    def to_file(self, f: Path) -> None:
        return f.write_text(self.to_toml())
