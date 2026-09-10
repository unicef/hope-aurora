# User

The custom user model (`AUTH_USER_MODEL = "security.User"`), based on Django's
`AbstractUser` with the UNICEF security mixin.

Module: `aurora.security.models` — `class User(SecurityMixin, AbstractUser)`

## Relations

- **profile** ← `UserProfile` (one-to-one, `related_name="profile"`)
- **aurorarole_set** ← `AuroraRole` (one-to-many, `related_name="user"` via the `user` FK)
- **record_set** ← `Record` (records where this user is the registrar)

## Fields

All standard `AbstractUser` fields apply (`username`, `email`, `password`,
`first_name`, `last_name`, `is_staff`, `is_superuser`, `is_active`,
`last_login`, `date_joined`, groups, permissions). Ordering is by `username`.

## Notes

- Swappable: referenced through `settings.AUTH_USER_MODEL`, not directly.
- The UNICEF `SecurityMixin` adds audit/security features used by the admin.
