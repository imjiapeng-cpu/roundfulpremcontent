# Drafts

Articles staged here are **not** deployed. `scripts/validate.py` and `scripts/build_manifest.py` only walk `content/` — anything under `drafts/` is invisible to CI.

Use this folder to write a batch of articles ahead of time, then move them into `content/` one at a time on the cadence you want.

## How to publish a drafted article

1. Move all locale files for the same `id` together:

   ```bash
   git mv drafts/en/NNN-your-slug.md       content/en/
   git mv drafts/zh-Hans/NNN-your-slug.md  content/zh-Hans/
   git mv drafts/zh-Hant/NNN-your-slug.md  content/zh-Hant/
   ```

2. (Optional) Bump `updatedAt` to today in **all three** locale files. The shared-field check requires `updatedAt` to match across locales, so update them together.

3. Commit and push:

   ```bash
   git add content/
   git commit -m "Publish article: <title>"
   git push
   ```

CI validates, rebuilds `manifest.json`, and the iOS app picks it up within ~1 hour.

## Schedule for the current batch

| Target publish | ID | Order | Title |
|---|---|---|---|
| 2026-05-26 | `004-calorie-macro-estimation` | 104 | How to Estimate Calories and Macros (and Where to Look It Up) |
| 2026-06-02 | `005-macros-101` | 105 | Macros 101: What They Are and Why Your Body Needs Them |
| 2026-06-09 | `006-macros-deep-dive` | 106 | Macros In Depth: Quality, Timing, Ratios, and Edge Cases |
| 2026-06-16 | `007-streaks-and-realistic-goals` | 107 | Streaks Without Burnout: Setting Goals You'll Actually Keep |

> The `id` prefix and the `order` value are intentionally different — the `id` follows the sequential numbering established by 001/002/003 (the in-bundle articles use 001/002/etc. semantics), while `order` lives in the `100+` range reserved for remote articles. This is the convention.

Update the dates here if the cadence slips. This README is not consumed by any tooling — it's just for you.
