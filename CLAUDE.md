# E-Presso BI Analyst — Project Context for Claude Code

## Who I am and how to work with me
- I'm Nate, an MSIM grad student at Montana State. I'm a beginner/intermediate Python programmer and I'm using this project to **learn**, not just to finish it. I'm on a Mac.
- **Explain the what and the why** behind code and design choices. Don't over-explain basic syntax I've clearly used, but do explain new libraries, concepts, and non-obvious decisions. Explain each function in plain English — I have to defend this in an individual oral check.
- **Build in small, testable steps.** One component at a time, then run/test it before moving on. Prefer the smallest change that fixes a problem.
- **Check in with me before big or non-trivial changes** (refactors, deleting/overwriting files, restructuring). Small, obviously-correct edits are fine.
- **Never commit or push to git unless I explicitly ask.** When I do ask, show me what will be committed and suggest a clear commit message first. The commit history is graded (real iteration, and commits from **every** teammate), so meaningful, well-described commits matter.
- When a prompt or fix seems important, remind me to note it — I need examples for my reflection.
- If something requires a terminal step I haven't done before (installing a tool, git login, virtual environments), walk me through it and explain what it does.

## Source documents
- `docs/project-guide.md` — the **Project Guide and Addendum ("AI Agent Assignment HELPER")**. **It overrides the assignment page wherever they differ.** Read it before planning any checkpoint. Key sections: 5 (data rules, grain, merge checks, caching), 6 ($1,000 test), 7 (assistant rules + tool contract), 8 (submission templates), 9 (rubric), 10 (common problems).
- `docs/powerbi-walkthrough.md` — the original Power BI assignment: file names, table fields, relationships, the charts we built, and reference figures. Use it to understand the data model and for validation.
- `docs/assignment.md` — the full Canvas assignment page (stages, agent test examples, submission list, rubric points). Use it for detail; the Guide wins on any conflict.
- Starter template this repo was made from: https://github.com/jmmcallister/epresso-starter (includes a `check_merge()` helper — use it). **Read the existing starter code first and build on it** rather than replacing it.

## The assignment (ADS midterm — 70 points, final due Sun Nov 15, 2026, 11:59 pm)
Build a hosted, interactive business intelligence app for **E-Presso** (fictional retail company from our earlier Power BI assignment) using **Python + Streamlit**, stored on **GitHub**, deployed on **Streamlit Community Cloud**. Team project with my Power BI Buddy.

1. **BUILD** — dashboard: load the E-Presso files, profile them, join tables correctly, calculate revenue and other KPIs, ≥3 labeled charts, filters that update every dependent result, data-quality checks, professional layout. Must **accept an uploaded updated dataset and recalculate with no code changes and no restart.**
2. **VALIDATE** — compare app vs. Power BI on: total 5-year revenue, website revenue, brick-and-mortar revenue, revenue by year, monthly pattern, plus one measure of our choice. Investigate every discrepancy. One reproducible independent check. Fully documented **$1,000 test** with predictions written *before* upload (Guide Section 6).
3. **EXTEND** — analytical assistant that answers questions by calling **≥3 named functions** on the currently loaded data.
   - Option A: live LLM with function calling (up to 15/15). Option B: rules-based router (max 12/15).
   - Build order: functions → dispatcher (maps tool name → function, runs it, logs the call) → rules-based router → LLM router upgrade.

## Data rules (Guide Section 5)
- **Grain statement for every source table before any join:** Table | Source file/sheet | One row = ___ | Key column(s) | Row count | Contains revenue?
- **Same column name ≠ valid join key.** Verify keys, data types, and grain.
- **Around every merge, record rows and revenue sum before/after** (use `check_merge()`). If revenue changes, stop and find out why.
- Updated data keeps the same file names, sheet names, column names, and dtypes. Values can change: rows added/removed, blanks, stores/products/categories/years appearing or disappearing.
- **Build filter lists from the loaded data.** Never type years/stores/categories/channels into code.
- Blank values must not crash the app — report them in the data-quality section.
- A missing required column → show a plain message naming it, not a Python traceback.
- **Never hardcode** a total, chart value, or expected answer.
- **Caching warning:** if `st.cache_data` isn't keyed to the uploaded file's *contents*, the app shows stale numbers after upload. This is the #1 reason teams fail the updated-data test. Always test by uploading a modified file without restarting.
- Never modify the original files in `data/`. Modified copies go in `data/modified/`.

