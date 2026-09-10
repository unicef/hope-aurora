# Message

A translation entry: one message id per locale with its localized content.
Backs the multilingual engine (`aurora.i18n`).

Module: `aurora.i18n.models` — `class Message(NaturalKeyModel)`

## Relations

- None; translations of the same source string share `msgcode` (use
  `get_siblings()` to retrieve them).

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `timestamp` | DateTimeField | creation time (`auto_now_add`) | no | — |
| `locale` | LanguageField | the locale of the message (db-indexed) | no | — |
| `msgid` | TextField | original (source) message value (db-indexed) | no | — |
| `msgstr` | TextField | localized content | yes | `None` |
| `md5` | CharField(512) | md5 of `msgid\|locale`, unique (computed on save) | no | — |
| `msgcode` | CharField(512) | md5 of `msgid`; shared by all translations of the same message | no | — |
| `auto` | BooleanField | auto-generated message | no | `False` |
| `draft` | BooleanField | draft messages are not used in translation | no | `True` |
| `used` | BooleanField | is the message used somewhere in Aurora | no | `True` |
| `last_hit` | DateTimeField | last time the translation was used | yes | `None` |

## Notes

- `(msgid, locale)` is unique.
- `update_or_create_translation(value, locale)` creates or updates a
  translation of an existing message.
