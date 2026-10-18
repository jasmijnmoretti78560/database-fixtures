# database-fixtures

Provides offline access to IANA time-zone identifiers and metadata (country code, coordinates, and comment) without any network or file-system access.

```python
from database_fixtures import TimeZoneDatabase

db = TimeZoneDatabase()

print(db.contains("America/New_York"))          # True
print(db.get("America/New_York").country_code)   # US
print(db.zones_for_country("US"))                # ['America/New_York', ...]
print(db.resolve_alias("UTC"))                   # Etc/UTC
```

## Why this exists

Code that handles time zones often needs to validate identifiers or look up the country behind a zone, but reaching out to the system zone database or a third-party package introduces a dependency that may not exist in a locked-down or offline environment. This library bundles a curated slice of the IANA `zone.tab` as a Python string literal so the data is available immediately, with zero runtime dependencies.

The trade-off is currency and completeness. The bundled data covers every ISO 3166 country and the `Etc/*` zones, but it is a fixed snapshot — it will not pick up future revisions to the upstream database. If you need rules for historical offset changes, pair this library with `zoneinfo` or another source of compiled tzdata; this library gives you identifiers and metadata, not transition rules.

## Edge cases

The library resolves exactly one alias family: the UTC-style synonyms (`UTC`, `GMT`, `Etc/UTC`, `Zulu`, `Universal`, and friends) all map to the canonical `Etc/UTC`. It does **not** resolve the `backward` file's deprecated identifiers (e.g. `US/Eastern`) — those are returned unchanged if they happen to exist in the bundled data, or `None` if they do not. The `ZZ` country code is used for `Etc/*` zones that are not tied to a real country, matching the upstream convention.
