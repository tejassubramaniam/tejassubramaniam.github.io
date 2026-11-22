"""Turn cached raw tabs (raw/tabs/) into the skill's dataset.

Outputs go to skill/debate-speaker-stats/data/:
  tournaments.csv          one row per tab: date, format, classes, premier-regional-major flag, coverage
  speeches.csv.gz          one row per prelim speech (ghost and reply speeches excluded)
  speaking_achievements.csv.gz  Auto-CV speaking achievements (outround / team tab / speaker tab), already scored
  judging_achievements.csv.gz   Auto-CV judging achievements (furthest judged / chaired / adjcore), already scored

Scoring follows "Auto Debating CVs: How It Works" (v1.8, A. Chen), BP version defaults.
"""
import ast, gzip, json, math, re
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd

RAW = Path("raw/tabs")
DATA = Path("data")
OUT = Path("skill/debate-speaker-stats/data")

# --- Auto-CV tables -------------------------------------------------------------------------
S_CLASSES = ["S-WUDC", "S-AAA+", "S-AAA", "S-AA+", "S-AA", "S-A+", "S-A", "S-B", "S-C", "S-D", "S-E"]
S_TABLE = {  # Win, GF, SF, QF, OF, DOF, QOF
    "S-WUDC": [10.2, 9.4, 8.6, 7.8, 7.0, 6.2, 5.4], "S-AAA+": [9.8, 9.0, 8.2, 7.4, 6.6, 5.8, 5.0],
    "S-AAA": [9.4, 8.6, 7.8, 7.0, 6.2, 5.4, 4.6], "S-AA+": [9.0, 8.2, 7.4, 6.6, 5.8, 5.0, 4.2],
    "S-AA": [8.6, 7.8, 7.0, 6.2, 5.4, 4.6, 3.8], "S-A+": [8.2, 7.4, 6.6, 5.8, 5.0, 4.2, 3.4],
    "S-A": [7.8, 7.0, 6.2, 5.4, 4.6, 3.8, 3.0], "S-B": [7.0, 6.2, 5.4, 4.6, 3.8, 3.0, 2.2],
    "S-C": [6.2, 5.4, 4.6, 3.8, 3.0, 2.2, 1.4], "S-D": [5.4, 4.6, 3.8, 3.0, 2.2, 1.4, 0.6],
    "S-E": [4.6, 3.8, 3.0, 2.2, 1.4, 0.6, 0.0],
}
LEVELS = ["Win", "GF", "SF", "QF", "OF", "DOF", "QOF"]
J_JUDGED = {  # GF, SF, QF, OF, DOF
    "J-WUDC": [9.4, 8.2, 7.4, 6.6, 6.2], "J-AAA+": [9.0, 8.2, 7.4, 6.6, 5.8], "J-AAA": [8.6, 7.8, 7.0, 6.2, 5.4],
    "J-AA+": [8.2, 7.4, 6.6, 5.8, 5.0], "J-AA": [7.8, 7.0, 6.2, 5.4, 4.6], "J-A+": [7.4, 6.6, 5.8, 5.0, 4.2],
    "J-A": [7.0, 6.2, 5.4, 4.6, 3.8], "J-B": [6.2, 5.4, 4.6, 3.8, 3.0], "J-C": [5.4, 4.6, 3.8, 3.0, 2.2],
    "J-D": [4.6, 3.8, 3.0, 2.2, 1.4], "J-E": [3.8, 3.0, 2.2, 1.4, 0.6],
}
J_CHAIRED = {
    "J-WUDC": [10.2, 9.8, 9.0, 8.2, 7.8], "J-AAA+": [9.8, 9.4, 9.0, 8.2, 7.4], "J-AAA": [9.4, 9.0, 8.6, 7.8, 7.0],
    "J-AA+": [9.0, 8.6, 8.2, 7.4, 6.6], "J-AA": [8.6, 8.2, 7.8, 7.0, 6.2], "J-A+": [8.2, 7.8, 7.4, 6.6, 5.8],
    "J-A": [7.8, 7.4, 7.0, 6.2, 5.4], "J-B": [7.0, 6.6, 6.2, 5.4, 4.6], "J-C": [6.2, 5.8, 5.4, 4.6, 3.8],
    "J-D": [5.4, 5.0, 4.6, 3.8, 3.0], "J-E": [4.6, 4.2, 3.8, 3.0, 2.2],
}
J_LEVELS = ["GF", "SF", "QF", "OF", "DOF"]
PRM_BONUS = 0.4
AM_T, AM_S, SEMI_AM_T, SEMI_AM_S, PRO_T, SEMI_PRO_T = 1.6, 0.8, 0.8, 0.4, 0.4, 0.2
ADJCORE_VALUE = -0.8
NON_BP_JUDGING = -0.8
THREE_V_THREE = {"Australs", "AP", "World Schools"}


