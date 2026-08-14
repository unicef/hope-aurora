# AuroraRole

A scoped role assignment: grants a Django group (`role`) to a user within an
organization, a project or a registration, optionally time-limited.

Module: `aurora.security.models` — `class AuroraRole(NaturalKeyModel, models.Model)`

## Relations

- **user** → `User` (FK, CASCADE)
- **organization** → `Organization` (FK, CASCADE, `related_name="members"`)
- **project** → `Project` (FK, CASCADE, `related_name="members"`)
- **registration** → `Registration` (FK, CASCADE, `related_name="members"`)
- **role** → `Group` (FK, CASCADE)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `user` | ForeignKey(User, CASCADE) | the assigned user | no | — |
| `organization` | ForeignKey(Organization, CASCADE) | scope: organization | yes | `None` |
| `project` | ForeignKey(Project, CASCADE) | scope: project | yes | `None` |
| `registration` | ForeignKey(Registration, CASCADE) | scope: registration | yes | `None` |
| `role` | ForeignKey(Group, CASCADE) | the role (Django group) | no | — |
| `valid_from` | DateField | role start date | no | now |
| `valid_until` | DateField | role end date (None = no expiry) | yes | `None` |

## Notes

- Scopes are hierarchical: when a registration is set, the project and
  organization are derived from it; when a project is set, the organization is
  derived from it.
- `(organization, project, registration, user, role)` is unique.
- Natural key: `(organization.slug | project.slug | registration.slug, user.username, role.name)`.
