# FlexForm

A form definition: an ordered collection of fields, optionally grouped in
formsets, that a registration renders for data collection. `FlexForm` is
multilingual (`I18NModel`).

Module: `aurora.core.models` — `class FlexForm(AdminReverseMixin, I18NModel, NaturalKeyModel)`

## Relations

- **project** → `Project` (FK, CASCADE)
- **validator** → `Validator` (FK, PROTECT; only validators with target `form`)
- **fields** ← `FlexFormField` (one-to-many, `related_name="fields"`, ordered)
- **formsets** ← `FormSet` (one-to-many, `related_name="formsets"`; child formsets)
- **formset_set** ← `FormSet` (formsets where this form is the embedded form)
- **registration_set** ← `Registration` (one-to-many)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `project` | ForeignKey(Project, CASCADE) | owning project | no | — |
| `name` | CharField(255) | form name, unique | no | — |
| `base_type` | StrategyClassField | base form class from `form_registry` | no | `FlexFormBaseForm` |
| `validator` | ForeignKey(Validator, PROTECT) | form-level validator | yes | `None` |
| `advanced` | JSONField | form options (wizard, layout...) | yes | `{}` |

## Notes

- Natural key: `name`.
- `get_form_class()` compiles enabled fields into a Django form at runtime;
  fields are the source of truth, do not edit the generated class.
- Backwards relation from a form's usages is available through `get_usage()`.
