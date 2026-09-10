# Codebase Structure

## Repository layout

    .
    ├── compose.yml            # development compose stack (root of the repo)
    ├── docker/                # Docker image: Makefile, Dockerfile, entrypoint
    ├── docs/                  # documentation sources (this site)
    ├── src/aurora/            # application package (src layout)
    │   ├── api/               # REST API: router, viewsets, serializers
    │   ├── config/            # settings, environment configuration, fragments
    │   ├── core/              # form builder: FlexForm, fields, validators, option sets
    │   ├── counters/          # daily record counters
    │   ├── i18n/              # multilingual messages and translation engine
    │   ├── registration/      # public registration flow and collected records
    │   ├── security/          # users, roles, authentication backends
    │   ├── web/               # public views, templates, middleware
    │   └── management/        # upgrade and demo management commands
    └── tests/                 # pytest suite

## Key concepts

- **Form** — a `FlexForm` with ordered `FlexFormField` instances; fields are
  rendered from a `field_type` strategy registered in `aurora/core/registry.py`.
- **Registration** — a published form instance: binds a `FlexForm` to a
  `Project` and defines the public URL, active period, locales and validation.
- **Record** — one submission of a registration; the collected fields are
  stored as JSON, with optional RSA encryption.
- **Validator** — JavaScript validation scripts (DukPY) attached to forms,
  fields, formsets, modules or scripts.

## Testing strategy

- **Unit/integration tests** — `pytest tests` (plain pytest; the suite
  includes Django integration tests with a PostgreSQL/Redis-backed stack).
- **Selenium tests** — run with `pytest tests -m selenium`, or add
  `--selenium` to run everything; `--show-browser` disables headless mode.
- Selenium tests are excluded from the default run because they need a
  browser and a full stack.

## Git workflow and CI/CD

- Branching: feature branches merged into `develop`; releases are tagged and
  merged to the release branch.
- CI runs on GitHub Actions: `lint.yml` (ruff/mypy), `test.yml` (pytest),
  `docs.yml` (ProperDocs build + GitHub Pages deploy), `dockerize.yml` (image
  build) and `security.yml` (dependency audit).
- The Docker image is built with `docker/Makefile` and versioned through
  hatch-vcs; the container entrypoint runs `upgrade --no-input` at startup.

## Next steps

- [Models](models/) — reference of every Django model.
- [REST API](api/) — endpoint conventions.
- [CLI Reference](cli.md) — management commands.
