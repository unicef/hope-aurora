# Contributing


Install [uv](https://docs.astral.sh/uv/)


    git clone https://github.com/unicef/hope-aurora
    uv venv .venv --python 3.12
    source .venv/bin/activate
    uv sync --all-extras
    pre-commit install --hook-type pre-commit --hook-type pre-push


## Run tests

    pytests tests

!!! note

    Support services (Postgres / Valkey) are automatically started byt the test suite
    using the compose file (`compose.yml`) in the `tests/` directory.

    If you want to keep the support stack up and running, just run this command in the project root.

        docker compose -f tests/compose.yml -p aurora-test-stack up




## Run Selenium tests (ONLY)

    pytests tests -m selenium



## Run local server


    ./manage.py runserver


!!! note

    To facililate developing you can use:

        export AUTHENTICATION_BACKENDS="aurora.security.backends.AnyUserAuthBackend"

    It works only if `DEBUG=True`



## Docker compose

Alternatively you can use provided docker compose for development

    docker compose up

Alternatively you can use provided docker compose for development

    docker compose up
