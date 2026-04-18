# Publishing

The site is a plain static bundle under `site/`. Two easy hosts: GitHub Pages and Cloudflare Pages. Don't run publish commands without explicit user confirmation — pushing or deploying is visible to others and hard to reverse.

## GitHub Pages

Two modes. Pick based on whether the user already has a repo for this.

### Mode A: Dedicated repo for the site

Simplest. Put the `site/` contents at the repo root.

```bash
cd <repo>
# Ensure build is current
python .claude/skills/ai-newsletter-builder/scripts/build_index.py --site site

# Move site/ contents up (optional — you can also just use docs/ below)
# Otherwise: enable Pages from the /site folder
git add site
git commit -m "chore(site): initial publish"
git push origin main
```

Then: GitHub → repo → Settings → Pages → Source: `Deploy from a branch`, Branch: `main`, Folder: `/site` (or `/docs` if you moved it). Confirm the URL shown.

### Mode B: Existing repo, publish `docs/`

Rename `site/` → `docs/` and use the built-in Pages support.

```bash
mv site docs
git add docs
git commit -m "chore(site): publish docs/"
git push
```

Then set Pages Source to `main` branch, `/docs` folder.

### Mode C: GitHub Actions

Useful if the user wants CI regeneration. Drop this at `.github/workflows/publish.yml`:

```yaml
name: Publish
on:
  push:
    branches: [main]
permissions:
  pages: write
  id-token: write
  contents: read
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - name: Rebuild index
        run: python .claude/skills/ai-newsletter-builder/scripts/build_index.py --site site
      - uses: actions/upload-pages-artifact@v3
        with: { path: site }
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: github-pages
    steps:
      - uses: actions/deploy-pages@v4
```

Before suggesting this, confirm the user wants CI — it's extra moving parts for a site that's mostly rebuilt locally.

## Cloudflare Pages

1. Push the repo to GitHub (or GitLab).
2. Cloudflare Dashboard → Pages → Create a project → Connect to Git → pick the repo.
3. Build settings:
   - **Framework preset**: None.
   - **Build command**: `python scripts/build_index.py --site site` (omit if no Python at build time; just publish `site/` directly).
   - **Build output directory**: `site`.
   - **Environment variables**: none needed by default.
4. Save and deploy.

Cloudflare Pages rebuilds on every push. If the user edits per-day issues outside of Claude, they still need to commit — the build is just the index regen.

### Custom domain

For either host, after the deploy URL is working, connect a custom domain if the user wants. Tell them the DNS record type and target — don't try to configure it yourself.

## Pre-publish checklist

Run through before the first push:

- [ ] `site/index.html` exists and opens correctly in a browser locally.
- [ ] `site/issues/` has at least one dated file.
- [ ] `site/data/issues.json` has entries matching the HTML files.
- [ ] `site/config/design.md` and `site/assets/style.css` both exist.
- [ ] No secrets in `site/config/` — sources.yaml should reference auth via CLIs (like `gog auth`), not hard-code tokens.
- [ ] `.gitignore` excludes `site/data/raw/` if raw collections shouldn't be published (recommended: raw can be large and contains full-article caches).

Offer to draft a minimal `.gitignore` if the user doesn't have one.

## Common pitfalls

- **Pages shows 404.** Wait a couple of minutes on first deploy. Also check the Pages source folder actually matches where `index.html` sits.
- **CSS missing after deploy.** Paths should all be relative (`assets/style.css`, not `/assets/style.css`). GitHub Pages project sites live under `/<repo>/` and absolute paths break.
- **Old issue still shows up.** Browsers cache the homepage. After a big regeneration, suggest a cache-busting query string in the homepage's own header, or just tell the user to hard-refresh.

## When NOT to publish automatically

If any of the following, pause and confirm with the user:
- Working directory is dirty (untracked changes beyond `site/`).
- Current branch isn't `main` / default.
- The user hasn't explicitly said "publish" (just "generate today's issue" isn't consent to push).

This is a shared-state action. When in doubt, don't push.
