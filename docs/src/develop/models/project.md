# Project

A project groups registrations and forms under an organization. It mirrors
the HOPE Programme in the [HOPE integration](../../run/config/).

Module: `aurora.core.models` — `class Project(AdminReverseMixin, NaturalKeyModel, MPTTModel)`

## Relations

- **organization** → `Organization` (FK, `related_name="projects"`)
- **parent** → self (MPTT tree, `children` reverse relation)
- **registrations** ← `Registration` (one-to-many, `related_name="registrations"`)
- **members** ← `AuroraRole` (one-to-many, `related_name="members"`)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `name` | CharField(100) | display name, unique | no | — |
| `slug` | SlugField(100) | auto-generated from the name on create | yes | `None` |
| `organization` | ForeignKey(Organization, CASCADE) | owning organization | no | — |
| `parent` | TreeForeignKey(self) | parent project in the hierarchy | yes | `None` |

## Notes

- Natural key: `(slug, organization.slug)`; `(slug, organization)` is unique.
- The `upgrade` command creates `unicef` / `default-project` when missing.
