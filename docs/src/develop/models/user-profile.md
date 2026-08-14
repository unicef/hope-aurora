# UserProfile

Per-user extra profile data attached one-to-one to the `User`.

Module: `aurora.security.models` — `class UserProfile(models.Model)`

## Relations

- **user** → `User` (OneToOneField, CASCADE, `related_name="profile"`)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `user` | OneToOneField(User, CASCADE) | the profile owner | no | — |
| `ad_uuid` | CharField(64) | Active Directory / Azure object id, unique (set on login) | yes | `None` |
| `custom_fields` | JSONField | free-form profile fields | yes | `{}` |
| `job_title` | CharField(255) | user's job title | yes | `` |

## Notes

- `ad_uuid` is populated from the identity provider during social
  authentication and is used by the [HOPE integration](../../run/config/)
  (`aurora_token`).
