---
id: 001-sample
title: Sample article
summary: A one-line teaser shown in the Insights list. Replace this when you publish a real article.
category: Science
minutesRead: 4
order: 100
tier: free
updatedAt: 2026-04-24
---

# Sample article

This is a placeholder. It exists so the validator, the manifest builder, and the iOS app all have a real article to chew on while the rest of the system is being wired up.

When you publish your first real article, copy this file to `content/en/NNN-your-slug.md`, replace the frontmatter values, and rewrite the body. Don't delete this one until at least one real article ships — keeping a known-good template around makes it easier to debug schema changes later.

## What goes here

A few paragraphs of body text. Standard markdown works — headings, lists, **bold**, *italic*, `inline code`, [links](https://roundful.app), and the usual GFM extensions like tables and task lists.

## A small table

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Must match the filename. |
| `order` | yes | Pick the next free number ≥ 100. |
| `updatedAt` | yes | Bump this when you edit the body. |

That's it. Push to `main`, the build runs, and within an hour the iOS app picks it up.
