import dataclasses
from pathlib import Path

import tomlkit


@dataclasses.dataclass
class ConfigFile:
    remote_name: str
    path_map: tuple[tuple[Path, Path]]

    def to_yaml(self) -> str:
        d = dataclasses.asdict(self)
        d["path_map"] = tuple((str(a), str(b)) for a, b in self.path_map)
        return tomlkit.dumps(d)