## What we know about the data so far
Full background is in `docs/powerbi-walkthrough.md` (the original Power BI assignment). All files are now in `data/`. **Five tables, five files the app loads:**

| App file | Table | Rows × cols | Grain (draft — Nate to review) | Key | Revenue? |
|---|---|---|---|---|---|
| `data/Support_EX_B_Stores.csv` | E-Presso Stores | 21 × 9 | one store/sales outlet (20 physical + website SH00) | `ID` | No |
| `data/Support_EX_B_Survey.xlsx`, sheet `Survey Results` | Survey Results | 105 × 5 | one store × one year's survey | `Survey ID` (= `SH00_25` style) | No |
| `data/Categories.csv` | Categories | 5 × 2 | one product category | `Category ID` (C1–C5) | No |
| `data/Products.csv` | Products | 20 × 2 | one product | `Product ID` (P01–P20) | No |
| `data/Sales.csv` | Sales | 25,200 × 7 | one store × one product × one month | `Sales ID` | **Yes** (`Revenue`) |

**Where the CSVs came from:** `Categories.csv`, `Products.csv`, and `Sales.csv` were converted from `data/source/Support_EX_B_Sales.accdb` (original Access file, kept for reference) with `tools/convert_access.py` (uses the `access-parser` library; values copied exactly, nothing recalculated). Verified: 25,200 rows, revenue sum identical before and after conversion. The script is a one-time tool and is **not** needed by the hosted app, so `access-parser` belongs in `requirements-dev.txt`, not `requirements.txt`.

**Loading gotchas (verified Oct 28):**
- `Support_EX_B_Stores.csv` is **tab-separated** despite `.csv`. The three converted CSVs are normal comma-separated.
- Survey workbook has 3 sheets (`Documentation`, `Survey Results`, `Terms and Definitions`). In `Survey Results`, row 1 is a title, row 2 is blank, **headers are on row 3** → `pd.read_excel(..., sheet_name="Survey Results", header=2)`.
- Survey `Year` is text like `Y2025`, not a number.
- Sales `Date` has **one date per month** (2025-01-31 … 2029-12-31; 60 months), usually the month-end — except Feb 2028, stored as `2028-02-28` even though 2028 is a leap year (420 rows). Group by **month**, never by exact date or an `is_month_end` check. `StoreYear` is `StoreID_YY` (e.g., `SH00_25`) and always matches Store ID + year of Date.
- Sales: 0 missing values, 0 duplicate Sales IDs, no zero/negative revenue. 21 stores × 20 products × 60 months = 25,200 rows exactly — a complete grid.
- Products per category: C1 Beans 5, C2 Syrups 5, C3 Espresso Machines 4, C4 Accessories 3, C5 Frothers 3. Each product belongs to exactly one category.
- Survey: SH00 (Website) **has** 5 survey rows, but `Satisfaction` and `Interest` are blank for all of them (no in-store survey for the website). The other 100 rows are complete. Satisfaction is 0–5 (one decimal); Interest ranges 62–99. Per the `Terms and Definitions` sheet: Satisfaction = "How satisfied were you with your shopping experience at your local E-Presso store?" (0–5); Interest = "How much do you value quality espresso products?" (0–100 scale). These are survey answers from active customers only — a limitation for any satisfaction-vs-revenue conclusion.

