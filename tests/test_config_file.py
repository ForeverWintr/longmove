from pathlib import Path

from longmove import config_file


def test_to_from_toml(tmp_path: Path) -> None:
    c = config_file.ConfigFile(
        remote_name="remote.server",
        path_map=(
            (Path("/tmp/foo"), Path("/server/offload/foo")),
            (Path("/tmp/foo2"), Path("/server/offload/foo2")),
        ),
    )

    y = c.to_toml()
    assert y == (
        'remote_name = "remote.server"\n'
        'path_map = [["/tmp/foo", "/server/offload/foo"], ["/tmp/foo2", '
        '"/server/offload/foo2"]]\n'
    )

    out = tmp_path / "config.toml"
    c.to_file(out)

    c2 = config_file.ConfigFile.from_file(out)
    assert c == c2
