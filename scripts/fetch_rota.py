"""Fetch the CLW rota calendars and save a compact copy to the planner's secret gist.

Secrets (set in the repo's Settings -> Secrets and variables -> Actions):
  CLW_WORK_URL   - CLW "work" calendar link
  CLW_LEAVE_URL  - CLW "leave" calendar link
  GIST_TOKEN     - GitHub token with the gist scope (same one the planner uses)
  GIST_ID        - the planner's Gist ID (Setup -> Sync)
Nothing from the calendars is written to this public repo.
"""
import json, os, re, sys, urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LON = ZoneInfo("Europe/London")
SLOT = {"am": "am", "pm": "pm", "eve": "eve", "night": "night"}


def need(name):
    v = os.environ.get(name, "").strip()
    if not v:
        sys.exit(f"Missing secret {name} - add it under Settings -> Secrets and variables -> Actions.")
    return v


def fetch(url):
    url = url.replace("webcal://", "https://")
    req = urllib.request.Request(url, headers={"User-Agent": "leave-planner-rota-sync"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def events(ics):
    text = re.sub(r"\r?\n[ \t]", "", ics)  # unfold continuation lines
    out, cur = [], None
    for line in text.splitlines():
        if line == "BEGIN:VEVENT":
            cur = {}
        elif line == "END:VEVENT":
            if cur is not None:
                out.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            k, v = line.split(":", 1)
            cur[k.split(";")[0].upper()] = v.replace(r"\,", ",").replace(r"\;", ";").replace(r"\n", " ").strip()
    return out


def when(v):
    if re.fullmatch(r"\d{8}", v):  # all-day date
        return datetime.strptime(v, "%Y%m%d").replace(tzinfo=LON)
    if v.endswith("Z"):
        return datetime.strptime(v, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).astimezone(LON)
    return datetime.strptime(v[:15], "%Y%m%dT%H%M%S").replace(tzinfo=LON)


def main():
    work_ics = fetch(need("CLW_WORK_URL"))
    leave_ics = fetch(need("CLW_LEAVE_URL"))

    work = []
    for e in events(work_ics):
        if "DTSTART" not in e:
            continue
        s, en = when(e["DTSTART"]), when(e.get("DTEND", e["DTSTART"]))
        summ = e.get("SUMMARY", "")
        m = re.match(r"\s*(am|pm|eve|night)\s*:\s*(.*)", summ, re.I)
        slot = SLOT[m.group(1).lower()] if m else ""
        label = e.get("LOCATION") or (m.group(2) if m else summ)
        label = re.sub(r"\s*\[[^\]]*\]\s*$", "", label).strip()
        work.append({"d": s.strftime("%Y-%m-%d"), "s": slot, "l": label,
                     "st": s.strftime("%H:%M"), "en": en.strftime("%H:%M"),
                     "h": round((en - s).total_seconds() / 3600, 2)})

    leave = []
    for e in events(leave_ics):
        if "DTSTART" not in e:
            continue
        s, en = when(e["DTSTART"]), when(e.get("DTEND", e["DTSTART"]))
        leave.append({"from": s.strftime("%Y-%m-%d"), "to": en.strftime("%Y-%m-%d"),
                      "st": s.strftime("%H:%M"), "en": en.strftime("%H:%M"),
                      "t": e.get("SUMMARY", "Leave").strip()})

    work.sort(key=lambda x: (x["d"], x["st"]))
    leave.sort(key=lambda x: x["from"])
    data = {"fetched": datetime.now(timezone.utc).isoformat(timespec="minutes"), "work": work, "leave": leave}

    body = json.dumps({"files": {"rota.json": {"content": json.dumps(data, separators=(",", ":"))}}}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/gists/{need('GIST_ID')}", data=body, method="PATCH",
        headers={"Authorization": f"Bearer {need('GIST_TOKEN')}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "User-Agent": "leave-planner-rota-sync"})
    with urllib.request.urlopen(req, timeout=60) as r:
        r.read()
    print(f"Saved {len(work)} work sessions and {len(leave)} leave entries to the gist.")


if __name__ == "__main__":
    main()