**Relationships (Power BI model, confirmed from our .pbix):** Sales.Category ID → Categories (M:1); Sales.Product ID → Products (M:1); Sales.StoreYear → Survey Results.Survey ID (M:1); Survey Results.Store ID → Stores.ID (M:1).
- Power BI reached Stores **through** the survey table. Because SH00 has survey rows (with blank scores), this chain does not drop website revenue: joining Sales→Stores directly on `Store ID` and joining through the survey give the **same** channel totals, with 0 unmatched rows. The direct join is simpler and doesn't depend on the survey file, so prefer it — and record this comparison as a validation/defense point.
- Joining survey onto Sales repeats one satisfaction score across ~240 sales rows per store-year. Never average satisfaction from the joined table; aggregate revenue to store-year first, then attach the survey.

**Our Power BI file:** `docs/powerbi/finishedpowerbi.pbix` (submitted with Audrey). Its stored data matches the source files exactly (same 25,200 sales rows and total). Note: in our model `PostalCode` stayed a **whole number** (the walkthrough said to make it text) — a small data-type difference worth mentioning in validation. Visual-level numbers aren't readable from the file; get them from Power BI itself (teammate's Windows machine) or from the walkthrough figures.

**Independent check results (Python, computed directly from the source files on Oct 28 — for validation ONLY, never hardcode into the app):** total revenue $42,174,440; Website $27,218,880; Brick & Mortar $14,955,560; by year 2025 $7,181,750 · 2026 $8,016,950 · 2027 $8,824,720 · 2028 $8,969,470 · 2029 $9,181,550; November 12.71% and December 25.61% of total. These match the walkthrough's figures (≈$42M, ≈$27M/$15M, $7.2M→$9.2M, 12.71%/25.61%). The app must arrive at these by itself.

**Stores table — `Support_EX_B_Stores.csv`**
- **Despite the `.csv` extension, it's tab-separated.** The starter uploader auto-detected this correctly, but any loader we write must handle it (e.g., `sep="\t"` or auto-detection). Don't assume other `.csv` files are comma-separated either — check each one.
- 21 rows, 9 columns: `ID, City, State, PostalCode, Phone, StoreType, Market, Location, Manager`. 0 duplicate rows.
- Draft grain: **one row = one store (sales outlet)**. Key: `ID` (SH00–SH20). No revenue.
- **`StoreType` defines the sales channel:** `SH00` = `Website`; SH01–SH20 = `Brick & Mortar`. This is how website vs. brick-and-mortar revenue will be split for validation.
- Data-quality notes to report in the app:
  - SH00 (Website) has blank City/State/PostalCode — expected for a non-physical store, so explain it rather than flag it as an error.
  - `PostalCode` is being read as a **number**; ZIP codes are labels and should be read as text (leading zeros would be lost otherwise).
  - SH11 (Chicago) phone is malformed: `773) 555-4766` (missing opening parenthesis).
  - SH07 (Flushing, NY) has `Location = Southwest`, which looks inconsistent with New York.
  - Two different stores are in Orlando, FL (SH01, SH08) — city is not unique; always use `ID` as the key.
- SH01 (Orlando) is `Location = South` while SH08 (Orlando) is `Location = East` — second Location inconsistency.
- SH04 (Greenville, NC) is `Location = East` while SH19 (Raleigh, NC) is `Location = South` — found by `data_prep.data_quality_notes()`.
- All Location findings are reported as **"Possible Location inconsistency to review"**, never errors: E-Presso's Location values may be company sales territories rather than standard geography (Nate's decision, Oct 28).
- `PostalCode` loads as a decimal (`32822.0`) because SH00's blank forces pandas to use floats — read it as text (done in `data_prep.TABLE_SPECS`).

## Assistant rules (Guide Section 7)
- **Banned:** LangChain pandas DataFrame agent, PandasAI, code-interpreter features, `eval()`/`exec()` on model output, model-written SQL or pandas, any function that changes the loaded data.
- Functions take **explicit parameters** (year, channel, store) — never hidden filter state. Validate parameters against values in the loaded data; unknown values return an error result, not a guess.
- **Every analytical function returns the tool contract:**
  ```python
  {
    'tool': 'get_revenue_by_channel',
    'value': {...},
    'definition': 'Sum of line-item revenue, grouped by sales channel',
    'scope': {'year': 'All', 'store': 'All'},
    'rows_used': 48210,
    'caveats': ['Revenue is not profit', '3 rows with missing channel were excluded'],
  }
  ```
