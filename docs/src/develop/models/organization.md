# Organization

An organization is the top-level tenant of the platform. Everything else
(projects, forms, registrations) hangs from it.

Module: `aurora.core.models` — `class Organization(AdminReverseMixin, NaturalKeyModel, MPTTModel)`

## Relations

- **parent** → self (MPTT tree, `children` reverse relation)
- **projects** ← `Project` (one-to-many, `related_name="projects"`)
- **members** ← `AuroraRole` (one-to-many, `related_name="members"`)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `name` | CharField(100) | display name, unique | no | — |
| `slug` | SlugField(100) | natural key, unique; auto-generated from the name on create | yes | `None` |
| `parent` | TreeForeignKey(self) | parent organization in the hierarchy | yes | `None` |

## Notes

- Natural key: `slug`.
- Identifies the HOPE Business Area in the [HOPE integration](../../run/config/).
