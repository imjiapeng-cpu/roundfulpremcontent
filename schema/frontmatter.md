# Article frontmatter spec

Every `.md` file under `content/<locale>/` must begin with a YAML frontmatter block. The frontmatter is the canonical source of truth — `scripts/build_manifest.py` reads it and copies the relevant fields into `manifest.json`. `scripts/validate.py` enforces the rules below; CI fails if any of them are violated.

If you just want to publish, you don't need to read this file — copy `content/en/001-sample.md`, edit the values, and you'll be fine. This document exists for when something fails validation and you need to know exactly what the linter expects.

## Shape

```markdown
---
id: 001-sample
title: Sample article
summary: A one-line teaser shown in the Insights list.
category: Science
minutesRead: 4
order: 100
tier: free
updatedAt: 2026-04-24
---

# Body starts here

Markdown body. GFM tables supported. Inline images live in `images/`:

![alt text](../../images/example.png)
```

The frontmatter block is everything between the first two `---` lines. The body is everything after the second `---`. Both must be present, in that order, with no content above the first `---`.

## Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Stable identifier. Must match the filename without `.md`. Format: `NNN-kebab-case-slug` where `NNN` is a 3-digit zero-padded number (e.g. `001-sample`, `042-meal-timing`). |
| `title` | string | yes | Display title shown in the Insights list and at the top of the article view. |
| `summary` | string | yes | One-line teaser shown under the title in the list view. Aim for under ~120 characters; hard cap is 200. |
| `category` | enum | yes | One of: `Method`, `Reference`, `Science`, `Mastery`, `Story`. |
| `minutesRead` | int | yes | Author's estimate of reading time in minutes. Must be ≥ 1. |
| `order` | int | yes | Sort key in the Insights list. Must be ≥ 100 (1–99 are reserved for the bundled in-app articles). Must be unique across the entire repo. |
| `tier` | enum | yes | `free` or `premium`. Use `free` to match the existing convention; remote articles are paywalled at the app layer regardless of this field. |
| `updatedAt` | date | yes | `YYYY-MM-DD`. Used by the iOS app for per-article cache busting — bump this whenever you edit the body. |

## Cross-locale rules

When the same article exists in multiple locales (e.g. `content/en/001-sample.md`, `content/zh-Hans/001-sample.md`, and `content/zh-Hant/001-sample.md`), the **shared** fields must match exactly across all variants:

- `id`
- `order`
- `tier`
- `category`
- `minutesRead`
- `updatedAt`

The **per-locale** fields naturally differ:

- `title`
- `summary`

If `validate.py` finds a mismatch on a shared field — for example, `001-sample.md` says `category: Science` in `en/` but `category: Method` in `zh-Hans/` — it fails the build and tells you which file is out of sync.

## Locale rules

- Every article must have an `en` variant. Missing `en` is a hard error.
- `zh-Hans` (Simplified Chinese) and `zh-Hant` (Traditional Chinese) variants are strongly recommended but optional. Missing either produces a warning, not a failure — the iOS app falls back to `en`.
- New locales beyond `en`, `zh-Hans`, and `zh-Hant` can be added by creating a new directory under `content/` with the BCP-47 locale tag as its name (e.g. `content/ja/`). The manifest schema accepts any string key under `translations`. The validator only emits "missing variant" warnings for the three locales above; add others to `validate.py` if you start using them regularly.

## File rules

- The filename must be `<id>.md`. So if `id: 001-sample`, the file must be `001-sample.md`.
- The file must end with a single trailing newline (`\n`). Most editors do this by default; if yours doesn't, configure it to.
- The file must be UTF-8 encoded. No BOM.

## Body rules

- Use standard CommonMark plus GitHub Flavored Markdown extensions (tables, strikethrough, task lists, fenced code blocks).
- Inline images go in the repo-root `images/` directory (shared across locales) and are referenced relatively: `![alt](../../images/your-image.png)`. Don't put images under `content/<locale>/` — that duplicates assets per language.
- Don't link to external CDNs for images. The iOS app fetches the body from GitHub Pages; external image hosts can break or rate-limit.
- Don't include HTML in the body unless absolutely necessary. The iOS app renders the markdown via a native renderer that may not handle arbitrary HTML.

## What `validate.py` checks

In order, the validator runs through:

1. Every file under `content/*/*.md` parses as YAML frontmatter + markdown body.
2. Every required field above is present and the right type.
3. `id` matches the filename stem.
4. `order` ≥ 100 and unique across the repo.
5. `id` unique across the repo.
6. `tier` is one of `free`, `premium`.
7. `category` is one of the five allowed values.
8. `updatedAt` parses as `YYYY-MM-DD`.
9. Shared fields agree across all locale variants of the same `id`.
10. Every `id` has an `en` variant. Missing `zh-Hans` or `zh-Hant` produces a warning.
11. Each file ends with a trailing newline.

If any step fails, the validator exits non-zero and prints the offending file and field. CI catches this before the article ever reaches GitHub Pages.

## What `build_manifest.py` does with this

The build script walks `content/<locale>/*.md`, parses each frontmatter block, groups by `id`, and emits one entry in `manifest.json` per `id` with all of its locale variants nested under `translations`. The shared fields (`order`, `tier`, etc.) are pulled from any one locale — by the time the build script runs, the validator has already guaranteed they agree.

The output JSON Schema is at `schema/manifest.schema.json`. That schema is the contract with the iOS app; this document is the contract with the author.
