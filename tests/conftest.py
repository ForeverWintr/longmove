import contextlib

import pytest


@contextlib.contextmanager
def catch_argparse_error(replacement=AssertionError):
    try:
        yield
    except SystemExit as e:
        raise AssertionError(e) from e
