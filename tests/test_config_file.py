from pathlib import Path

from longmove import config_file


def test_to_from_toml(tmp_path: Path) -> None:
    out = tmp_path / "config.toml"
    c = config_file.ConfigFile(
        remote_name="remote.server",
        remote_root="/offload",
        path_map=(
            (Path("/tmp/foo"), Path("/server/offload/foo")),
            (Path("/tmp/foo2"), Path("/server/offload/foo2")),
        ),
        config_location=out,
    )

    c.to_file()

    c2 = config_file.ConfigFile.from_file(out)
    assert c == c2
