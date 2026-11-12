# Planner

Personal planner for an 8-week consultant rota: week/fortnight focus view with copyable summary, month and year-at-a-glance views, leave booking by clinical session with quick wins and breaks, and structured workout planning (Motion, Home Gym, David Lloyd, Other) with a monthly Motion allowance.

Data is saved in the browser on each device (localStorage). To keep devices in step, turn on **Settings → Sync between devices**, which stores the data in a secret gist on your GitHub account (needs a classic token with the `gist` scope). **Settings → Backup** copies it manually.

Hosted with GitHub Pages: https://mattevans133.github.io/leave-planner/

## Rota sync (CLW)

`.github/workflows/rota.yml` runs `scripts/fetch_rota.py` five times a day. It reads the CLW work and leave calendars and saves a compact `rota.json` into the same secret gist the planner syncs with. The planner then shows theatre allocations, on-calls and rota leave. No rota data is stored in this repo.

Repository secrets needed (Settings → Secrets and variables → Actions): `CLW_WORK_URL`, `CLW_LEAVE_URL`, `GIST_TOKEN` (classic token with the `gist` scope) and `GIST_ID`.

## Structure

`index.html` is the whole app (styles, data model and views in one file). `sw.js` keeps a copy for offline use and always fetches the newest version when online.
