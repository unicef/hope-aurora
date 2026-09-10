# CLI Reference

Aurora ships a small set of custom management commands, implemented with
[djclick](https://pypi.org/project/djclick/). They are invoked with
`manage.py <command>` (or `django-admin <command>` when the settings module is
resolved).

## upgrade

One-shot provisioning command: runs migrations, creates the default
Organization/Project, collects static files and creates the initial
superuser. The Docker image runs `upgrade --no-input` on startup.

    manage.py upgrade [OPTIONS]

| Option | Type | Default | Purpose |
|--------|------|---------|---------|
| `-v, --verbosity` | int | `1` | Log verbosity |
| `--prompt / --no-input` | flag | `--no-input` | Prompt for parameters instead of reading them from the environment |
| `-e, --admin-email` | str | env `ADMIN_EMAIL` | Email of the superuser to create (skipped if a superuser already exists) |
| `-p, --admin-password` | str | env `ADMIN_PASSWORD` | Password of the superuser to create |
| `--migrate / --no-migrate` | flag | `--migrate` | Run database migrations |
| `--static / --no-static` | flag | `--static` | Collect static assets |
| `--organization` | str | env `DEFAULT_ORGANIZATION` | Name of the default Organization; also creates a "Default Project" in it |

The command is safe to run concurrently on multiple instances: migrations and
provisioning are serialized through a Redis lock (key from `MIGRATION_LOCK_KEY`).

## demo

Populates a development instance with a demo form, validators and registrations:

    manage.py demo

It creates a `FlexForm` with fields and validators and a `Registration`
pointing to it, so you can immediately exercise the registration flow. No
options are accepted.

## Standard Django commands

All regular Django commands are available (`migrate`, `collectstatic`,
`runserver`, `createsuperuser`, ...). `aurora.config.settings` is the default
settings module; the `run` and `dev` entrypoints of the Docker image rely on
`upgrade` and `runserver` respectively.

## Next steps

- [Development Guide](index.md) — structure and conventions.
- [Settings](../settings/) — environment variables consumed by the commands.
