# Debate speaker stats

A dataset of competitive BP university tabs (2022 onwards) and a Claude skill that looks up a debater's
speaker averages and Auto-CV scores.

- `skill/debate-speaker-stats/` — the skill (SKILL.md, `scripts/lookup.py`, bundled `data/`). Zip this folder to
  upload it to Claude.
- `build/` — scripts that rebuild the data:
  1. `select_tabs.py`: filters the Auto-CV tournament list (`raw/sheet_list.csv`, exported from the
     "List of Tournaments (Main)" sheet) to `data/tabs.csv`: 2022+, class S-A or above, not Asia/Africa except ABP, no WSDC/NorthAms.
  2. `scrape.py`: caches each tab's Tabbycat API responses in `raw/tabs/` (gitignored). Re-runnable; `--force` refreshes.
  3. `process.py`: builds `skill/debate-speaker-stats/data/` from the cache, scoring Auto-CV achievements.

To refresh: re-export the sheet to `raw/sheet_list.csv`, then run the three scripts from this folder in order,
then re-zip the skill.
