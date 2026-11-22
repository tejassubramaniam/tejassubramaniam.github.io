#!/usr/bin/env python3
"""Look up a debater in the bundled tab dataset.

  python3 lookup.py "Tejas Subramaniam"                 # report
  python3 lookup.py "Matt Toomey" "Matthew Toomey"     # several spellings = one person
  python3 lookup.py --search toomey                    # list names containing a string
  python3 lookup.py "Name" --all-formats               # include non-BP (Australs/AP) speaks in averages
  python3 lookup.py "Name" --json                      # machine-readable output

Standard library only.
"""
import argparse, csv, gzip, json, re, sys, unicodedata
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
GHOST, J_TO_S, S_TO_J = 0.8, 2.4, 4.8
N_SPEAK, N_JUDGE, N_COMBINED, MAX_ADJCORE = 10, 10, 15, 5
SPECIAL = str.maketrans("ĐđÐðŁłØø", "DdDdLlOo")


# ---- name matching (as in the Auto-CV name matcher) ------------------------------------------
def words(name):
    s = re.sub(r'"[^"]*"|\'[^\']*\'|“[^”]*”|‘[^’]*’|\([^)]*\)|\[[^\]]*\]', " ", name or "")
    s = unicodedata.normalize("NFKD", s.translate(SPECIAL))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z ]", " ", s).lower()
    return s.split()


def keys(name):
    w = words(name)
    if not w:
        return set()
    k = {"".join(w)}
    if len(w) > 2:
        k |= {w[0] + w[-1], w[0] + w[1]}
    return k


def matches(tab_name, queries):
    tk = keys(tab_name)
    if not tk:
        return False
    full = "".join(words(tab_name))
    return any(q_full in tk or full in qk for q_full, qk in queries)


