# mac_address_formatter
"""MAC address parsing, validation, and reformatter.

This package is organised so that importing the package exposes every
function you'd normally want:

    from mac_address_formatter import parse, validate, format, normalize
"""

from .core import (
    InvalidMacAddressError,
    parse,
    validate,
    format,
    normalize,
)

__all__ = [
    "InvalidMacAddressError",
    "parse",
    "validate",
    "format",
    "normalize",
]
