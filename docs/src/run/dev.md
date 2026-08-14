# Run Development Version

!!! warning

    This is an unsecure development configuration. **DO NOT USE IN PRODUCTION.**

To locally run the latest unreleased version of Aurora with Docker:

    docker run \
        --rm \
        -p 8000:8000 \
        -e ADMIN_EMAIL="${ADMIN_EMAIL}" \
        -e ADMIN_PASSWORD="${ADMIN_PASSWORD}" \
        -e ALLOWED_HOSTS="*" \
        -e CACHE_DEFAULT="redis://[REDIS_SERVER]:[PORT]/0" \
        -e CSRF_COOKIE_SECURE=False \
        -e CSRF_TRUSTED_ORIGINS=http://localhost \
        -e DATABASE_URL="${DATABASE_URL}" \
        -e DEBUG="1" \
        -e DJANGO_ADMIN_URL=admin/ \
        -e DJANGO_SETTINGS_MODULE=aurora.config.settings \
        -e LOG_LEVEL="DEBUG" \
        -e SECRET_KEY="${SECRET_KEY}" \
        -e SENTRY_DSN="${SENTRY_DSN}" \
        unicef/hope-aurora:develop

Requires PostgreSQL (`DATABASE_URL`) and Redis (`CACHE_DEFAULT`) reachable from
the container. See the [Settings](../settings/) page for every available
environment variable.

## Next steps

- [Quick Start](quickstart.md) — configure your first registration.
- [Docker](../docker.md) — build the local image and use compose.
