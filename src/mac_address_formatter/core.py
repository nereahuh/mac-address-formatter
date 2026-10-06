"""Core implementation of MAC address parsing and formatting.

Design decision (stated plainly):
    This library accepts *exactly* 48-bit EUI-48 / MAC-48 addresses and nothing
    else. It does NOT try to support:
      - 64-bit EUI-64 addresses
      - case conversion of the hex digits (lowercase is always emitted)
      - leading/trailing whitespace (the caller is expected to strip input)
      - empty strings

The reason is simple: every extra accepted shape multiplies the number of
edge cases the caller has to think about. One shape, one rule. If a caller
needs EUI-64, this library is not the right tool.

Also note that hex output is always lowercase, because uppercase is a purely
presentational choice that's better left to the caller via `.upper()` on the
returned string.
"""

from __future__ import annotations

import re
from typing import Optional

__all__ = [
    "InvalidMacAddressError",
    "parse",
    "validate",
    "format",
    "normalize",
]

# A MAC-48 is exactly 12 hex digits.
# We allow them to be grouped by colons, hyphens, dots, or nothing at all,
# but the separators must be internally consistent. Mixing separators
# (e.g. "aa:bb-cc") would be a sign of corrupted input and is rejected.
#
# The four recognised patterns, and the group sizes they imply:
#   "aa:bb:cc:dd:ee:ff"   -> octets of 2 (6 groups of 2)
#   "aa-bb-cc-dd-ee-ff"   -> octets of 2 (6 groups of 2)
#   "aabb.ccdd.eeff"      -> half-words of 4 (3 groups of 4) - Cisco style
#   "aabbccddeeff"        -> raw, no groups
#
# We deliberately reject mixed separators like "aa:bb-cc:dd:ee:ff" because
# accepting them would make the API ambiguous about what "normalising"
# should mean. Better to fail loudly.
_PATTERNS = [
    # colon-separated octets
    (re.compile(r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$"), 2),
    # hyphen-separated octets
    (re.compile(r"^(?:[0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2}$"), 2),
    # dot-separated half-words (Cisco notation)
    (re.compile(r"^(?:[0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4}$"), 4),
    # raw, no separator
    (re.compile(r"^[0-9a-fA-F]{12}$"), 12),
]


class InvalidMacAddressError(ValueError):
    """Raised when a string cannot be parsed as a 48-bit MAC address.

    A subclass of ValueError so that existing `except ValueError` blocks
    continue to work, while still allowing finer-grained handling if desired.
    """


def parse(value: str) -> str:
    """Parse a MAC address string and return its normalised form.

    The normalised form is 12 lowercase hex digits with no separator, e.g.
    "aabbccddeeff". This is the canonical representation used internally
    and returned by `parse`.

    Args:
        value: A string in one of the four accepted notations
            (colon, hyphen, dot, or raw hex). Must be exactly 48 bits worth
            of hex digits when separators are stripped.

    Returns:
        The 12-character lowercase hex string with no separators.

    Raises:
        InvalidMacAddressError: If the input is None, not a string, or does
            not match any of the four accepted notations.
    """
    if value is None or not isinstance(value, str):
        raise InvalidMacAddressError(
            f"expected a str, got {type(value).__name__ if value is not None else 'None'}"
        )

    if not value:
        raise InvalidMacAddressError("empty string is not a MAC address")

    for pattern, _group_size in _PATTERNS:
        if pattern.match(value):
            # All four patterns match the same total set of hex digits (12),
            # so stripping every non-hex character yields the canonical form.
            return re.sub(r"[^0-9a-fA-F]", "", value).lower()

    # If we reach here, the input didn't match any pattern. Provide a
    # useful error message including the rejected value so the caller can
    # see what went wrong without inspecting logs.
    raise InvalidMacAddressError(f"not a valid 48-bit MAC address: {value!r}")


def validate(value: str) -> bool:
    """Return True if *value* is a valid MAC address, False otherwise.

    This is a convenience wrapper around `parse` for callers who want a
    boolean predicate rather than exception handling. It deliberately
    catches `InvalidMacAddressError` (a subclass of `ValueError`) rather
    than `BaseException`, so that genuine errors like a KeyboardInterrupt
    still propagate.
    """
    try:
        parse(value)
        return True
    except InvalidMacAddressError:
        return False


def format(value: str, separator: str = ":") -> str:
    """Format a MAC address string into the requested notation.

    Args:
        value: A MAC address in any of the four accepted notations.
        separator: One of ":" (colon, default), "-" (hyphen), "." (dot,
            Cisco half-word style), or "" (empty, raw hex).

    Returns:
        The MAC address in the requested notation, lowercase.

    Raises:
        InvalidMacAddressError: If *value* is not a valid MAC address.
        ValueError: If *separator* is not one of the four accepted values.

    Notes:
        The dot separator groups digits into three half-words of four
        ("aabb.ccdd.eeff") rather than six octets of two, because that is
        the established Cisco IOS notation. We do not support an arbitrary
        custom separator because every separator implies a grouping, and
        supporting arbitrary groupings would make the API ambiguous.
    """
    canonical = parse(value)

    if separator == ":":
        return ":".join(canonical[i : i + 2] for i in range(0, 12, 2))
    if separator == "-":
        return "-".join(canonical[i : i + 2] for i in range(0, 12, 2))
    if separator == ".":
        return ".".join(canonical[i : i + 4] for i in range(0, 12, 4))
    if separator == "":
        return canonical

    raise ValueError(
        f"unsupported separator {separator!r}; use one of ':', '-', '.', or ''"
    )


def normalize(value: str, separator: str = ":") -> str:
    """Parse and reformat a MAC address in one call.

    Equivalent to `format(value, separator)`, but named to express intent:
    "I have a MAC in some notation, give me back the same MAC in this other
    notation."

    Args:
        value: A MAC address in any of the four accepted notations.
        separator: The desired output separator (see `format`).

    Returns:
        The MAC address in the requested notation, lowercase.
    """
    return format(value, separator=separator)
