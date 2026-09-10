# Quick Start

This guide walks you through running Aurora locally and configuring your first
registration end to end: database, first form, and a working public
registration page.

## Prerequisites

- Docker with Docker Compose (v2)
- 4 GB of free RAM

## 1. Start the stack

Clone the repository and build the local image:

    git clone https://github.com/unicef/hope-aurora
    cd hope-aurora/docker
    make build

The image is tagged `unicef/hope-aurora:local`. Now start the stack from the
repository root (the compose file lives there):

    cd ..
    docker compose up

On first startup the container runs migrations, creates the default
Organization (`unicef`) and Project (`default-project`) and creates the
superuser from the `ADMIN_EMAIL` / `ADMIN_PASSWORD` environment variables
(`admin@example.com` / `password` by default).

!!! note

    `docker compose up` builds nothing: it requires the local image created
    by `make build` (or `unicef/hope-aurora:local` published on Docker Hub).

## 2. Login to the admin

Navigate to <http://localhost:8000/admin/> and login with:

- user: `admin@example.com`
- password: `password`

The admin URL is configurable via the `DJANGO_ADMIN_URL` setting.

## 3. Create a form

1. Open **Flex Forms** in the admin sidebar and click **ADD FLEX FORM**.
2. Give the form a **name**, e.g. `Health Survey`, and select the `UNICEF` project.
3. Save the form, then click the **form editor** button on the change page.
4. Add a couple of fields, e.g. **Text** fields named `family_name` and `given_name`, and a **Number** field `age`.
5. Save each field. Field names are auto-generated from the label and must match `^[a-z_0-9]*$`.

## 4. Create a registration

1. Open **Registrations** in the admin sidebar and click **ADD REGISTRATION**.
2. Set the **name** (the slug is derived from it), select the `UNICEF` project and the `Health Survey` form.
3. Set the **start** date to today and check **active**.
4. Save the registration.

## 5. Verify the result

Open the public registration page (URLs are locale-prefixed):

    http://localhost:8000/en-us/register/health-survey/

Fill the form and submit it. Then:

1. Back in the admin, open the registration and expand its **Records**.
2. Your submission is listed there with timestamp and collected fields.

You have now configured your first Aurora registration. To make registrations
unique per person, set the **Unique field path** (JMESPath, e.g.
`family_name`) and **Unique field error** on the registration, so duplicates
are rejected at the database level.

## Next steps

- [Configuration reference](../settings/) — all environment variables.
- [Run development version](dev/) — run the latest unreleased code.
- [HOPE integration](config/) — connect Aurora to HOPE.
- [REST API](../api/) — export collected data programmatically.
