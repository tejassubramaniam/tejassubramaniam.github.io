"""Cache raw Tabbycat API responses for every tab in data/tabs.csv under raw/tabs/<key>/.
Re-runnable: tabs whose cache has done.json are skipped unless --force."""
import gzip, json, re, sys, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd, requests

OUT = Path("raw/tabs")
FORCE = "--force" in sys.argv
ONLY = [a for a in sys.argv[1:] if not a.startswith("--")]

def key(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

def get(url, as_json=True):
    for i in range(4):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                return r.json() if as_json else r.text
            if r.status_code in (400, 401, 403, 404, 500):
                return None
        except Exception:
            pass
        time.sleep(2 ** i)
    return None

def page_table(url):
    """Tables embedded in a Tabbycat public page (tablesData), or None."""
    page = get(url, as_json=False)
    if not page:
        return None
    line = next((l for l in page.split("\n") if "tablesData:" in l), None)
    if not line:
        return None
    try:
        return json.loads(line.split("tablesData:", 1)[1].strip().rstrip(","))
    except ValueError:
        return None

def save(d, name, obj):
    with gzip.open(d / f"{name}.json.gz", "wt") as f:
        json.dump(obj, f)

def scrape(t):
    d = OUT / key(t.tournament)
    if (d / "done.json").exists() and not FORCE:
        return t.tournament, "cached"
    d.mkdir(parents=True, exist_ok=True)
    u = urllib.parse.urlparse(t.home_url)
    base = "https://" + u.netloc.removeprefix("www.")
    seg = [p for p in u.path.split("/") if p]
    if seg:
        slug = seg[0]
    else:
        ts = get(f"{base}/api/v1/tournaments") or []
        if len(ts) != 1:
            save(d, "done", {"ok": False, "why": f"{len(ts)} tournaments on site"}); return t.tournament, "no slug"
        slug = ts[0]["url"].rstrip("/").split("/")[-1]
    api = f"{base}/api/v1/tournaments/{slug}"
    rounds = get(f"{api}/rounds")
    if rounds is None:  # no API: keep whatever the public tab pages show
        sp, tm = page_table(f"{base}/{slug}/tab/speaker/"), page_table(f"{base}/{slug}/tab/team/")
        save(d, "page_speaker_tab", sp); save(d, "page_team_tab", tm)
        ok = bool(sp)
        save(d, "done", {"ok": ok, "why": "pages only" if ok else "no API", "base": base, "slug": slug})
        return t.tournament, "pages only" if ok else "no API"
    save(d, "rounds", rounds)
    for name, path in [("teams", "teams"), ("speakers", "speakers"), ("adjudicators", "adjudicators"),
                       ("break_categories", "break-categories"), ("speaker_categories", "speaker-categories"),
                       ("speaker_rounds", "speakers/standings/rounds"), ("team_standings", "teams/standings")]:
        save(d, name, get(f"{api}/{path}"))
    pairings = {}
    for r in rounds:
        pairings[r["url"]] = get(f"{r['url']}/pairings")
    save(d, "pairings", pairings)
    # ballots only for the last elimination round of each break category (to know who won)
    finals = {}
    for r in rounds:
        if r.get("stage") == "E":
            c = r.get("break_category")
            if c not in finals or r["seq"] > finals[c]["seq"]:
                finals[c] = r
    ballots = {}
    for r in finals.values():
        for p in pairings.get(r["url"]) or []:
            ballots[p["url"]] = get(f"{p['url']}/ballots")
    save(d, "ballots", ballots)
    # public-page fallbacks for tabs whose API hides scores
    save(d, "page_speaker_tab", page_table(f"{base}/{slug}/tab/speaker/"))
    save(d, "page_team_tab", page_table(f"{base}/{slug}/tab/team/"))
    save(d, "done", {"ok": True, "base": base, "slug": slug, "time": time.time()})
    return t.tournament, "ok"

if __name__ == "__main__":
    tabs = pd.read_csv("data/tabs.csv")
    if ONLY:
        tabs = tabs[tabs.tournament.isin(ONLY)]
    with ThreadPoolExecutor(10) as ex:
        for name, status in ex.map(scrape, tabs.itertuples()):
            print(status, name, flush=True)
