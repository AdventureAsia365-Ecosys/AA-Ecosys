#!/usr/bin/env python3
"""Replace the password of a PostgreSQL DSN with a fresh random one (AA-1182, key ceremony group 1).

Reads one DSN on stdin and writes the same DSN with a new password on stdout, so the value only ever passes through a
pipe between `aws secretsmanager get-secret-value` and `aws secretsmanager put-secret-value` (never an argument, a
file or the terminal). User, host, port, database and query stay as they are. The new password is 40 characters of
letters and digits (no percent-encoding needed, and DB Migrate set-password asks for at least 32 printable ASCII
characters). Errors name the problem only, never any part of the input.

Usage: the one-line pipe in docs/ops/runbooks/key-ceremony.md, group 1.
"""
from __future__ import annotations

import secrets
import string
import sys
import urllib.parse

LENGTH = 40
ALPHABET = string.ascii_letters + string.digits


def new_password(length: int = LENGTH) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def rotate(dsn: str, password: str | None = None) -> str:
    """The DSN with its password replaced. ValueError (no part of the DSN in the message) when it is not a
    postgresql:// URL with a user, a host and exactly one '@'."""
    dsn = dsn.strip()
    try:
        parsed = urllib.parse.urlparse(dsn)
    except ValueError:
        raise ValueError("not a parseable URL") from None
    if parsed.scheme not in ("postgresql", "postgres"):
        raise ValueError("not a postgresql:// DSN")
    if parsed.netloc.count("@") != 1:
        raise ValueError("the DSN needs exactly one user[:password]@ part")
    auth, _, hostspec = parsed.netloc.partition("@")
    user = auth.partition(":")[0]
    if not user or not hostspec:
        raise ValueError("the DSN has no user or no host")
    return urllib.parse.urlunparse(parsed._replace(netloc=f"{user}:{password or new_password()}@{hostspec}"))


def main() -> int:
    try:
        sys.stdout.write(rotate(sys.stdin.read()))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
