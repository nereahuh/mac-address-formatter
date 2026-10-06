# tests for mac_address_formatter.core
#
# Each test covers a behaviour the implementation actually claims to support.
# We deliberately do NOT test 64-bit EUI-64 parsing, case preservation, or
# whitespace tolerance, because the library explicitly rejects all three.

import unittest

from mac_address_formatter import (
    InvalidMacAddressError,
    parse,
    validate,
    format,
    normalize,
)


class TestParse(unittest.TestCase):
    def test_parse_colon(self):
        self.assertEqual(parse("aa:bb:cc:dd:ee:ff"), "aabbccddeeff")

    def test_parse_hyphen(self):
        self.assertEqual(parse("aa-bb-cc-dd-ee-ff"), "aabbccddeeff")

    def test_parse_dot(self):
        # Cisco half-word notation: three groups of four hex digits.
        self.assertEqual(parse("aabb.ccdd.eeff"), "aabbccddeeff")

    def test_parse_raw(self):
        self.assertEqual(parse("aabbccddeeff"), "aabbccddeeff")

    def test_parse_uppercase_input_normalised_to_lowercase(self):
        # The library always emits lowercase, regardless of input case.
        self.assertEqual(parse("AA:BB:CC:DD:EE:FF"), "aabbccddeeff")
        self.assertEqual(parse("AABBCCDDEEFF"), "aabbccddeeff")

    def test_parse_mixed_separators_rejected(self):
        # Mixed separators are treated as corrupted input and rejected.
        with self.assertRaises(InvalidMacAddressError):
            parse("aa:bb-cc:dd:ee:ff")

    def test_parse_wrong_length_rejected(self):
        with self.assertRaises(InvalidMacAddressError):
            parse("aa:bb:cc:dd:ee")           # too few octets
        with self.assertRaises(InvalidMacAddressError):
            parse("aa:bb:cc:dd:ee:ff:00")     # too many octets
        with self.assertRaises(InvalidMacAddressError):
            parse("aabbccddeef")              # 11 hex digits
        with self.assertRaises(InvalidMacAddressError):
            parse("aabbccddeeff00")           # 14 hex digits

    def test_parse_non_hex_rejected(self):
        with self.assertRaises(InvalidMacAddressError):
            parse("gg:bb:cc:dd:ee:ff")

    def test_parse_empty_and_none(self):
        with self.assertRaises(InvalidMacAddressError):
            parse("")
        with self.assertRaises(InvalidMacAddressError):
            parse(None)
        with self.assertRaises(InvalidMacAddressError):
            parse(123)  # type: ignore[arg-type]

    def test_parse_error_is_value_error(self):
        # InvalidMacAddressError subclasses ValueError so that broad
        # `except ValueError` handlers keep working.
        with self.assertRaises(ValueError):
            parse("not a mac")


class TestValidate(unittest.TestCase):
    def test_validate_valid_returns_true(self):
        self.assertTrue(validate("aa:bb:cc:dd:ee:ff"))
        self.assertTrue(validate("aabbccddeeff"))

    def test_validate_invalid_returns_false(self):
        self.assertFalse(validate("aa:bb-cc:dd:ee:ff"))
        self.assertFalse(validate(""))
        self.assertFalse(validate(None))


class TestFormat(unittest.TestCase):
    def test_format_to_colon(self):
        self.assertEqual(format("aabbccddeeff", ":"), "aa:bb:cc:dd:ee:ff")

    def test_format_default_separator_is_colon(self):
        # The default separator should be colon, matching the most common
        # textual representation of MAC addresses.
        self.assertEqual(format("aabbccddeeff"), "aa:bb:cc:dd:ee:ff")

    def test_format_to_hyphen(self):
        self.assertEqual(format("aa:bb:cc:dd:ee:ff", "-"), "aa-bb-cc-dd-ee-ff")

    def test_format_to_dot(self):
        # Dot notation groups into half-words of four, not octets of two.
        self.assertEqual(format("aa:bb:cc:dd:ee:ff", "."), "aabb.ccdd.eeff")

    def test_format_to_raw(self):
        self.assertEqual(format("aa:bb:cc:dd:ee:ff", ""), "aabbccddeeff")

    def test_format_roundtrip_all_notations(self):
        # Any notation in -> any notation out should preserve the bits.
        original = "aa:bb:cc:dd:ee:ff"
        for sep in (":", "-", ".", ""):
            self.assertEqual(format(format(original, sep), ":"), original)

    def test_format_uppercase_input_lowercase_output(self):
        self.assertEqual(format("AA:BB:CC:DD:EE:FF", ":"), "aa:bb:cc:dd:ee:ff")

    def test_format_invalid_separator_rejected(self):
        with self.assertRaises(ValueError):
            format("aabbccddeeff", "/")

    def test_format_invalid_mac_rejected(self):
        with self.assertRaises(InvalidMacAddressError):
            format("not-a-mac", ":")


class TestNormalize(unittest.TestCase):
    def test_normalize_is_alias_for_format(self):
        # normalize exists for semantic clarity, not for different behaviour.
        self.assertEqual(normalize("aa-bb-cc-dd-ee-ff", ":"), "aa:bb:cc:dd:ee:ff")
        self.assertEqual(normalize("aabb.ccdd.eeff", "-"), "aa-bb-cc-dd-ee-ff")
        self.assertEqual(normalize("aa:bb:cc:dd:ee:ff"), "aa:bb:cc:dd:ee:ff")


if __name__ == "__main__":
    unittest.main()
