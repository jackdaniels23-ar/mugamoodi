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
import shutil
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
BRAND = "Mugamoodi"
TAGLINE = "transparent URL aliases for your terminal"


def use_color() -> bool:
    return sys.stdout.isatty() and not os.getenv("NO_COLOR")


def paint(text: str, code: str) -> str:
    if not use_color():
        return text
    return f"\033[{code}m{text}\033[0m"


def blue(text: str) -> str:
    return paint(text, "34")


def green(text: str) -> str:
    return paint(text, "32")


def yellow(text: str) -> str:
    return paint(text, "33")


def dim(text: str) -> str:
    return paint(text, "2")


def bold(text: str) -> str:
    return paint(text, "1")


def terminal_width(default: int = 78) -> int:
    return max(58, min(shutil.get_terminal_size((default, 20)).columns, 100))


def banner() -> None:
    width = terminal_width()
    title = f"{BRAND} :: {TAGLINE}"
    print(blue("+" + "-" * (width - 2) + "+"))
    print(blue("|") + f" {bold(title)}".ljust(width - 1) + blue("|"))
    print(blue("+" + "-" * (width - 2) + "+"))


def section(title: str) -> None:
    print()
    print(blue(f"== {title} =="))


def detail_row(label: str, value: str) -> None:
    print(f"  {dim(label.rjust(12))}  {value}")


def success(message: str) -> None:
    print(f"{green('[ok]')} {bold(message)}")


def warn(message: str) -> None:
    print(f"{yellow('[!]')} {message}")


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


def prompt_required(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Please enter a value.")


def normalize_base_url(raw_base_url: str) -> str:
    base_url = normalize_url(raw_base_url)
    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"


def command_mask(args: argparse.Namespace) -> int:
    banner()
    if not args.url:
        section("Interactive mask")
        args.url = prompt_required("1. URL to be changed")
        args.base_url = normalize_base_url(prompt_required("2. Masking website"))
        if not args.alias:
            custom_alias = input("Alias slug (press Enter for random): ").strip()
            args.alias = custom_alias or None

    db = load_db()
    url = normalize_url(args.url)
    slug = validate_slug(args.alias) if args.alias else make_slug(db)

    if slug in db and not args.force:
        raise SystemExit(f"Alias '{slug}' already exists. Use --force to replace it.")

    db[slug] = {
        "url": url,
        "base_url": args.base_url,
        "note": args.note or "",
        "created_at": now_iso(),
    }
    save_db(db)

    success("Alias created")
    detail_row("masked", blue(format_alias(slug, args.base_url)))
    detail_row("destination", url)
    if args.note:
        detail_row("note", args.note)
    return 0


def command_wizard(args: argparse.Namespace) -> int:
    return command_mask(args)


def command_reveal(args: argparse.Namespace) -> int:
    banner()
    db = load_db()
    slug = extract_slug(args.alias_or_slug)
    item = db.get(slug)

    if not item:
        raise SystemExit(f"No alias found for '{slug}'.")

    base_url = item.get("base_url", args.base_url)
    section("Reveal")
    detail_row("alias", blue(format_alias(slug, base_url)))
    detail_row("destination", item["url"])
    detail_row("created", item.get("created_at", "unknown"))
    if item.get("note"):
        detail_row("note", item["note"])
    return 0


def command_list(args: argparse.Namespace) -> int:
    banner()
    db = load_db()
    if not db:
        warn("No aliases yet.")
        print(dim("  Try: mugamoodi mask example.com -a demo"))
        return 0

    rows = []
    for slug, item in sorted(db.items()):
        base_url = item.get("base_url", args.base_url)
        rows.append((format_alias(slug, base_url), item["url"], item.get("note", "")))

    alias_width = min(max(len(row[0]) for row in rows), 48)
    section(f"Saved aliases ({len(rows)})")
    print(f"  {bold('alias'.ljust(alias_width))}  {bold('destination')}")
    print(f"  {dim('-' * alias_width)}  {dim('-' * 40)}")
    for alias, url, note in rows:
        label = alias if len(alias) <= alias_width else alias[: alias_width - 1] + "..."
        suffix = f"  ({note})" if note else ""
        print(f"  {blue(label.ljust(alias_width))}  {url}{dim(suffix)}")

    return 0


def command_remove(args: argparse.Namespace) -> int:
    banner()
    db = load_db()
    slug = extract_slug(args.alias_or_slug)

    if slug not in db:
        raise SystemExit(f"No alias found for '{slug}'.")

    removed = db.pop(slug)
    save_db(db)
    base_url = removed.get("base_url", args.base_url)
    success("Alias removed")
    detail_row("alias", blue(format_alias(slug, base_url)))
    detail_row("destination", removed["url"])
    return 0


def command_open(args: argparse.Namespace) -> int:
    banner()
    db = load_db()
    slug = extract_slug(args.alias_or_slug)
    item = db.get(slug)

    if not item:
        raise SystemExit(f"No alias found for '{slug}'.")

    success("Opening destination")
    detail_row("url", item["url"])
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
        epilog=(
            "examples:\n"
            "  mugamoodi mask\n"
            "  mugamoodi mask example.com -a demo\n"
            "  mugamoodi reveal demo\n"
            "  mugamoodi list\n"
            "  NO_COLOR=1 mugamoodi list"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base shown for aliases. Default: {DEFAULT_BASE_URL}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    mask_parser = subparsers.add_parser("mask", help="Create a new URL alias.")
    mask_parser.add_argument("url", nargs="?", help="Destination URL.")
    mask_parser.add_argument("-a", "--alias", help="Custom alias slug.")
    mask_parser.add_argument("-n", "--note", help="Optional label for your own records.")
    mask_parser.add_argument("-f", "--force", action="store_true", help="Replace an existing alias.")
    mask_parser.set_defaults(func=command_mask)

    wizard_parser = subparsers.add_parser("wizard", help="Ask for the URL and masking website.")
    wizard_parser.add_argument("-a", "--alias", help="Custom alias slug.")
    wizard_parser.add_argument("-n", "--note", help="Optional label for your own records.")
    wizard_parser.add_argument("-f", "--force", action="store_true", help="Replace an existing alias.")
    wizard_parser.set_defaults(url=None, func=command_wizard)

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
