#!/usr/bin/env python3
"""Mugamoodi: a transparent URL alias CLI.

This tool creates local, human-friendly aliases for URLs and stores the
destination in a JSON file. It is intentionally transparent: every generated
alias can be revealed and listed with its real destination.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import string
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


APP_DIR = Path(
    os.getenv(
        "MUGAMOODI_HOME",
        Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "mugamoodi",
    )
)
DB_PATH = APP_DIR / "links.json"
DEFAULT_BASE_URL = "https://mugamoodi.local"
SLUG_ALPHABET = string.ascii_lowercase + string.digits
SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{1,63}$")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_db() -> dict[str, dict[str, str]]:
    if not DB_PATH.exists():
        return {}

    try:
        with DB_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not read {DB_PATH}: invalid JSON ({exc}).")

    if not isinstance(data, dict):
        raise SystemExit(f"Could not read {DB_PATH}: expected a JSON object.")

    return data


def save_db(data: dict[str, dict[str, str]]) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with DB_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")


def normalize_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if not parsed.scheme:
        raw_url = "https://" + raw_url
        parsed = urlparse(raw_url)

    if parsed.scheme not in {"http", "https"}:
        raise SystemExit("Only http:// and https:// URLs are supported.")

    if not parsed.netloc or "." not in parsed.netloc:
        raise SystemExit("Please enter a valid URL with a domain, like https://example.com.")

    return raw_url


def validate_slug(slug: str) -> str:
    if not SLUG_PATTERN.match(slug):
        raise SystemExit("Alias must be 2-64 characters: letters, numbers, hyphens, or underscores.")
    return slug.lower()


def make_slug(existing: dict[str, dict[str, str]], length: int = 7) -> str:
    while True:
        slug = "".join(secrets.choice(SLUG_ALPHABET) for _ in range(length))
        if slug not in existing:
            return slug


def format_alias(slug: str, base_url: str) -> str:
    return f"{base_url.rstrip('/')}/{slug}"


def command_mask(args: argparse.Namespace) -> int:
    db = load_db()
    url = normalize_url(args.url)
    slug = validate_slug(args.alias) if args.alias else make_slug(db)

    if slug in db and not args.force:
        raise SystemExit(f"Alias '{slug}' already exists. Use --force to replace it.")

    db[slug] = {
        "url": url,
        "note": args.note or "",
        "created_at": now_iso(),
    }
    save_db(db)

    print("Alias created")
    print(f"  masked:      {format_alias(slug, args.base_url)}")
    print(f"  destination: {url}")
    if args.note:
        print(f"  note:        {args.note}")
    return 0


def command_reveal(args: argparse.Namespace) -> int:
    db = load_db()
    slug = extract_slug(args.alias_or_slug)
    item = db.get(slug)

    if not item:
        raise SystemExit(f"No alias found for '{slug}'.")

    print(f"alias:       {format_alias(slug, args.base_url)}")
    print(f"destination: {item['url']}")
    print(f"created:     {item.get('created_at', 'unknown')}")
    if item.get("note"):
        print(f"note:        {item['note']}")
    return 0


def command_list(args: argparse.Namespace) -> int:
    db = load_db()
    if not db:
        print("No aliases yet.")
        return 0

    rows = []
    for slug, item in sorted(db.items()):
        rows.append((format_alias(slug, args.base_url), item["url"], item.get("note", "")))

    alias_width = min(max(len(row[0]) for row in rows), 48)
    print(f"{'alias'.ljust(alias_width)}  destination")
    print(f"{'-' * alias_width}  {'-' * 40}")
    for alias, url, note in rows:
        label = alias if len(alias) <= alias_width else alias[: alias_width - 1] + "..."
        suffix = f"  ({note})" if note else ""
        print(f"{label.ljust(alias_width)}  {url}{suffix}")

    return 0


def command_remove(args: argparse.Namespace) -> int:
    db = load_db()
    slug = extract_slug(args.alias_or_slug)

    if slug not in db:
        raise SystemExit(f"No alias found for '{slug}'.")

    removed = db.pop(slug)
    save_db(db)
    print(f"Removed {format_alias(slug, args.base_url)} -> {removed['url']}")
    return 0


def command_open(args: argparse.Namespace) -> int:
    db = load_db()
    slug = extract_slug(args.alias_or_slug)
    item = db.get(slug)

    if not item:
        raise SystemExit(f"No alias found for '{slug}'.")

    print(f"Opening destination: {item['url']}")
    webbrowser.open(item["url"])
    return 0


def extract_slug(alias_or_slug: str) -> str:
    parsed = urlparse(alias_or_slug)
    if parsed.scheme and parsed.path:
        slug = parsed.path.strip("/").split("/")[-1]
    else:
        slug = alias_or_slug.strip().strip("/")
    return validate_slug(slug)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mugamoodi",
        description="Mugamoodi creates and manages transparent local aliases for URLs.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base shown for aliases. Default: {DEFAULT_BASE_URL}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    mask_parser = subparsers.add_parser("mask", help="Create a new URL alias.")
    mask_parser.add_argument("url", help="Destination URL.")
    mask_parser.add_argument("-a", "--alias", help="Custom alias slug.")
    mask_parser.add_argument("-n", "--note", help="Optional label for your own records.")
    mask_parser.add_argument("-f", "--force", action="store_true", help="Replace an existing alias.")
    mask_parser.set_defaults(func=command_mask)

    reveal_parser = subparsers.add_parser("reveal", help="Show the real destination.")
    reveal_parser.add_argument("alias_or_slug", help="Alias URL or slug.")
    reveal_parser.set_defaults(func=command_reveal)

    list_parser = subparsers.add_parser("list", help="List saved aliases.")
    list_parser.set_defaults(func=command_list)

    remove_parser = subparsers.add_parser("remove", help="Delete an alias.")
    remove_parser.add_argument("alias_or_slug", help="Alias URL or slug.")
    remove_parser.set_defaults(func=command_remove)

    open_parser = subparsers.add_parser("open", help="Open the real destination in your browser.")
    open_parser.add_argument("alias_or_slug", help="Alias URL or slug.")
    open_parser.set_defaults(func=command_open)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
