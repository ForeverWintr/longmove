# longmove
Tool for moving and retrieving files to and from remote destinations.

![GithubActions Badge](https://github.com/ForeverWintr/longmove/actions/workflows/tests.yml/badge.svg)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![codecov](https://codecov.io/gh/ForeverWintr/longmove/branch/main/graph/badge.svg?token=COLZBZZ2SR)](https://codecov.io/gh/ForeverWintr/longmove)

## Development Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management. See the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for how to install uv.

### Set up the development environment

```bash
# Create a virtual environment and install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Run the tool
uv run lm

# Run tests
uv run pytest
```
>>>>>>> @{-1}
