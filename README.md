# Roundful — Premium Content

This repo holds the **additional** Insights articles the Roundful iOS app fetches at runtime. The first five articles are bundled inside the app for a fast first launch; everything else lives here.

You don't need to think about JSON, YAML schemas, or CI to publish. Type markdown, push to `main`, and within an hour the iOS app picks it up.

---

## Publish a new article in 4 steps

1. **Pick the next free `order` number.** Open `manifest.json`, find the highest `order`, and add 1. The first remote article uses `100`, the next `101`, and so on. Anything below `100` is reserved for the bundled in-app articles.

2. **Copy the English placeholder.**

   ```bash
   cp content/en/001-sample.md content/en/NNN-your-slug.md
   ```

   Replace `NNN` with the order number you picked, and `your-slug` with a short kebab-case description (e.g. `102-meal-timing.md`). The filename and the `id:` field inside must match.

3. **Fill in the frontmatter and write the body.** Open the new file and edit the block between the two `---` lines, then write the body underneath. See the [cheat sheet](#frontmatter-cheat-sheet) below.

4. **Repeat for `zh-Hans/` and `zh-Hant/`, then push.**

   ```bash
   cp content/zh-Hans/001-sample.md content/zh-Hans/NNN-your-slug.md
   cp content/zh-Hant/001-sample.md content/zh-Hant/NNN-your-slug.md
   # edit both...
   git add .
   git commit -m "Add article: <title>"
   git push
   ```

   That's it. CI runs the validator, rebuilds `manifest.json`, and deploys to GitHub Pages. If anything is wrong, GitHub emails you and the deploy is blocked until it's fixed.

> `zh-Hans` (Simplified Chinese) and `zh-Hant` (Traditional Chinese) translations are strongly recommended but optional. If you skip either, CI prints a warning but still deploys; the iOS app falls back to English.

---

## Edit an existing article

1. Open the `.md` file under `content/<locale>/`.
2. Edit the body. You can also tweak `title` or `summary` per locale.
3. **Bump `updatedAt` to today's date** (`YYYY-MM-DD`). This is what tells the iOS app to invalidate its per-article cache.
4. `git add . && git commit -m "..." && git push`.

The app will pick up the new version within ~1 hour, or immediately on the user's next launch.

---

## Frontmatter cheat sheet

Every `.md` file starts with this block. All fields are required.

| Field | Example | Notes |
|---|---|---|
| `id` | `102-meal-timing` | Must match the filename without `.md`. Format: `NNN-kebab-case`, where `NNN` is a 3-digit number. |
| `title` | `Meal timing` | What shows up at the top of the article and in the Insights list. |
| `summary` | `Why when you eat matters more than what.` | One-line teaser. Aim for under ~120 chars. Hard cap is 200. |
| `category` | `Science` | One of: `Method`, `Reference`, `Science`, `Mastery`, `Story`. |
| `minutesRead` | `4` | Rough reading time in minutes. |
| `order` | `102` | Sort key. Pick the next free number ≥ 100. Must be unique across the repo. |
| `tier` | `free` | `free` or `premium`. Use `free` to match the existing convention. |
| `updatedAt` | `2026-04-24` | `YYYY-MM-DD`. Bump this every time you edit the body. |

For the full spec (including cross-locale rules and what the validator checks), see [`schema/frontmatter.md`](schema/frontmatter.md).

### Sample block

```markdown
---
id: 102-meal-timing
title: Meal timing
summary: Why when you eat matters more than what.
category: Science
minutesRead: 4
order: 102
tier: free
updatedAt: 2026-04-24
---

# Meal timing

Body starts here. Standard markdown plus GFM tables, task lists, and fenced code.

Use shared images from the repo-root `images/` folder:

![alt text](../../images/example.png)
```

---

## Where it lives once published

- **Working URL right now:** `https://imjiapeng-cpu.github.io/roundfulpremcontent/`
  - Manifest: `https://imjiapeng-cpu.github.io/roundfulpremcontent/manifest.json`
  - Article body example: `https://imjiapeng-cpu.github.io/roundfulpremcontent/content/en/001-sample.md`
- **Custom domain:** to be decided. See the handoff message — three options on the table (subdomain, Cloudflare subpath, or stay on the GitHub URL). When you pick one, point the iOS app at it and update this README.

---

## What CI does for you

Every push triggers `.github/workflows/build.yml`:

1. Runs `python scripts/validate.py`. If anything is wrong with frontmatter, IDs, ordering, or locale pairing, the job fails and the deploy is blocked.
2. Runs `python scripts/build_manifest.py`. If the regenerated `manifest.json` differs from the committed one (because you forgot to rebuild locally — that's fine, you don't have to), the bot commits the new version back to `main`.

When `main` is up-to-date, `.github/workflows/pages.yml` deploys the entire repo to GitHub Pages.

If a push fails, GitHub emails you with a link to the run. Click it; the validator's error message tells you which file and which field broke.

---

## Common mistakes

- **Duplicate `id`** — two articles with the same `id`. The validator rejects this. Pick a fresh `id`.
- **Duplicate `order`** — two articles with the same `order`. Pick the next unused number ≥ 100.
- **Forgot to bump `updatedAt`** — the file goes out, but users on cached copies never see your changes. The validator can't catch this; it's on you.
- **`order` < 100** — reserved for bundled articles. Use ≥ 100.
- **`id` doesn't match filename** — file is `102-meal-timing.md` but frontmatter says `id: 102-meal-time`. The validator catches this.
- **Missing `zh-Hans` or `zh-Hant`** — warning only. CI deploys, app falls back to English. Add the translation when you have it.
- **No trailing newline** — most editors add one automatically. If yours doesn't, hit Enter at the end of the file before saving.
- **Used a category that doesn't exist** — must be one of the five listed above. Adding new categories requires an iOS app change too, so don't.

---

## Run the validator locally (optional)

You don't need to — CI does this for you on every push. But if you want to catch errors before pushing:

```bash
pip install pyyaml
python scripts/validate.py
python scripts/build_manifest.py   # regenerates manifest.json
```

Both scripts work with Python 3.11+. The only dependency is `pyyaml`.

---

## What's where

```
.
├── README.md                 ← this file
├── manifest.json             ← generated, don't hand-edit
├── content/
│   ├── en/                   ← English articles
│   ├── zh-Hans/              ← Simplified Chinese articles
│   └── zh-Hant/              ← Traditional Chinese articles
├── drafts/                   ← staging area, ignored by CI; see drafts/README.md
├── images/                   ← shared images, language-agnostic
├── schema/
│   ├── manifest.schema.json  ← contract with the iOS app
│   └── frontmatter.md        ← contract with the author (you)
├── scripts/
│   ├── validate.py           ← lints content/ and frontmatter
│   └── build_manifest.py     ← regenerates manifest.json
└── .github/workflows/        ← CI: validate, rebuild manifest, deploy
```

If something here is unclear, ping the agent that set this up.
