from pathlib import Path

import pytest
import click

from longmove import main
from tests.conftest import catch_argparse_error


@catch_argparse_error()
def test_register(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    file = tmp_path / "test.txt"
    args = f"register {file}"

    main.main(args.split())

    assert 0
