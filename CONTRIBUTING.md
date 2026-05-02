# Contributing

Thanks for considering a contribution!

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install pre-commit
.venv/bin/pre-commit install
```

## Running tests

```sh
.venv/bin/python -m unittest discover -vs tests
```

Tests also run in CI on Python 3.10–3.14. New hooks should ship with tests
in `tests/`.

## Linting and formatting

`pre-commit` runs `black`, `isort`, `flake8`, and `pyupgrade`. Either let
the installed hook handle it on commit, or run it manually:

```sh
.venv/bin/pre-commit run --all-files
```

pre-commit.ci also runs these hooks on every PR.

## Adding a new hook

A new hook needs:

- An entry in `.pre-commit-hooks.yaml`
- An entry point in `setup.py`
- A usage example in `README.md`
- Tests in `tests/`
