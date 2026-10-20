#!/usr/bin/env bash
# One status run: check the Pi every 2 minutes for ~50 minutes, publishing status.json to the
# status-data branch (one commit, rewritten each time) after every check. See .github/workflows/status.yml.
set -u
end=$(( $(date +%s) + 50 * 60 ))
repo="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
mkdir -p "$(dirname "$STATUS_FILE")"
while :; do
  rm -rf "$(dirname "$STATUS_FILE")/.git"
  if git fetch -q "$repo" status-data 2>/dev/null; then git show FETCH_HEAD:status.json > "$STATUS_FILE" || true; fi
  python3 status/update.py
  (
    cd "$(dirname "$STATUS_FILE")"
    git init -q -b status-data
    git config user.name "status bot"
    git config user.email "status-bot@users.noreply.github.com"
    git add status.json
    git commit -q -m "status $(date -u +%FT%TZ)"
    git push -q --force "$repo" status-data
  ) || echo "publish failed, will retry next round"
  [ "$(date +%s)" -ge "$end" ] && break
  sleep 120
done
