# Setup HOPE integration

Aurora can synchronize content with the HOPE platform through the admin sync
engine. The following steps configure the integration between an Aurora
instance and HOPE.

## 1. Add `aurora_token` to the user

Each HOPE user that must exchange data with Aurora needs a token. The token is
stored on the user profile (field `ad_uuid`), it is set automatically on
login.

## 2. Add `aurora_server` in the Constance Config

Open the **Constance Config** page in the admin and set the URL of the
production Aurora server. The server and token values used by the sync engine
are configured through the Constance keys and the `ADMIN_SYNC_*` environment
variables (see the [Settings reference](../settings/) for
`ADMIN_SYNC_REMOTE_SERVER`, `ADMIN_SYNC_REMOTE_ADMIN_URL` and
`ADMIN_SYNC_LOCAL_ADMIN_URL`).

## 3. Fetch data from Aurora

Use the admin sync actions in the admin to pull content (forms, validators,
option sets, templates) from the remote Aurora server into the local instance.

## 4. Associate Organizations to Business Areas

Map each Aurora **Organization** to the corresponding HOPE **Business Area**
so that collected registrations can be routed to the correct workspace.

## 5. Associate Projects to Programmes

Map each Aurora **Project** to the corresponding HOPE **Programme**. A
registration always belongs to one project, which in turn belongs to one
organization.

## Next steps

- [Quick Start](quickstart.md) — run Aurora locally.
- [Settings](../settings/) — full configuration reference.
