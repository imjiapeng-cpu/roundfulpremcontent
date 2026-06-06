#!/usr/bin/env python3
"""Validate the premium-content repo.

Runs a series of checks against everything under content/ and exits
non-zero if any check fails. Missing zh-Hans for an article is reported
as a warning and does NOT fail the run.

Usage: python scripts/validate.py
Requires: Python 3.11+, pyyaml.
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    sys.stderr.write(
        "ERROR: pyyaml is required. Install with `pip install pyyaml`.\n"
    )
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"

REQUIRED_FIELDS = {
    "id": str,
    "title": str,
    "summary": str,
    "category": str,
    "minutesRead": int,
    "order": int,
    "tier": str,
    "updatedAt": (str, dt.date),  # PyYAML may auto-parse YYYY-MM-DD into a date
}
SHARED_FIELDS = ("id", "order", "tier", "category", "minutesRead", "updatedAt")
ALLOWED_TIERS = {"free", "premium"}
ALLOWED_CATEGORIES = {"Method", "Reference", "Science", "Mastery", "Story"}
ID_PATTERN = re.compile(r"^[0-9]{3}-[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SUMMARY_HARD_MAX = 200
FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z",
    re.DOTALL,
)


class ValidationError(Exception):
    pass


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter dict, body text). Raises ValidationError on bad shape."""
    raw = path.read_text(encoding="utf-8")
    if not raw.endswith("\n"):
        raise ValidationError(f"{path}: file must end with a trailing newline")
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise ValidationError(
            f"{path}: missing or malformed YAML frontmatter "
            f"(must start with `---` and contain a closing `---`)"
        )
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise ValidationError(f"{path}: YAML parse error: {e}") from e
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: frontmatter must be a YAML mapping")
    return data, m.group(2)


def validate_one(path: Path, locale: str) -> dict:
    """Validate a single .md file. Returns its frontmatter dict on success."""
    fm, _body = parse_frontmatter(path)

    for field, types in REQUIRED_FIELDS.items():
        if field not in fm:
            raise ValidationError(f"{path}: missing required field `{field}`")
        if not isinstance(fm[field], types):
            raise ValidationError(
                f"{path}: field `{field}` has wrong type "
                f"(got {type(fm[field]).__name__})"
            )

    # Normalize updatedAt: PyYAML may give us a date object
    if isinstance(fm["updatedAt"], dt.date):
        fm["updatedAt"] = fm["updatedAt"].isoformat()
    if not DATE_PATTERN.match(fm["updatedAt"]):
        raise ValidationError(
            f"{path}: `updatedAt` must be YYYY-MM-DD, got {fm['updatedAt']!r}"
        )
    try:
        dt.date.fromisoformat(fm["updatedAt"])
    except ValueError as e:
        raise ValidationError(f"{path}: `updatedAt` is not a real date: {e}") from e

    if not ID_PATTERN.match(fm["id"]):
        raise ValidationError(
            f"{path}: `id` must match NNN-kebab-case-slug, got {fm['id']!r}"
        )
    if fm["id"] != path.stem:
        raise ValidationError(
            f"{path}: `id` ({fm['id']}) must equal filename stem ({path.stem})"
        )
    if fm["order"] < 100:
        raise ValidationError(
            f"{path}: `order` must be >= 100 "
            f"(1-99 reserved for bundled articles), got {fm['order']}"
        )
    if fm["minutesRead"] < 1:
        raise ValidationError(
            f"{path}: `minutesRead` must be >= 1, got {fm['minutesRead']}"
        )
    if fm["tier"] not in ALLOWED_TIERS:
        raise ValidationError(
            f"{path}: `tier` must be one of {sorted(ALLOWED_TIERS)}, "
            f"got {fm['tier']!r}"
        )
    if fm["category"] not in ALLOWED_CATEGORIES:
        raise ValidationError(
            f"{path}: `category` must be one of {sorted(ALLOWED_CATEGORIES)}, "
            f"got {fm['category']!r}"
        )
    if not fm["title"].strip():
        raise ValidationError(f"{path}: `title` cannot be empty")
    if not fm["summary"].strip():
        raise ValidationError(f"{path}: `summary` cannot be empty")
    if len(fm["summary"]) > SUMMARY_HARD_MAX:
        raise ValidationError(
            f"{path}: `summary` exceeds hard cap of {SUMMARY_HARD_MAX} chars "
            f"(got {len(fm['summary'])})"
        )

    fm["_path"] = path
    fm["_locale"] = locale
    return fm


def validate_repo() -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    if not CONTENT_DIR.is_dir():
        return ([f"content/ directory missing at {CONTENT_DIR}"], [])

    by_id: dict[str, list[dict]] = defaultdict(list)
    by_order: dict[int, list[Path]] = defaultdict(list)

    locale_dirs = sorted(p for p in CONTENT_DIR.iterdir() if p.is_dir())
    for locale_dir in locale_dirs:
        locale = locale_dir.name
        for md_path in sorted(locale_dir.glob("*.md")):
            try:
                fm = validate_one(md_path, locale)
            except ValidationError as e:
                errors.append(str(e))
                continue
            by_id[fm["id"]].append(fm)
            by_order[fm["order"]].append(md_path)

    # Cross-locale: shared fields must agree
    for article_id, variants in by_id.items():
        ref = variants[0]
        for v in variants[1:]:
            for field in SHARED_FIELDS:
                if v[field] != ref[field]:
                    errors.append(
                        f"shared-field mismatch for id={article_id}: "
                        f"`{field}` is {ref[field]!r} in {ref['_path']} "
                        f"but {v[field]!r} in {v['_path']}"
                    )

    # Every article needs an en variant; missing zh-Hans / zh-Hant are warnings
    for article_id, variants in by_id.items():
        locales = {v["_locale"] for v in variants}
        if "en" not in locales:
            errors.append(
                f"article id={article_id} is missing the required `en` variant"
            )
        if "zh-Hans" not in locales:
            warnings.append(
                f"article id={article_id} is missing a `zh-Hans` variant "
                f"(falling back to en in the iOS app)"
            )
        if "zh-Hant" not in locales:
            warnings.append(
                f"article id={article_id} is missing a `zh-Hant` variant "
                f"(falling back to en in the iOS app)"
            )

    # Order uniqueness across the entire repo (across ids, ignoring locales)
    order_to_ids: dict[int, set[str]] = defaultdict(set)
    for variants in by_id.values():
        for v in variants:
            order_to_ids[v["order"]].add(v["id"])
    for order, ids in order_to_ids.items():
        if len(ids) > 1:
            errors.append(
                f"`order` {order} is used by multiple articles: "
                f"{sorted(ids)} (each article must have a unique order)"
            )

    return errors, warnings


def main() -> int:
    errors, warnings = validate_repo()
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        print(f"\nValidation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"OK ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
