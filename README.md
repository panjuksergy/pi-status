# pi-status

Public status page for the pi-bots services. It lives in its own public repo on purpose: the bots' code
(pi-bots) stays private, and this page has to work when the Pi is off.

`.github/workflows/status.yml` runs every ~5 minutes, asks the Pi's public `/health` (served by the pi-bots
webhook: which bots answer, whether a deploy is running) and writes `status.json` to the `status-data` branch.
`docs/index.html` (GitHub Pages) reads it and shows it in Ukrainian or English: current state, a 7-day uptime
bar and the history.

Two kinds of downtime, which users see differently:
- **Announced**: open an issue in this repo with the label `incident`; its title is the reason users see
  («Міняємо блок живлення»), the body is optional detail. Close the issue when it's over. Do it from the GitHub
  phone app *before* switching the Pi off. Only issues by the repo owner or collaborators count.
- **Unplanned**: the Pi doesn't answer and there is no open `incident` issue, so the page says the server is
  unavailable, that this was not announced, and that it is being fixed.

If a deploy is running the page says «Йде оновлення»; if one bot's port doesn't answer, «частково».

## Setup (once)

1. Create the repo as **public** (`panjuksergy/pi-status`) and push this folder to `main`.
2. Settings → Pages → Deploy from a branch → `main` / `/docs`. The page is then at
   `https://panjuksergy.github.io/pi-status/`; give users that link (e.g. in each bot's description in @BotFather).
3. Settings → Secrets and variables → Actions → `PI_URL` (a secret or a variable, both work) = the public address of the Pi without a
   trailing slash (the one that serves `/split/...`). It is only the address, which users know anyway.
4. Issues → Labels → create `incident`. Then Actions → status → Run workflow once.

Keep nothing secret here: the repo is public, and `PI_URL` is the only thing it knows about the Pi.
GitHub pauses scheduled workflows in a repo with no activity for 60 days; any push or issue resumes them.
Scheduled runs can be delayed by several minutes; the page shows the time of the last check.
