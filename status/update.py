#!/usr/bin/env python3
"""Status checker, run by .github/workflows/status.yml every few minutes (off the Pi, so it still works
when the Pi is down). It asks the Pi's public /health, reads the owner's open "incident" issues for the
reason, and writes status.json (current state + 7 days of history) for docs/index.html.

Environment: PI_URL (public address of the Pi, no trailing slash), STATUS_FILE (read and written),
GITHUB_TOKEN + GITHUB_REPOSITORY (to read incident issues; optional).
States: up, maintenance (a deploy is running), partial (a bot isn't answering), down.
"""
import json
import os
import time
import urllib.error
import urllib.request

PI_URL = os.environ.get("PI_URL", "").rstrip("/")
STATUS_FILE = os.environ.get("STATUS_FILE", "status.json")
KEEP = 7 * 86400
TRUSTED = {"OWNER", "MEMBER", "COLLABORATOR"}   # only these may announce a reason


def fetch_json(url, headers=None, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "pi-bots-status", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read(200_000))


def check_pi():
    """Returns the /health answer, or None when the Pi can't be reached (tried twice)."""
    for attempt in range(2):
        try:
            # ngrok shows a warning page to anything that isn't a browser unless it sees this header.
            data = fetch_json(f"{PI_URL}/health", {"ngrok-skip-browser-warning": "1"})
            if isinstance(data, dict) and data.get("ok") is True:
                return data
        except (urllib.error.URLError, OSError, ValueError):
            pass
        if attempt == 0:
            time.sleep(10)
    return None


def incident():
    """The newest open issue labelled "incident" written by someone who can write to the repo."""
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return None
    try:
        issues = fetch_json(f"https://api.github.com/repos/{repo}/issues?labels=incident&state=open&per_page=10",
                            {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
    except (urllib.error.URLError, OSError, ValueError):
        return None
    for issue in issues:
        if "pull_request" not in issue and issue.get("author_association") in TRUSTED:
            return {"title": issue["title"][:200], "details": (issue.get("body") or "")[:1000],
                    "since": issue["created_at"]}
    return None


def main():
    now = int(time.time())
    health = check_pi() if PI_URL else None
    notice = incident()
    services = (health or {}).get("services", {})
    if health is None:
        state = "down"
    elif health.get("deploying"):
        state = "maintenance"
    elif not all(services.values()):
        state = "partial"
    else:
        state = "up"

    try:
        with open(STATUS_FILE, encoding="utf-8") as f:
            old = json.load(f)
    except (OSError, ValueError):
        old = {}
    history = [h for h in old.get("history", []) if h[0] > now - KEEP] + [[now, state]]
    events = old.get("events", [])
    if not events or events[-1]["state"] != state:
        events.append({"t": now, "state": state, "reason": notice["title"] if notice and state != "up" else None})
    ups = sum(1 for _, s in history if s == "up")

    status = {"checked": now, "state": state, "services": services, "incident": notice,
              # down with a reason = announced by the owner; down without one = the owner doesn't know yet
              "announced": bool(notice), "uptime7d": round(100 * ups / len(history), 2),
              "history": history, "events": events[-30:]}
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, separators=(",", ":"))
    print(state, "| incident:", notice["title"] if notice else None, "| services:", services)


if __name__ == "__main__":
    main()
