# FlexFormField

One question of a form. The widget and behavior come from a registered field
type (`field_type` strategy); the instance-level options live in `advanced`.

Module: `aurora.core.models` — `class FlexFormField(AdminReverseMixin, NaturalKeyModel, I18NModel, OrderableModel)`

## Relations

- **flex_form** → `FlexForm` (FK, CASCADE, `related_name="fields"`)
- **validator** → `Validator` (FK, PROTECT; only validators with target `field`)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `flex_form` | ForeignKey(FlexForm, CASCADE) | owning form | no | — |
| `label` | CharField(2000) | question text (i18n-enabled) | no | — |
| `name` | CharField(100) | internal name, must match `^[a-z_0-9]*$`; auto-generated from the label | yes | — |
| `field_type` | StrategyClassField | widget/field class from `field_registry` | no | — |
| `choices` | CharField(2000) | comma-separated choices for choice fields | yes | `None` |
| `required` | BooleanField | whether the question is mandatory | no | `False` |
| `enabled` | BooleanField | include the field in the compiled form | no | `True` |
| `validator` | ForeignKey(Validator, PROTECT) | field-level validator | yes | `None` |
| `validation` | TextField | inline validation code | yes | `None` |
| `regex` | RegexField | client-side pattern validation | yes | `None` |
| `advanced` | JSONField | widget/field options (`widget_kwargs`, `field_kwargs`, `smart` attrs) | yes | `None` |

## Notes

- Natural key: `(flex_form, name)` is unique.
- `get_instance()` instantiates the concrete Django form field; invalid
  configurations are rejected in `clean()`.
- `ordering` (from `OrderableModel`) determines the field order in the form.
