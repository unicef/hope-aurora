# REST API

Aurora exposes a read-only REST API under `/api/` to consume configuration
and collected data programmatically. The API is documented with
[drf-spectacular](https://drf-spectacular.readthedocs.io/): an interactive
Swagger UI is available at `/api/rest/swagger/` and ReDoc at
`/api/rest/redoc/`, both generated from the live schema at `/api/schema/`.

## Authentication

Three authentication methods are supported:

- **Session** — browser sessions, used by the admin UI.
- **Token** — `Authorization: Token <token>` header (Django REST framework tokens).
- **Basic** — username/password.

Example with a token:

    curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
         https://aurora.example.org/api/registration/

The API root itself returns `401 Unauthorized` for anonymous requests. All
list/detail endpoints require the relevant Django model permissions
(`view_registration`, `view_record`, ...).

## Endpoints

| Resource | URL | Description |
|----------|-----|-------------|
| Organizations | `/api/organization/` | List of organizations |
| Projects | `/api/project/` | List of projects (filter by `organization`) |
| Forms | `/api/form/` | FlexForm definitions |
| Form fields | `/api/field/` | Fields of every form |
| FormSets | `/api/formset/` | Repeater groups |
| Registrations | `/api/registration/` | Registration definitions |
| Registration records | `/api/registration/{pk}/records/` | Collected records of a registration |
| Registration metadata | `/api/registration/{pk}/metadata/` | Form schema consumed by the registration page |
| Registration version | `/api/registration/{pk}/version/` | Version info of a registration |
| Registration CSV | `/api/registration/{pk}/csv/` | CSV export of collected records |
| Records | `/api/record/` | All collected records |
| Validators | `/api/validator/` | Validation scripts |
| Option sets | `/api/optionset/` | Options exposed via the `core.optionset` view |
| FlatPages | `/api/flatpage/` | Flat pages |
| Templates | `/api/template/` | dbtemplates templates |
| Users | `/api/user/` | Users |
| Counters | `/api/counter/` | Daily record counters |
| System info | `/api/sys/` | Instance metadata (version, build, commit) |

## Pagination and filtering

List endpoints paginate and support the `modified_after` filter
(`?modified_after=2026-01-01`), useful for incremental syncs. The
`records` action of a registration accepts:

- `page` / `page_size` (capped at 100) for pagination,
- `start_date` to filter records by timestamp,
- `ser` to select the record payload: `fields` (default), `files`, `full`,
  `storage` or `encrypted`.

The `records` endpoint answers with `ETag` and `Cache-Control: private,
max-age=120` headers and supports conditional requests.

## Exporting records as CSV

    curl -H "Authorization: Token <token>" \
         "https://aurora.example.org/api/registration/42/csv/?include=*"

The CSV export supports field inclusion/exclusion and formatting options:

- `filters` / `exclude` — JMESPath-based record filters,
- `include` / `exclude` — fields to include or skip,
- `fmt.date_format`, `fmt.datetime_format`, `fmt.time_format` — date formatting,
- `csv.delimiter`, `csv.quotechar`, `csv.header` — CSV formatting.

Append `&download=1` to receive the file as an attachment, or `&preview=1`
to preview the headers without downloading. Exports are limited to **5000
records** per request: narrow your filters when the export is rejected.

## Errors

| Status | Meaning |
|--------|---------|
| 401 | Not authenticated (API root returns this for anonymous users) |
| 403 | Authenticated but missing model permissions |
| 404 | Unknown resource or record |
| 500 | Export failure (e.g. more than 5000 records) |

## Next steps

- [Adding REST endpoints](../develop/api/) — development guide.
- [Settings](../settings/) — authentication-related configuration.
