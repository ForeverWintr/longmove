# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`longmove` is a CLI tool (`lm`) for moving/retrieving files to and from remote
destinations. It wraps `rsync`, parsing its `--progress` output to drive a
`rich` progress bar. Async I/O is built on `trio`.

## Commands

Dependency management is via [uv](https://github.com/astral-sh/uv).

```bash
uv sync                          # create .venv and install deps + dev group
uv run lm                        # run the CLI
uv run lm send SOURCE DEST       # send a local file/dir to remote (user@host:/path/)
uv run pytest                    # run the test suite
uv run pytest tests/test_core.py::test_rsync_copy   # run a single test
uv run ruff check                # lint
uv run ruff format               # format
```

Pre-commit runs ruff (import-sort, lint, format) — see `.pre-commit-config.yaml`.

## Architecture

The dependency flow is `main.py` (CLI) → `core.py` (transfer engine) →
`util.py` / `config_file.py` (support).

- **`main.py`** — the `click` command group `cli`. Subcommands: `configure`
  (create/update config), `register` (track a file for offload), `offload`
  (WIP — raises `NotImplementedError`), and `send` (the working transfer path,
  which calls `trio.run(core.send_with_progress, ...)`).

- **`core.py`** — the rsync engine, fully async under trio.
  - `ProgressData` is a frozen dataclass whose `_LINE_PATTERN` regex parses one
    line of rsync progress output (bytes/pct/speed/ETA and the optional
    `xfr#…, to-chk=…/…` transfer summary). `to-chk` vs `ir-chk` distinguishes a
    known total from an in-progress incremental scan (`total_known`).
  - `rsync_copy` builds the rsync command, launches it via `trio.run_process`
    inside a nursery, and is an **async generator** yielding `ProgressData`.
  - `send_with_progress` consumes that generator to update the `rich` progress bar.

- **`util.py`** — `click.ParamType` subclasses (`LocalPath`, `LongmoveConfig`)
  that validate/convert CLI arguments; `configure_logging` (rich handler,
  `-v` bumps to DEBUG); and `gen_lines`, an async generator that splits a trio
  byte stream into lines on `\r`/`\n` (rsync uses `\r` for progress updates).

- **`config_file.py`** — `ConfigFile`, a frozen dataclass serialized to TOML via
  `tomlkit`. Default location comes from `platformdirs.site_config_path`.
  `path_map` records (local path, remote-relative path) pairs. The
  `LONGMOVE_CONFIG` env var (see `constants.py`) overrides the config path.

## Testing notes

- `pytest-trio` runs with `trio_mode = true` (see `pyproject.toml`), so async
  test functions and fixtures need no decorator.
- `tests/conftest.py` provides fixtures: `basic_config` (writes a config and
  points `LONGMOVE_CONFIG` at it), `source_files` / `source_files_big` (real
  files for exercising rsync), and `trio_path`.
- `test_rsync_copy` shells out to a real `rsync`, so it must be installed.
- CLI commands are tested with `click.testing.CliRunner`.

## Wing IDE

This repo is a Wing project (`longmove.wpr`). See `.claude/CLAUDE.md` and
`.claude/*.md` for the MCP-tool workflow (analysis/testing/review) and the
version-control invariants that apply when working here — notably: the user
initiates commits and reviews, and new tracked files are created with
`create_tracked_file` rather than `Write`.