def load(d, name):
    p = d / f"{name}.json.gz"
    return json.load(gzip.open(p, "rt")) if p.exists() else None


def tab_level(rank, per_team, n_teams_in_final):
    """Map a (team or speaker) tab position to the numerically equally hard outround level index.
    Win = places held by one team; GF = the rest of the final; then each round doubles."""
    win = per_team
    gf = per_team * n_teams_in_final
    if rank <= win:
        return 0
    size, lvl = gf, 1
    while lvl < len(LEVELS):
        if rank <= size:
            return lvl
        size, lvl = size * 2, lvl + 1
    return None


def cat_key(name):
    return re.sub(r"[^a-z]", "", (name or "").lower())


def process_tab(t, d):
    meta = load(d, "done")
    if not meta or not meta.get("ok"):
        return None
    rounds = load(d, "rounds") or []
    prelims = sorted([r for r in rounds if r.get("stage") == "P"], key=lambda r: r["seq"])
    n_prelim = len(prelims)
    prelim_urls = {r["url"]: r for r in prelims}
    three = t.format in THREE_V_THREE
    per_team = 3 if three else 2
    teams_in_final = 2 if three else 4
    teams = {x["url"]: x for x in (load(d, "teams") or [])}
    speakers = {s["url"]: s for s in (load(d, "speakers") or [])}
    for tm in teams.values():  # roster speakers carry their team
        for s in tm.get("speakers", []):
            speakers.setdefault(s["url"], {**s, "team": tm["url"]})
            speakers[s["url"]].setdefault("team", tm["url"])
    pairings = load(d, "pairings") or {}
    dates = sorted(r["starts_at"][:10] for r in prelims if r.get("starts_at"))
    date = dates[0] if dates else (t.date if isinstance(t.date, str) else None)
    info = {"date": date, "date_source": "tab" if dates else ("sheet" if date else "none"), "n_prelims": n_prelim}

    short_to_url = {tm.get("short_name"): u for u, tm in teams.items()}
    # ---- speeches (API, else public speaker-tab page) ----
    speeches = []
    for s in load(d, "speaker_rounds") or []:
        sp = speakers.get(s["speaker"])
        if not sp or not sp.get("name") or sp.get("anonymous"):
            continue
        for rr in s.get("rounds", []):
            if rr["round"] not in prelim_urls:
                continue
            for x in rr.get("speeches", []):
                if x.get("ghost") or not x.get("score") or (x.get("position") or 0) > per_team:
                    continue  # skip ghost (iron) and reply speeches
                speeches.append((sp["name"], sp.get("team"), prelim_urls[rr["round"]]["seq"], float(x["score"])))
    info["speeches_source"] = "api" if speeches else None
    if not speeches:
        page = load(d, "page_speaker_tab")
        if page:
            tb = page[0]; keys = [h["key"] for h in tb["head"]]
            for row in tb["data"]:
                rec = dict(zip(keys, row))
                name = rec.get("name", {}).get("text")
                team = (rec.get("team") or {}).get("text")
                for k in keys:
                    if re.fullmatch(r"R\d+", k):
                        try:
                            v = float(rec[k]["text"])
                        except (ValueError, KeyError, TypeError):
                            continue
                        if v > 0:
                            speeches.append((name, short_to_url.get(team, "page:" + str(team)), int(k[1:]), v))
            if speeches:
                info["speeches_source"] = "page"
    sp_df = pd.DataFrame(speeches, columns=["name", "team", "round", "speaks"]).drop_duplicates(["name", "team", "round"])
    info["n_speeches"] = len(sp_df)

    # ---- per-speaker prelim summary, speaker tab (re-ranked by average), pro-am status ----
    if not n_prelim and len(sp_df):  # page-only tabs: count prelims from the speaker tab columns
        n_prelim = info["n_prelims"] = sp_df["round"].nunique()
    half = n_prelim / 2 if n_prelim else 1
    g = sp_df.groupby(["name", "team"]).speaks.agg(["mean", "size"]).reset_index()
    elig = g[g["size"] >= half].copy()
    elig["spk_rank"] = elig["mean"].rank(ascending=False, method="min")
    n_spk = len(elig)
    team_best = {}
    for team, grp in elig.groupby("team"):
        team_best[team] = sorted(grp["mean"], reverse=True)

    def proam(team, avg):
        """(team adjustment, speaker-tab adjustment, label) for a speaker with this prelim average."""
        others = list(team_best.get(team, []))
        if avg in others:
            others.remove(avg)
        if not others:
            return 0.0, 0.0, ""
        best_other = max(others)
        gap_below, gap_above = best_other - avg, avg - best_other
        if gap_below >= 1.01 - 1e-9:
            return -AM_T, -AM_S, "am"
        if gap_below >= 0.75 - 1e-9:
            return -SEMI_AM_T, -SEMI_AM_S, "semi-am"
        if gap_above >= 1.01 - 1e-9:
            return PRO_T, 0.0, "pro"
        if gap_above >= 0.75 - 1e-9:
            return SEMI_PRO_T, 0.0, "semi-pro"
        return 0.0, 0.0, ""

    # ---- team tab ----
    team_rank = {}
    for x in load(d, "team_standings") or []:
        team_rank[x["team"]] = x["rank"]
    if not team_rank:  # page fallback keyed by short name
        page = load(d, "page_team_tab")
        if page:
            tb = page[0]; keys = [h["key"] for h in tb["head"]]
            for row in tb["data"]:
                rec = dict(zip(keys, row))
                try:
                    rk = int(re.sub(r"\D", "", str(rec["Rk"].get("sort", rec["Rk"]["text"]))))
                except (ValueError, KeyError):
                    continue
                nm = rec.get("team", {}).get("text")
                team_rank[short_to_url.get(nm, "page:" + str(nm))] = rk
    # teams that debated >= half prelims, from the prelim draws
    appear = Counter()
    for r in prelims:
        for p in pairings.get(r["url"]) or []:
            for tm in p.get("teams", []):
                appear[tm["team"]] += 1
    n_teams2 = sum(1 for v in appear.values() if v >= half) or len(team_rank)
    info["n_teams2"] = n_teams2

    # ---- outrounds: furthest round reached per team and category ----
    cats = {c["url"]: c for c in (load(d, "break_categories") or [])}
    sheet_cats = {}
    try:
        raw_info = re.sub(r"np\.(int64|float64)\(([^)]*)\)", r"\2", str(t.category_info))
        sheet_cats = {cat_key(k): v for k, v in ast.literal_eval(raw_info).items()} if raw_info not in ("nan", "{}") else {}
    except (ValueError, SyntaxError):
        sheet_cats = {}

    def cat_class(cat_url):
        """(speaking class, judging step penalty, label) for a break category."""
        c = cats.get(cat_url, {})
        nm = c.get("name", "")
        if c.get("is_general") or cat_key(nm) in ("open", "national"):
            return t.speaking_class, 0.0, "Open"
        sc = sheet_cats.get(cat_key(nm))
        if sc is None:  # categories the Auto-CV list does not recognise (e.g. debate-offs) earn nothing
            return None, None, nm
        highest = sc.get("is_highest_non_open_cat", False)
        jpen = 1.0 if highest else 2.0
        big = re.search(r"WUDC|EUDC|Australs", t.tournament)
        if big and cat_key(nm) == "esl":
            jpen = 0.5
        elif big and cat_key(nm) == "efl":
            jpen = 1.0
        return sc.get("speaking_class", "S-E"), jpen, nm

    elims = defaultdict(list)
    for r in rounds:
        if r.get("stage") == "E" and r.get("break_category"):
            elims[r["break_category"]].append(r)
    ballots = load(d, "ballots") or {}
    team_out = defaultdict(list)   # team -> [(cat_url, level index)]
    judge_out = defaultdict(list)  # adj url -> [(cat_url, depth, chaired)]
    for cu, rs in elims.items():
        rs = sorted(rs, key=lambda r: r["seq"])
        for i, r in enumerate(rs):
            depth = len(rs) - 1 - i  # 0 = final
            for p in pairings.get(r["url"]) or []:
                for tm in p.get("teams", []):
                    team_out[tm["team"]].append((cu, depth + 1))
                adj = p.get("adjudicators") or {}
                if adj.get("chair"):
                    judge_out[adj["chair"]].append((cu, depth, True))
                for pa in adj.get("panellists") or []:
                    judge_out[pa].append((cu, depth, False))
                if depth == 0:  # the final: find the winner from the ballot
                    wins = Counter()
                    for b in ballots.get(p["url"]) or []:
                        if b.get("discarded"):
                            continue
                        for sh in (b.get("result") or {}).get("sheets", []):
                            for tr in sh.get("teams", []):
                                if tr.get("win"):
                                    wins[tr["team"]] += 1
                    if wins:
                        team_out[wins.most_common(1)[0][0]].append((cu, 0))
    info["has_outrounds"] = bool(elims)

    # ---- speaking achievements ----
    prm = 0.4 if str(t.is_premier_regional_major).lower() == "true" else 0.0
    team_members = defaultdict(set)
    for _, row in g.iterrows():
        team_members[row.team].add(row["name"])
    sp_ach = []
    for _, row in g.iterrows():
        name, team, avg, n = row["name"], row.team, row["mean"], row["size"]
        t_adj, s_adj, pa_label = proam(team, avg) if n >= half else (0.0, 0.0, "")
        # speaker tab
        if n >= half:
            rk = elig.loc[(elig.name == name) & (elig.team == team), "spk_rank"].iloc[0]
            lvl = tab_level(rk, per_team, teams_in_final)
            if rk <= n_spk / 2 and lvl is not None:
                base = S_TABLE[t.speaking_class][lvl]
                sp_ach.append((name, "speaker tab", f"speaker tab #{int(rk)} of {n_spk} (= {LEVELS[lvl]})", base, prm, s_adj, pa_label))
        # team tab
        if team in team_rank:
            rk = team_rank[team]
            lvl = tab_level(rk, 1, teams_in_final)
            if rk <= n_teams2 / 2 and lvl is not None:
                base = S_TABLE[t.speaking_class][lvl]
                sp_ach.append((name, "team tab", f"team tab #{rk} of {n_teams2} (= {LEVELS[lvl]})", base, prm, t_adj, pa_label))
        # outrounds: best over categories
        best = None
        for cu, lvl in team_out.get(team, []):
            cls, _, label = cat_class(cu)
            if cls is None or lvl >= len(LEVELS):
                continue
            pts = S_TABLE[cls][lvl]
            if best is None or pts > best[0]:
                best = (pts, f"{label} {'winner' if lvl == 0 else LEVELS[lvl]}")
        if best:
            sp_ach.append((name, "outround", best[1], best[0], prm, t_adj, pa_label))
    sp_ach = pd.DataFrame(sp_ach, columns=["name", "kind", "detail", "base", "prm_bonus", "proam_adj", "proam"])
    sp_ach["points"] = (sp_ach.base + sp_ach.prm_bonus + sp_ach.proam_adj).round(2)

    # ---- judging achievements ----
    adjs = {a["url"]: a for a in (load(d, "adjudicators") or [])}
    jcls = t.judging_class if t.judging_class in J_JUDGED else "J-E"
    fmt_adj = 0.0 if t.format == "BP" else NON_BP_JUDGING
    j_ach = []
    for au, a in adjs.items():
        if not a.get("name") or a.get("anonymous"):
            continue
        if a.get("adj_core"):
            j_ach.append((a["name"], "adjcore", "adjcore", J_JUDGED[jcls][0] + ADJCORE_VALUE, prm, fmt_adj))
            continue
        best_j = best_c = None
        for cu, depth, chaired in judge_out.get(au, []):
            cls, jpen, label = cat_class(cu)
            if jpen is None:
                continue
            for table, is_c in ((J_JUDGED, False), (J_CHAIRED, True)):
                if is_c and not chaired:
                    continue
                col = depth + jpen
                lo, hi = math.floor(col), math.ceil(col)
                row = table[jcls]
                val = lambda c: row[c] if c < len(row) else 0.0
                pts = (val(lo) + val(hi)) / 2
                if pts <= 0:
                    continue
                desc = f"{'chaired' if is_c else 'judged'} {label} {J_LEVELS[depth] if depth < len(J_LEVELS) else 'outround'}"
                if is_c and (best_c is None or pts > best_c[0]):
                    best_c = (pts, desc)
                if not is_c and (best_j is None or pts > best_j[0]):
                    best_j = (pts, desc)
        for b, kind in ((best_j, "judged"), (best_c, "chaired")):
            if b:
                j_ach.append((a["name"], kind, b[1], b[0], prm, fmt_adj))
    j_ach = pd.DataFrame(j_ach, columns=["name", "kind", "detail", "base", "prm_bonus", "format_adj"])
    j_ach["points"] = (j_ach.base + j_ach.prm_bonus + j_ach.format_adj).round(2)
    info["n_adjudicators"] = len(adjs)
    return info, sp_df, sp_ach, j_ach


