"""Filter the Auto-CV tournament list: 2022+, class S-A or above, not Africa/Asia (ABP kept), no WSDC/NorthAms
(schools / different format). Writes data/tabs.csv."""
import re, pandas as pd
OK = ["S-WUDC", "S-AAA+", "S-AAA", "S-AA+", "S-AA", "S-A+", "S-A"]
df = pd.read_csv("raw/sheet_list.csv")
abp = df.tournament.str.contains(r"\bABP\b") & ~df.tournament.str.contains("Pre-ABP|ABP Fundraiser|ABPDC")
sel = df[(df.year >= 2022) & df.speaking_class.isin(OK) & (~df.region.isin(["Africa", "Asia"]) | abp)]
sel = sel[~sel.tournament.str.match(r"WSDC|NorthAms")]
cols = ["tournament", "home_url", "year", "date", "format", "region", "country", "speaking_class", "judging_class",
        "is_premier_regional_major", "no_wbr_speakers", "no_79.11plus_speakers", "no_teams2", "no_wbr_adjs", "no_adjs2"]
sel[cols].sort_values("tournament").to_csv("data/tabs.csv", index=False)
print(len(sel), "tabs;", (sel.year == 2026).sum(), "from 2026")
