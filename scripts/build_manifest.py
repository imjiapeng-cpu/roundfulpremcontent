#!/usr/bin/env python3
"""Build manifest.json from the content/ tree.

Walks content/<locale>/*.md, parses each frontmatter block, groups
entries by id, and writes manifest.json at the repo root.

This script does NOT validate. Run scripts/validate.py first (CI does
this for you). If the content is malformed, behavior is undefined.

Usage: python scripts/build_manifest.py
Requires: Python 3.11+, pyyaml.
"""
from __future__ import annotations

import datetime as dt
import json
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
MANIFEST_PATH = REPO_ROOT / "manifest.json"

SCHEMA_VERSION = 1
MIN_APP_VERSION = "1.4.0"

FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z",
    re.DOTALL,
)


def parse_frontmatter(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise SystemExit(f"build_manifest: malformed frontmatter in {path}")
    data = yaml.safe_load(m.group(1)) or {}
    if isinstance(data.get("updatedAt"), dt.date):
        data["updatedAt"] = data["updatedAt"].isoformat()
    return data


def collect() -> dict[str, dict]:
    """Return {id: {shared fields, translations: {locale: {title, summary, path}}}}."""
    grouped: dict[str, dict] = defaultdict(
        lambda: {"translations": {}}
    )

    for locale_dir in sorted(p for p in CONTENT_DIR.iterdir() if p.is_dir()):
        locale = locale_dir.name
        for md_path in sorted(locale_dir.glob("*.md")):
            fm = parse_frontmatter(md_path)
            article_id = fm["id"]

            entry = grouped[article_id]
            # Shared fields: pulled from any locale; validate.py guarantees they agree.
            for field in ("order", "tier", "category", "minutesRead", "updatedAt"):
                entry[field] = fm[field]
            entry["id"] = article_id

            rel_path = md_path.relative_to(REPO_ROOT).as_posix()
            entry["translations"][locale] = {
                "title": fm["title"],
                "summary": fm["summary"],
                "path": rel_path,
            }

    return grouped


def build_manifest() -> dict:
    grouped = collect()
    articles = []
    for article_id in sorted(grouped, key=lambda k: grouped[k]["order"]):
        e = grouped[article_id]
        articles.append({
            "id": e["id"],
            "order": e["order"],
            "tier": e["tier"],
            "category": e["category"],
            "minutesRead": e["minutesRead"],
            "updatedAt": e["updatedAt"],
            "translations": dict(sorted(e["translations"].items())),
        })

    return {
        "version": SCHEMA_VERSION,
        "generatedAt": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
        "minAppVersion": MIN_APP_VERSION,
        "articles": articles,
    }


def main() -> int:
    if not CONTENT_DIR.is_dir():
        print(f"ERROR: content/ not found at {CONTENT_DIR}", file=sys.stderr)
        return 1

    manifest = build_manifest()
    out = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    MANIFEST_PATH.write_text(out, encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH} with {len(manifest['articles'])} article(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
