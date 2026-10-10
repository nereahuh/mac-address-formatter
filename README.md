# mac_address_formatter

A small, zero-dependency Python library for parsing, validating, and reformatting 48-bit MAC addresses between colon, hyphen, dot (Cisco), and raw hex notations.

## Usage

```python
from mac_address_formatter import parse, validate, format, normalize

parse("aa:bb:cc:dd:ee:ff")            # -> "aabbccddeeff"
validate("aabb.ccdd.eeff")            # -> True
format("aabbccddeeff", "-")            # -> "aa-bb-cc-dd-ee-ff"
normalize("aa-bb-cc-dd-ee-ff", ":")    # -> "aa:bb:cc:dd:ee:ff"
```

The exported names are: `parse`, `validate`, `format`, `normalize`, and `InvalidMacAddressError`.

## Why

When hardware inventories, DHCP logs, and switch configs all get dumped into the same database, the same MAC address shows up in three or four notations. This library exists to collapse that variety into one canonical form and emit whichever notation the downstream system expects, without pulling in a networking framework.

The trade-off is that it only supports 48-bit MAC addresses and only four notations. It does not handle 64-bit EUI-64 identifiers, case preservation, or whitespace. If you need those, this is the wrong tool.

## Edge cases

- Hex output is always lowercase. If you need uppercase, call `.upper()` on the returned string.
- Mixed separators inside one string (e.g. `aa:bb-cc:dd:ee:ff`) are rejected, not silently fixed. They usually indicate corrupted input.
- The dot separator emits Cisco-style half-words (`aabb.ccdd.eeff`), not octet pairs with dots.
- Empty strings, `None`, and non-string types raise `InvalidMacAddressError`, which subclasses `ValueError`.

## Running the tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