- The assistant may only state numbers that appear in a tool result.
- Every answer starts with its **scope** (e.g., "Scope: all stores, all years") and is organized as **Findings / Interpretation / Next steps** (or "no recommendation is supported by this data").
- Required UI: chat box; tool-call log under each answer (function, arguments, raw result); per-session limit (~15 questions) with a clear message; graceful fallback if API fails or quota runs out; clear reply to unsupported questions listing what it *can* answer.
- **API keys:** Streamlit Secrets only; secret files in `.gitignore`; never in code, chat, or git history. If one is committed, it must be revoked.

## Planned architecture
The starter app already has three tabs — **Data and profile**, **Dashboard**, **Assistant** — matching the three stages. Fill these in rather than restructuring.

| File | Purpose |
|---|---|
| `streamlit_app.py` | Layout/UI only: upload/load, filters, KPIs, charts, chat page |
| `data_prep.py` | Loading, cleaning, type fixes, verified joins, grain/merge checks, data-quality report |
| `analytics.py` | Pure functions → tool-contract dicts. **Single source of truth for every number** |
| `agent.py` | Dispatcher, call log, rules-based router, LLM router, rate limit, error handling |
| `tests/` | Tests using tiny made-up tables where the answer can be calculated by hand |
| `requirements.txt` | Every package the hosted app needs (missing package = #1 deploy failure) |
| `README.md` | What it does, file layout, how to use, table relationships, limitations, Option A/B stated accurately |
| `docs/` | Project Guide, grain statements, merge-check log, validation table, $1,000 test record, agent test log |

Key idea: **the dashboard and the assistant call the same `analytics.py` functions**, so validating the functions validates both. Before creating new files, check what the starter already provides and confirm the plan with me.

## Deploying
- **After pushing a change to a helper file (`analytics.py`, `data_prep.py`, `agent.py`), reboot the app** in Streamlit Cloud (Manage app → ⋮ → Reboot app). On a push, Streamlit Cloud reruns `streamlit_app.py` but can keep the *old* helper modules in memory, so new app code calls old functions. This happened on Oct 28: every table failed with `load_table() got an unexpected keyword argument 'dtype'` until a reboot.
- After every deploy, open the live app and check for red error boxes before calling a step done. Include the reboot step in every live-app checklist.

## Checkpoints (Guide Section 2 — suggested pacing only)
| Date | Checkpoint | Done means |
|---|---|---|
| Fri Oct 23 | 0 — Hello World | Starter repo copied, deployed, URL submitted, both teammates committed once |
| Wed Oct 28 | 1 — First deployment | Hosted app loads the E-Presso files, shows a data profile; grain statements written |
| Sun Nov 1 | 2 — Functional dashboard | Total revenue reconciled with Power BI; filters + 3 charts working; $1,000 test attempted |
| Wed Nov 4 | 3 — Analytical functions | ≥3 tested functions + dispatcher that runs and logs each call |
| Sun Nov 8 | 4 — Working assistant | Assistant (rules-based OK) with tool-call log; validation table + $1,000 test complete |
| Sun Nov 15 | Final | Everything in Guide Section 1 |

Nov 8–15: LLM upgrade, five agent tests + fix/retest, reflection, defense prep.

## Current status
- Checkpoints are suggested pacing only, not graded or submitted. The only real deadline is the final submission on Nov 15.
- GitHub repo: `nateadams2703/epresso-bi-analyst-NAAH` (branch `main`), cloned to `~/Documents/epresso-bi-analyst-NAAH`. Git login works (fine-grained token in the macOS keychain), so `git push origin main` works without prompting.
- **Both teammates have commits:** Audrey's first commit (`d011f3b`, Oct 29) reviewed `docs/grain-statements.md`. She will fix that file's "Status: draft for review" line as her second commit, so don't change it.
- Decisions (Oct 28–29): the app loads the original files from `data/` by default and an upload replaces a table; filters live at the top of the sidebar; Location issues are "possible inconsistencies to review" (may be sales territories); the store chart shows physical stores by default with an "Include the website" checkbox; category trends are small multiples with their own vertical scales.
- **Checkpoint 0 done (Oct 28):** starter app deployed on Streamlit Community Cloud.
- **Checkpoint 1 done (Oct 28):** grain statements written and reviewed; `data_prep.py` loads and checks all five tables; hosted app shows the data profile. The live app needed a reboot after the push (see Deploying).
- **Checkpoint 2 done (Oct 29):**
  - Joins: `build_sales_model()` joins Sales → Stores/Products/Categories through `check_merge()`; 25,200 rows and $42,174,440 before and after every join (merge-check log in `docs/grain-statements.md`).
  - Reconciled with Power BI (`docs/validation-table.md`): total, Website, and Brick & Mortar match exact Power BI table values to the cent; years, months (company and Chicago), and Chicago by year match every Power BI label. Power BI's "Percent of Annual Revenue per Month" really divides by the grand total for the current filters; our chart is labelled honestly.
  - Dashboard: sidebar filters (year, channel, store, category) built from the data; KPI tiles (total, Website share, revenue change); four charts (year × channel, monthly share, category × year small multiples, store). Every result calls `analytics.py` with the same selection.
  - Analytics functions with the tool contract: `get_total_revenue`, `get_revenue_breakdown`, `get_monthly_share`, `get_revenue_change`, `store_labels`. Fixed a starter bug in `_apply_filters()` (it validated against already-filtered rows).
  - Tests: 70 passing, including `tests/test_app.py` (AppTest: filters drive every result, store checkbox, stale filters, dollar-sign escaping).
  - **$1,000 test done on the hosted app** (`docs/1000-test.md`, screenshots in `docs/screenshots/1000-test/`): `data/modified/Sales.csv` changes S1120280601 (SH11 Chicago, 2028-06-30) 590.0 → 1590.0. Predictions were committed and pushed first (`a67af25`; never edit Part 2). The first attempt uploaded the original `Sales.csv` by mistake (same file name), so the total didn't move; the retry gave $42,175,440.00, and every recorded result matched the predictions. Some predictions (e.g. Brick & Mortar total, Beans 2028, Category = Beans filter) have no recorded value and are marked "Not confirmed". Restored to $42,174,440.00; no code changes, no restart.
  - **Fix from the first attempt:** `data_prep.loaded_summary()` shows each table's rows and, for Sales, its revenue sum in the sidebar's "Loaded from" and in "Loaded tables", so two files with the same name can be told apart. Retested locally through the real upload widget (Streamlit 1.66); **hosted retest still to record** in `docs/1000-test.md` after a reboot.
  - The assistant step of the $1,000 test (same question before and after) waits for Checkpoint 3.
- Streamlit Cloud installs the **newest** package versions (pandas 3.x, Streamlit 1.66, Plotly 7 on Oct 28–29), newer than on Nate's Mac. Run the tests in a clean environment before relying on version-specific behaviour.
- Streamlit renders `$...$` in Markdown text as math: wrap any displayed text that can contain dollar signs in `md()` in `streamlit_app.py`. A test checks this.
- Known small gap: the uploader accepts `.xls`, which would need `xlrd` (not installed); no expected file is `.xls`, so it only triggers the "name doesn't match" message.
- The assistant still runs the starter tools on the Sales table only (until Checkpoint 3).
- **Next up:** reboot the hosted app and record the fingerprint retest, then Checkpoint 3: at least three tested functions in the dispatcher (the four revenue functions above are candidates), replacing the starter's generic `get_total`/`group_total`.
- Update this section as checkpoints are completed.
