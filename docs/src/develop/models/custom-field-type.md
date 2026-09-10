# CustomFieldType

A user-defined field type: an instance of a registered base field type with
fixed attributes, reusable across forms like a built-in type.

Module: `aurora.core.models` — `class CustomFieldType(AdminReverseMixin, NaturalKeyModel, models.Model)`

## Relations

- **validator** → `Validator` (FK, PROTECT; only validators with target `field`)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `name` | CharField(100) | unique name, must match `[A-Z][a-zA-Z0-9_]*` | no | — |
| `base_type` | StrategyClassField | underlying field class from `field_registry` | no | `forms.CharField` |
| `attrs` | JSONField | fixed kwargs applied when the type is instantiated | no | `{}` |
| `regex` | RegexField | client-side pattern validation | yes | `None` |
| `validator` | ForeignKey(Validator, PROTECT) | field-level validator | yes | `None` |

## Notes

- Natural key: `name`.
- On save the generated class is registered into `field_registry`, making it
  available as a `field_type` for `FlexFormField`.
- `clean()` instantiates the class with `attrs` to validate the definition.
