---
name: debate-speaker-stats
description: Look up a BP debater by name in a bundled dataset of ~225 competitive university debating tabs (2022 onwards, class S-A or above on the Auto-CV tournament list, excluding Asian and African circuits except ABP) and report their speaker average over their last 5 comps, last 10 comps and whole career, plus their Auto-CV speaking, judging and combined scores with the achievements behind them. Use whenever the user gives a debater's name and asks about their speaks, speaker average, CV, Auto CV score, results, breaks or tournament history, or asks to compare debaters.
---

# Debate speaker stats

Answers questions about individual debaters from a bundled, pre-scraped dataset. Everything runs
offline from `data/`; no network access is needed.

## How to use

Run the lookup script with the person's name:

```bash
python3 scripts/lookup.py "Tejas Subramaniam"
```

- **Several spellings of one person:** pass them all, e.g. `lookup.py "Matt Toomey" "Matthew Toomey"`.
  The matcher already ignores case, accents, punctuation, emoji and anything in quotes or brackets
  (nicknames), and for names of three or more words it also tries first+last and first two words.
  It does not know that Matt = Matthew.
- **Not sure of the spelling:** `lookup.py --search toomey` lists matching names and how many tabs each appears on.
- **Include Australs/AP-format speaks in the averages:** add `--all-formats`. By default averages use BP
  tabs only, because 3v3 speaks sit on a lower scale (roughly 77 there ≈ 79 in BP).
- **Structured output:** add `--json`.

Always check the "Matched tab names" line. If it pulls in someone else with a similar name, or misses
a spelling, rerun with the right list of names. Two different people with the same name cannot be
separated.

## What the numbers mean

- **Speaker averages** are per speech over prelim rounds (no ghost/iron or reply speeches),
  over the person's 5 and 10 most recent comps in the dataset, and over all of them. If they have
  fewer comps than that, all are used and the count is shown.
- **Auto-CV scores** follow Andrew Chen's "Auto Debating CVs: How It Works" (v1.8, BP defaults):
  - Up to 3 speaking achievements per tab (furthest outround, team-tab position, speaker-tab position), each
    scored from the tab's speaking class. Tab positions count only in the top half, and only for people who
    spoke at least half the prelims. Pro-am, semi-pro and similar adjustments come from the partner's average,
    and premier regional majors get +0.4.
  - Up to 2 judging achievements per tab (furthest outround judged, furthest chaired), scored from the tab's judging
    class, with the category step-downs for non-open outrounds. Adjcore get a flat Open-GF-minus-0.8 achievement,
    and non-BP judging gets −0.8.
  - Ghost copies (−0.8 each) and cross-category ghosts (judging→speaking −2.4, speaking→judging −4.8) are applied.
    Speaking = mean of the top 10, judging = mean of the top 10 (at most 5 adjcore), and combined = mean of the top 15
    (at most 10 of each kind).
  - Tournament classes (speaking, judging and per-category) come from the Auto-CV tournament list, not recomputed.

## Caveats to tell the user when relevant

- The dataset is a **subset** of the Auto-CV list: only 2022+ tabs of class S-A or higher, outside the Asian and African
  circuits (ABP kept), and no WSDC. So Auto-CV scores here are usually **at or below** the official app's. They're
  lower for anyone whose best results are older, from smaller tournaments, or from the excluded circuits.
- A few tabs could not be read or hide their scores; `data/tournaments.csv` has a `scraped` flag and `n_speeches` per tab.
- Concurrent (gold/silver) outrounds and ESL/EFL subtournament rules beyond the category class are simplified.
- Dates come from each tab's first prelim; tabs with no date use a mid-year placeholder (`date_source` column).

## Data files

- `data/tournaments.csv`: tab, URL, date, format, speaking/judging class, premier-regional-major flag, coverage counts
- `data/speeches.csv.gz`: tournament, name, team, round, speaks
- `data/speaking_achievements.csv.gz` and `data/judging_achievements.csv.gz`: every scored achievement with its base points and adjustments

For questions the script doesn't answer directly (rankings, comparisons, other averages), load these CSVs
with pandas or `csv` and compute from them, using the same name matching (`words`, `keys`, `matches` in `scripts/lookup.py`).
