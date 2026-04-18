#!/usr/bin/env bash
# Sync global skill → repo and push to GitHub.
# Usage: bash scripts/publish.sh ["optional commit message"]
set -e

GLOBAL_SKILL="$HOME/.claude/skills/ai-newsletter-builder"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "→ syncing $GLOBAL_SKILL → $REPO_DIR"

rsync -av --delete \
  --exclude='.git' \
  --exclude='.gitignore' \
  --exclude='README.md' \
  --exclude='scripts/publish.sh' \
  "$GLOBAL_SKILL/" "$REPO_DIR/"

cd "$REPO_DIR"

if git diff --quiet && git diff --cached --quiet; then
  echo "nothing changed, skipping commit"
  exit 0
fi

MSG="${1:-chore: sync from global skill}"
git add -A
git commit -m "$MSG

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>"

GITHUB_TOKEN=$(gh auth token 2>/dev/null || true)
if [ -n "$GITHUB_TOKEN" ]; then
  GITHUB_TOKEN="$GITHUB_TOKEN" git push origin main
else
  git push origin main
fi

echo "✓ published to $(git remote get-url origin)"
