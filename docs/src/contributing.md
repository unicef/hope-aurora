# Contributing

## Install the development environment

Install [uv](https://docs.astral.sh/uv/) and clone the repository:

    git clone https://github.com/unicef/hope-aurora
    uv venv .venv --python 3.14
    source .venv/bin/activate
    uv sync --all-extras
    pre-commit install --hook-type pre-commit --hook-type pre-push

## Run tests

    pytest tests

## Run Selenium tests (ONLY)

    pytest tests -m selenium

## Run all tests with Selenium

    pytest tests --selenium

!!! note

    You can disable Selenium headless mode (show the browser activity on the screen) using the `--show-browser` flag.

## Run the local server

    ./manage.py runserver

!!! note

    To facilitate development you can use:

        export AUTHENTICATION_BACKENDS="aurora.security.backends.AnyUserAuthBackend"

    It works only if `DEBUG=True`.

## Docker compose

Alternatively you can use the provided docker compose for development:

    docker compose up

See [Docker](docker.md) for details about building the local image first.

## Next steps

- [Development Guide](develop/) — codebase structure, models, CLI and REST API conventions.
