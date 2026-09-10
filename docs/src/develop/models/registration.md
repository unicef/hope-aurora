# Registration

A published form: binds a `FlexForm` to a `Project`, defines the public URL,
the active period, locales, uniqueness rules and optional data encryption.

Module: `aurora.registration.models` — `class Registration(NaturalKeyModel, I18NModel, models.Model)`

## Relations

- **project** → `Project` (FK, CASCADE, `related_name="registrations"`)
- **flex_form** → `FlexForm` (FK, PROTECT)
- **welcome_page** → `django.contrib.flatpages.FlatPage` (FK, SET_NULL)
- **validator** → `Validator` (FK, SET_NULL; target `module`)
- **scripts** → `Validator` (M2M, `related_name="script_for"`; target `script`)
- **records** ← `Record` (one-to-many)
- **counters** ← `Counter` (one-to-many, `related_name="counters"`)
- **members** ← `AuroraRole` (one-to-many, `related_name="members"`)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `name` | CharField(255) | registration name, unique per project | no | — |
| `title` | CharField(500) | display title | yes | `None` |
| `slug` | SlugField(500) | public URL slug, unique; auto-generated from the name | yes | `None` |
| `project` | ForeignKey(Project, CASCADE) | owning project | no | — |
| `flex_form` | ForeignKey(FlexForm, PROTECT) | the form to render | no | — |
| `start` | DateField | collection start date | no | now |
| `end` | DateField | collection end date (None = never) | yes | `None` |
| `active` | BooleanField | whether the registration is open | no | `False` |
| `archived` | BooleanField | archived registrations cannot be reopened | no | `False` |
| `locale` | CharField(10) | default locale | no | `LANGUAGE_CODE` |
| `dry_run` | BooleanField | simulate submission without storing records | no | `False` |
| `handler` | StrategyField | storage strategy (`SaveToDB` by default) | yes | `None` |
| `show_in_homepage` | BooleanField | show on the public home page | no | `False` |
| `welcome_page` | ForeignKey(FlatPage, SET_NULL) | page shown after registration | yes | `None` |
| `locales` | ChoiceArrayField | additional available locales | yes | `None` |
| `intro` | TextField | intro text (i18n-enabled) | yes | `` |
| `footer` | TextField | footer text (i18n-enabled) | yes | `` |
| `client_validation` | BooleanField | enable client-side validation | no | `False` |
| `validator` | ForeignKey(Validator, SET_NULL) | module-level validator | yes | `None` |
| `scripts` | ManyToManyField(Validator) | scripts loaded on the registration page | no | — |
| `unique_field_path` | CharField(1000) | JMESPath expression of the unique field | yes | `None` |
| `unique_field_error` | CharField(255) | message shown for duplicate unique field | yes | `None` |
| `public_key` | TextField | RSA public key for encrypted collections | yes | `None` |
| `encrypt_data` | BooleanField | encrypt stored records with the public key | no | `False` |
| `advanced` | JSONField | layout options (`smart` attrs, wizard...) | yes | `{}` |
| `protected` | BooleanField | limit access to users with `registration.register` | no | `False` |
| `is_pwa_enabled` | BooleanField | allow the page to be installed as a PWA | no | `False` |
| `export_allowed` | BooleanField | allow exporting collected data | no | `False` |

## Notes

- Natural key: `(slug, project)`; `(name, project)` is unique.
- `is_running()` checks `start <= today <= end` (no end = always running).
- Public URL: `/{locale}/register/{slug}/` (see `get_absolute_url`).
- Custom permissions: `can_manage_registration`, `register`,
  `create_translation`, `export_data`, `can_view_data`.
- When `encrypt_data` is enabled, `setup_encryption_keys()` generates an RSA
  key pair: the public key is stored here, the private key must be kept out
  of the database.