# ---- data -------------------------------------------------------------------------------------
def read(name):
    p = DATA / name
    op = gzip.open if name.endswith(".gz") else open
    with op(p, "rt", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load():
    tours = {r["tournament"]: r for r in read("tournaments.csv")}
    return tours, read("speeches.csv.gz"), read("speaking_achievements.csv.gz"), read("judging_achievements.csv.gz")


# ---- Auto-CV score ----------------------------------------------------------------------------
def chain(v):
    out = []
    while v > 1e-9:
        out.append(round(v, 2))
        v -= GHOST
    return out


def pick(items, caps, n):
    """Greedy top-n under per-type caps (a laminar matroid, so greedy is optimal).
    items: (value, tags). caps: tag -> max count."""
    used, chosen = defaultdict(int), []
    for v, tags in sorted(items, key=lambda x: -x[0]):
        if len(chosen) == n:
            break
        if any(used[t] >= caps.get(t, n) for t in tags):
            continue
        for t in tags:
            used[t] += 1
        chosen.append(v)
    return chosen


def cv_scores(sp_points, j_items):
    """sp_points: [points]; j_items: [(points, is_adjcore)]. Returns (speaking, judging, combined)."""
    s_pool = [v for p in sp_points for v in chain(p)]
    j_pool = [(v, a) for p, a in j_items for v in chain(p)]
    speaking = sum(pick([(v, ("S",)) for v in s_pool], {}, N_SPEAK)) / N_SPEAK
    judging = sum(pick([(v, ("J", "A") if a else ("J",)) for v, a in j_pool], {"A": MAX_ADJCORE}, N_JUDGE)) / N_JUDGE
    items = [(v, ("S",)) for v in s_pool]
    items += [(v, ("J", "A") if a else ("J",)) for v, a in j_pool]
    items += [(v - J_TO_S, ("S",)) for v, a in j_pool if v - J_TO_S > 0]
    items += [(v - S_TO_J, ("J",)) for v in s_pool if v - S_TO_J > 0]
    combined = sum(pick(items, {"S": N_SPEAK, "J": N_JUDGE, "A": MAX_ADJCORE}, N_COMBINED)) / N_COMBINED
    return round(speaking, 2), round(judging, 2), round(combined, 2)


# ---- report -----------------------------------------------------------------------------------
def average(rows):
    n = sum(r["n"] for r in rows)
    return round(sum(r["sum"] for r in rows) / n, 2) if n else None


def report(names, all_formats=False):
    tours, speeches, sp_ach, j_ach = load()
    queries = [("".join(words(n)), keys(n)) for n in names]
    hit = {}
    is_match = lambda nm: hit.setdefault(nm, matches(nm, queries))

    per_t = defaultdict(lambda: {"sum": 0.0, "n": 0, "names": set()})
    for r in speeches:
        if is_match(r["name"]):
            k = (r["tournament"], r["team"])
            per_t[k]["sum"] += float(r["speaks"]); per_t[k]["n"] += 1; per_t[k]["names"].add(r["name"])
    comps = []
    for (tn, _), v in per_t.items():
        t = tours[tn]
        comps.append({"tournament": tn, "date": t["date"], "format": t["format"], "class": t["speaking_class"],
                      "rounds": v["n"], "avg": round(v["sum"] / v["n"], 2), "sum": v["sum"], "n": v["n"],
                      "names": sorted(v["names"])})
    comps.sort(key=lambda c: (c["date"], c["tournament"]))
    counted = [c for c in comps if all_formats or c["format"] == "BP"]
    stats = {
        "last_5": average(counted[-5:]), "last_5_n": len(counted[-5:]),
        "last_10": average(counted[-10:]), "last_10_n": len(counted[-10:]),
        "career": average(counted), "career_n": len(counted),
        "formats": "all formats" if all_formats else "BP only",
        "non_bp_tournaments_excluded": 0 if all_formats else len(comps) - len(counted),
    }
    sa = [dict(r, points=float(r["points"])) for r in sp_ach if is_match(r["name"])]
    ja = [dict(r, points=float(r["points"])) for r in j_ach if is_match(r["name"])]
    for a in sa + ja:
        a["date"] = tours[a["tournament"]]["date"]
    s, j, c = cv_scores([a["points"] for a in sa if a["points"] > 0],
                        [(a["points"], a["kind"] == "adjcore") for a in ja if a["points"] > 0])
    matched = sorted({nm for nm, ok in hit.items() if ok})
    return {"query": names, "matched_names": matched, "tournaments": comps, "averages": stats,
            "auto_cv": {"speaking": s, "judging": j, "combined": c},
            "speaking_achievements": sorted(sa, key=lambda a: -a["points"]),
            "judging_achievements": sorted(ja, key=lambda a: -a["points"]),
            "coverage": {"n_tabs": sum(1 for t in tours.values() if t["scraped"] == "True"),
                         "latest_tab": max(t["date"] for t in tours.values() if t["date"])}}


def print_report(r):
    print(f"Query: {', '.join(r['query'])}")
    print(f"Matched tab names: {', '.join(r['matched_names']) or 'none'}")
    if not r["matched_names"]:
        print("No match. Try --search with part of the name."); return
    a = r["averages"]
    print(f"\nSpeaker averages ({a['formats']}; per speech):")
    print(f"  last 5 comps : {a['last_5']}  ({a['last_5_n']} comps)")
    print(f"  last 10 comps: {a['last_10']}  ({a['last_10_n']} comps)")
    print(f"  career       : {a['career']}  ({a['career_n']} comps)")
    if a["non_bp_tournaments_excluded"]:
        print(f"  ({a['non_bp_tournaments_excluded']} non-BP comps not in these averages; use --all-formats)")
    cv = r["auto_cv"]
    print(f"\nAuto-CV (within this dataset): speaking {cv['speaking']}, judging {cv['judging']}, combined {cv['combined']}")
    print("\nTop speaking achievements:")
    for x in r["speaking_achievements"][:10]:
        adj = f" [{x['proam']}]" if x.get("proam") else ""
        print(f"  {x['points']:5.2f}  {x['tournament']} ({x['date'][:7]}): {x['detail']}{adj}")
    if r["judging_achievements"]:
        print("\nTop judging achievements:")
        for x in r["judging_achievements"][:10]:
            print(f"  {x['points']:5.2f}  {x['tournament']} ({x['date'][:7]}): {x['detail']}")
    print("\nTournaments spoken (date, class, rounds, average):")
    for c in r["tournaments"]:
        fmt = "" if c["format"] == "BP" else f" [{c['format']}]"
        print(f"  {c['date']}  {c['tournament']:38s} {c['class']:7s} {c['rounds']:2d} rds  {c['avg']:.2f}{fmt}")
    cov = r["coverage"]
    print(f"\nDataset: {cov['n_tabs']} tabs, latest {cov['latest_tab']}.")


def search(term):
    _, speeches, _, j_ach = load()
    t = "".join(words(term))
    counts = defaultdict(set)
    for r in speeches:
        if t in "".join(words(r["name"])):
            counts[r["name"]].add(r["tournament"])
    for r in j_ach:
        if t in "".join(words(r["name"])):
            counts[r["name"]].add(r["tournament"])
    for nm, ts in sorted(counts.items(), key=lambda x: -len(x[1]))[:40]:
        print(f"{len(ts):3d} tabs  {nm}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--search")
    ap.add_argument("--all-formats", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.search:
        search(a.search); sys.exit()
    if not a.names:
        ap.error("give a name or --search")
    res = report(a.names, a.all_formats)
    if a.json:
        for c in res["tournaments"]:
            c.pop("sum"); c.pop("n")
        print(json.dumps(res, indent=1, default=str))
    else:
        print_report(res)
