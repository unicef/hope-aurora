# Build and use your Docker image

After you have cloned the repo, be sure to have a Redis and PostgreSQL server running on your machine:

    export ADMIN_EMAIL=admin@example.com
    export ADMIN_PASSWORD=password
    export DATABASE_URL=postgres://postgres:@127.0.0.1:5432/aurora
    export CACHE_DEFAULT=redis://127.0.0.1:6379/1?client_class=django_redis.client.DefaultClient

    cd docker

    make build run

The `make run` target also accepts a `DOCKER_IMAGE_NAME` environment variable
(e.g. `DOCKER_IMAGE_NAME=unicef/hope-aurora`) to select the image to run, and
defaults to the image built by `make build`.

!!! note

    `make run` does not set `DJANGO_ADMIN_URL`: the admin URL is randomly
    generated at startup unless you export it explicitly, e.g.
    `export DJANGO_ADMIN_URL=admin/`.

## Use the provided compose.yml

The compose file lives in the repository root:

    cd ..
    docker compose up

Navigate to <http://localhost:8000/admin/> and login using `admin@example.com` / `password`.

## Next steps

- [Quick Start](run/quickstart/) — end-to-end first registration.
- [Run development version](run/dev/) — run the latest unreleased code.
