import unittest

from database_fixtures import TimeZoneDatabase, UTC_ALIAS_NAMES
from database_fixtures.core import ZoneRecord


class TestZoneRecord(unittest.TestCase):
    """Unit tests for the ZoneRecord value type."""

    def test_eq_same_values(self):
        a = ZoneRecord("Etc/UTC", "ZZ", "+0000+00000")
        b = ZoneRecord("Etc/UTC", "ZZ", "+0000+00000")
        self.assertEqual(a, b)

    def test_eq_different_comment(self):
        a = ZoneRecord("Etc/UTC", "ZZ", "+0000+00000", "Coordinated Universal Time")
        b = ZoneRecord("Etc/UTC", "ZZ", "+0000+00000", "")
        self.assertNotEqual(a, b)

    def test_eq_against_non_record(self):
        r = ZoneRecord("Etc/UTC", "ZZ", "+0000+00000")
        self.assertNotEqual(r, "Etc/UTC")

    def test_repr_contains_name(self):
        r = ZoneRecord("Europe/London", "GB", "+5130+00010")
        self.assertIn("Europe/London", repr(r))


class TestTimeZoneDatabaseBasic(unittest.TestCase):
    """Tests that the bundled data loads and exposes the documented API."""

    def setUp(self):
        self.db = TimeZoneDatabase()

    def test_zones_returns_sorted_list_of_strings(self):
        zones = self.db.zones()
        self.assertIsInstance(zones, list)
        self.assertEqual(zones, sorted(zones))
        self.assertIn("America/New_York", zones)
        self.assertTrue(all(isinstance(z, str) for z in zones))

    def test_contains_known_zone(self):
        self.assertTrue(self.db.contains("Europe/London"))

    def test_contains_unknown_zone(self):
        self.assertFalse(self.db.contains("Mars/Olympus_Mons"))

    def test_get_returns_record(self):
        record = self.db.get("America/New_York")
        self.assertIsInstance(record, ZoneRecord)
        self.assertEqual(record.name, "America/New_York")
        self.assertEqual(record.country_code, "US")

    def test_get_unknown_returns_none(self):
        self.assertIsNone(self.db.get("Nowhere/Imaginary"))


class TestTimeZoneDatabaseCountry(unittest.TestCase):
    """Tests for country-based lookups."""

    def setUp(self):
        self.db = TimeZoneDatabase()

    def test_zones_for_country_returns_sorted_names(self):
        us_zones = self.db.zones_for_country("US")
        self.assertIsInstance(us_zones, list)
        self.assertIn("America/New_York", us_zones)
        self.assertEqual(us_zones, sorted(us_zones))

    def test_zones_for_country_is_case_insensitive(self):
        self.assertEqual(self.db.zones_for_country("us"), self.db.zones_for_country("US"))

    def test_zones_for_unknown_country_is_empty(self):
        self.assertEqual(self.db.zones_for_country("XX"), [])

    def test_countries_returns_sorted_uppercase_codes(self):
        countries = self.db.countries()
        self.assertEqual(countries, sorted(countries))
        self.assertIn("US", countries)
        self.assertIn("ZZ", countries)
        self.assertTrue(all(len(c) == 2 and c.isupper() for c in countries))


class TestTimeZoneDatabaseAliases(unittest.TestCase):
    """Tests for UTC-alias resolution — the only alias family the library handles."""

    def setUp(self):
        self.db = TimeZoneDatabase()

    def test_utc_alias_resolves_to_etc_utc(self):
        for alias in ("UTC", "Etc/UTC", "GMT", "Zulu", "Universal"):
            with self.subTest(alias=alias):
                self.assertEqual(self.db.resolve_alias(alias), "Etc/UTC")

    def test_utc_alias_names_constant_is_non_empty(self):
        self.assertGreater(len(UTC_ALIAS_NAMES), 1)

    def test_canonical_zone_resolves_to_itself(self):
        self.assertEqual(self.db.resolve_alias("Europe/London"), "Europe/London")

    def test_unknown_name_resolves_to_none(self):
        self.assertIsNone(self.db.resolve_alias("Mars/Olympus"))


class TestParser(unittest.TestCase):
    """Tests for the internal TSV line parser."""

    def test_parse_line_without_comment(self):
        record = TimeZoneDatabase._parse_line(
            "ZZ\t+0000+00000\tEtc/UTC\tCoordinated Universal Time",
            "ZZ\t+0000+00000\tEtc/UTC\tCoordinated Universal Time",
        )
        self.assertEqual(record.comments, "Coordinated Universal Time")

    def test_parse_line_with_empty_comment_field(self):
        record = TimeZoneDatabase._parse_line(
            "ZZ\t+0000+00000\tEtc/GMT\t",
            "ZZ\t+0000+00000\tEtc/GMT\t",
        )
        self.assertEqual(record.comments, "")

    def test_parse_line_raises_on_bad_format(self):
        with self.assertRaises(ValueError):
            TimeZoneDatabase._parse_line("bad data", "bad data")


if __name__ == "__main__":
    unittest.main()
