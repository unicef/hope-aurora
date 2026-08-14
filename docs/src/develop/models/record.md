# Record

One submission of a registration. The collected fields are stored as JSON,
optionally RSA-encrypted, together with metadata and file attachments.

Module: `aurora.registration.models` — `class Record(models.Model)`

## Relations

- **registration** → `Registration` (FK, PROTECT)
- **registrar** → `User` (FK, SET_NULL) — the user who submitted the record

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `registration` | ForeignKey(Registration, PROTECT) | owning registration | no | — |
| `unique_field` | CharField(255) | value of the unique field (db-indexed) | yes | `None` |
| `remote_ip` | RemoteIp (GenericIPAddressField) | client IP, captured automatically on insert | yes | `None` |
| `timestamp` | DateTimeField | submission time (`auto_now_add`, db-indexed) | no | — |
| `storage` | BinaryField | raw storage payload (strategy-dependent) | yes | `None` |
| `ignored` | BooleanField | mark record as ignored (e.g. duplicates) | yes | `None` |
| `size` | IntegerField | payload size | yes | `None` |
| `counters` | JSONField | counter snapshot at submission time | yes | `None` |
| `fields` | JSONField | collected field values | yes | `None` |
| `files` | BinaryField | attached files (serialized) | yes | `None` |
| `index1`/`index2`/`index3` | CharField(255) | generic indexed values for querying | yes | `None` |
| `is_offline` | BooleanField | record submitted from an offline client | no | `False` |
| `registrar` | ForeignKey(User, SET_NULL) | submitting user | yes | `None` |

## Notes

- `(registration, unique_field)` is unique — this enforces the per-form
  unique key at the database level.
- `unicef_id` derives the canonical HOPE id from the record.
- `data` / `payload` return decrypted values when the registration is not
  encrypted; encrypted registrations deny access without the private key.
- `decrypt(private_key=...)` decrypts encrypted fields/files; offline records
  are decrypted with `decrypt_offline`.