def main():
    tabs = pd.read_csv(DATA / "tabs.csv")
    sheet = pd.read_csv("raw/sheet_list.csv").set_index("tournament")
    tabs["category_info"] = tabs.tournament.map(sheet["category_info"])
    rows, all_sp, all_sa, all_ja = [], [], [], []
    for t in tabs.itertuples():
        d = RAW / re.sub(r"[^a-z0-9]+", "_", t.tournament.lower()).strip("_")
        res = process_tab(t, d)
        base = {"tournament": t.tournament, "url": t.home_url, "format": t.format, "region": t.region,
                "speaking_class": t.speaking_class, "judging_class": t.judging_class,
                "premier_regional_major": str(t.is_premier_regional_major).lower() == "true"}
        if res is None:
            rows.append({**base, "scraped": False}); continue
        info, sp, sa, ja = res
        rows.append({**base, "scraped": True, **info})
        for df in (sp, sa, ja):
            df.insert(0, "tournament", t.tournament)
        all_sp.append(sp); all_sa.append(sa); all_ja.append(ja)
        print(f"{t.tournament:40s} speeches={info['n_speeches']:5d} spk_ach={len(sa):4d} judge_ach={len(ja):4d}", flush=True)
    tours = pd.DataFrame(rows)
    # tabs with no date anywhere: mid-year placeholder, flagged
    miss = tours.scraped & tours.date.isna()
    tours.loc[miss, "date"] = tours.loc[miss, "tournament"].str.extract(r"(\d{4})$")[0] + "-07-01"
    tours.loc[miss, "date_source"] = "placeholder"
    OUT.mkdir(parents=True, exist_ok=True)
    tours.to_csv(OUT / "tournaments.csv", index=False)
    pd.concat(all_sp).to_csv(OUT / "speeches.csv.gz", index=False)
    pd.concat(all_sa).to_csv(OUT / "speaking_achievements.csv.gz", index=False)
    pd.concat(all_ja).to_csv(OUT / "judging_achievements.csv.gz", index=False)


if __name__ == "__main__":
    main()
