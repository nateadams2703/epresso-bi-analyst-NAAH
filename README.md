# E-Presso BI Analyst

A web app for E-Presso managers to explore five years of sales (2025–2029), check the data
behind the numbers, and ask business questions in plain English. Built by Nate Adams and
Audrey Haley for the AI Business Intelligence Challenge (ADS midterm).

**Live app:** https://nate-audrey-epresbianalyst.streamlit.app/
The app sleeps when nobody has used it for a while. If you see "Yes, get this app back up!",
click it and wait about a minute. No login is needed.

## What this application does
E-Presso sells coffee products through a website and 20 physical stores. The app loads
E-Presso's sales, store, product, category, and customer-survey files and does three things:

1. **Shows the data and its quality:** the size of each table, its keys, how the tables join,
   and any problems in the data.
2. **Shows a dashboard:** total revenue, the website's share, and the change over time, with
   four charts. Every number follows the filters you choose.
3. **Answers business questions:** an assistant answers by running fixed, tested analysis
   functions on the loaded data and shows exactly which functions it ran.

You can upload an updated version of any file. The app recalculates everything from it with no
code changes and no restart.

## How to use it
**Sidebar**
- **Dashboard filters** (top): Year, Channel, Store, Category. Leave a filter empty to include
  everything. The lists come from the loaded data.
- **Data** (below): upload updated E-Presso files. A file replaces the table with the **same
  file name**; the other tables keep the original data. "Loaded from" shows each table's file,
  its source, its row count, and, for Sales, its revenue sum. Two files can share a name, so
  check this after every upload.

The app expects these files (names, sheets, and columns must stay the same):

| Table | File | Notes |
|---|---|---|
| Stores | `Support_EX_B_Stores.csv` | tab-separated, despite `.csv` |
| Categories | `Categories.csv` | |
| Products | `Products.csv` | |
| Sales | `Sales.csv` | the only table with revenue |
| Survey | `Support_EX_B_Survey.xlsx`, sheet `Survey Results` | headers on row 3 |

**Tabs**
- **Data and profile:** for each table, the source, rows, and columns. Then the data-quality
  notes (Review, Info, Expected), the key checks, the relationship checks, the merge checks, and
  a profile of each table (missing values, data types, preview).
- **Dashboard:**
  - **Tiles:** total revenue, the website's share, and the revenue change from the first to the
    last selected year.
  - **Charts:**
    - revenue by year and channel;
    - share of revenue by month (percent of the selected period);
    - revenue by category and year (one small chart per category, each with its own scale);
    - revenue by store (physical stores only unless you tick "Include the website").
  - Each chart has a "Show data" table with the exact values.
- **Assistant:**
  - **Asking:** type a question. Choose the mode: **Gemini (language model, Option A)** or
    **Rules-based (Option B)**. "Apply the sidebar filters to my questions" (on by default)
    uses the dashboard filters for anything your question does not mention.
  - **Each answer** shows its scope, then Findings, Interpretation, and Next steps, plus a
    tool-call log with every function run, its arguments, and its raw result.
  - **Limit:** 15 questions per session.

**Example questions:** "How much revenue did the website generate in 2028?", "Which store had
the greatest revenue decline?", "Which store is the most profitable?", "Does customer
satisfaction cause higher revenue?", "Should E-Presso close the Chicago store?", "How did we do
in 2028?"

## Data model and grain
Full grain statements and merge checks: `docs/grain-statements.md`.

| Table | One row = | Key | Rows (original data) | Revenue? |
|---|---|---|---|---|
| Stores | one store (20 physical stores + the website, SH00) | `ID` | 21 | No |
| Categories | one product category | `Category ID` | 5 | No |
| Products | one product | `Product ID` | 20 | No |
| Sales | one store's revenue for one product in one month | `Sales ID` | 25,200 | **Yes** |
| Survey | one store's customer survey for one year | `Survey ID` | 105 | No |

**Joins:**
- Sales is joined to Stores (`Store ID` = `ID`), Products, and Categories. All three are
  many-to-one.
- Every join is checked: rows and revenue must be the same before and after. On the original
  data, all joins keep 25,200 rows and $42,174,440, with 0 unmatched rows.
- For satisfaction, revenue is first totalled to one row per store and year, and only then
  joined to the survey (105 → 105 rows). Each survey score is used once.

**Revenue** means the sum of the `Revenue` column on the monthly sales rows. It is not profit:
there are no cost columns. The website is store SH00 with `StoreType` "Website"; the other 20
stores are "Brick & Mortar". Stores belong to a **Market tier** (1-Small, 2-Minor, 3-Medium,
4-Large, 5-Global = the website), so store comparisons are also made within tiers.

**Data-quality notes on the original data:** 4 to review (one malformed phone number, three
possible Location inconsistencies, which may be company sales territories rather than
geography), 1 info (two stores in Orlando, so stores are always identified by ID), and 1 expected
(the website has no address and no in-store survey).

## How the assistant works
Every number comes from one of seven tested analysis functions in `analytics.py`:

| Tool | What it calculates |
|---|---|
| `get_total_revenue` | total revenue for chosen years, channels, stores, categories |
| `get_revenue_breakdown` | revenue by one or two of year, month, channel, store, category |
| `get_monthly_share` | each month's share of revenue for the selected period |
| `get_store_trends` | each store's revenue change between two years, with its Market tier, rank within the tier, and the tier median |
| `get_satisfaction_vs_revenue` | correlation of satisfaction with store-year revenue, overall and within tiers |
| `get_data_coverage` | what the loaded data contains (e.g. no cost data, so no profit) |
| `data_quality_report` | duplicates and missing values in the Sales table |

**One dispatcher runs every tool** (`agent.run_tool`). It accepts only these seven tool names,
checks every argument against the loaded data (an unknown store, or "Orlando", which has two
stores, gets an error message, never a guess), and logs every call.

**Gemini mode (Option A)** is the default when an API key is configured:
1. Gemini (`gemini-3.5-flash-lite`, free tier) chooses which tools to call through **function
   calling**.
2. Our dispatcher runs the tools; Gemini then writes the answer from their results.
3. **Before an answer is shown, our code checks it:**
   - every number must appear in a tool result, a tool argument, or the question (rounded
     forms such as $6.34M are allowed);
   - the scope line is written by our code, from the arguments the tools used;
   - "No recommendation is supported by this data." appears only for decision, profit, and
     judgment questions;
   - correlation and causation remarks appear only when the correlation tool was used.
4. **Fallback:** if there is no key, the API fails, a free-tier limit is reached, Gemini needs
   more than 5 model calls or 6 tool calls, or its answer fails a check, the **rules-based
   assistant answers instead**. The notice says why, and the tab counts how often Gemini
   answered.

**Rules-based mode (Option B):** keyword rules map the question to the same tools, and fixed
templates write the answer.

**Never allowed:** running code written by the model (there is no code-execution tool, and no
`eval` or `exec` anywhere), changing the data, or stating a number that no tool produced.
Details: `docs/assistant-gemini.md`.

## How we validated it
- **Power BI comparison** (`docs/validation-table.md`):
  - **Exact matches:** total revenue $42,174,440.00, Website $27,218,880.00, and
    Brick & Mortar $14,955,560.00 match Power BI's table visuals to the cent.
  - **Chart labels:** revenue by year, the monthly pattern, and Chicago by year match every
    label. Power BI's "Percent of Annual Revenue per Month" actually divides by the total for
    the current filters, not each year's total; our chart is labelled by what it calculates.
- **Independent check:** a short pandas script on the source files, with none of the app's
  code, gives the same figures.
- **$1,000 test** (`docs/1000-test.md`):
  - **Predictions first:** one Chicago sales row was raised by exactly $1,000, and the
    predictions were committed **before** the upload.
  - **First attempt:** the original file was uploaded by mistake, since both files are called
    `Sales.csv`. This led to the row and revenue fingerprint in "Loaded from".
  - **Retest:** every checked prediction matched: total $42,175,440.00; Chicago 2028 $270,100.
    No code changes, no restart, and the original was restored.
- **Agent tests** (`docs/agent-tests.md`): the five required tests, run on the hosted app with
  screenshots of the tool-call log:
  - **Rules-based mode:** all five passed.
  - **Gemini mode:** Gemini answered every question itself. After the Defect 3 fix, all five
    tests and "How did we do in 2028?" passed.
  - **Three defects found, fixed, and retested:**
    - casual questions like "How did Orlando do in 2028?" were not understood;
    - the first live Gemini call was rejected (wrong message role);
    - Gemini answer quality (missing tier context, profit ranking, wording).
- **Automated tests:** 308 tests in `tests/`, most using small made-up tables where the answer
  can be worked out by hand. They include app tests that drive the real page and Gemini tests
  that use a fake Gemini client, so they never use API quota.

## Free-tier limits
- **Gemini free tier** for `gemini-3.5-flash-lite`, as shown for the team's key on Google AI
  Studio (Nov 2, 2026): **about 15 requests per minute, 500 per day, and 250K input tokens per
  minute**. One question uses up to 5 requests (usually 3).
- **When a limit is reached**, the API returns error 429. The app then falls back to the
  rules-based assistant and says whether the per-minute limit ("wait a minute") or the daily
  limit ("resets the next day") was reached.
- **The app** allows 15 questions per session.

## Limitations
- **Revenue is not profit.** There are no costs in the data, so the app cannot say which store
  is most profitable or whether a store should close. It says so, shows the revenue evidence,
  and lists what is missing.
- **Correlation is not causation.** Satisfaction vs. revenue is weak overall (+0.235) and near
  zero within most tiers (100 store-years). The survey covers active customers only, and the
  website has no survey.
- **Trends compare two years** (by default the first and last); the years in between are not
  used.
- **Location values** may be sales territories rather than geography; three are flagged for
  review, not corrected.
- **Rules-based mode** only understands the question types it has rules for. For example, "How
  did we do in 2028?" gets the "I can't answer that" reply in that mode.
- **Gemini mode, known minor issues:**
  - it sometimes writes raw numbers (8969470) instead of formatted ones;
  - it sometimes repeats the scope inside the findings;
  - it may suggest a follow-up question the data cannot answer.

  The numbers themselves are always checked.
- **Data sent to Google:** in Gemini mode, the question and tool results are sent to Google, and
  free-tier content may be used to improve Google's products. This is acceptable only because
  E-Presso is fictional course data.
- **Free-tier limits** (above) mean heavy use falls back to the rules-based assistant.

## Files
| File or folder | Purpose |
|---|---|
| `streamlit_app.py` | The page: sidebar, tabs, charts, assistant chat (layout only) |
| `data_prep.py` | Loading and checking the files, joins with merge checks, data-quality notes |
| `analytics.py` | Every calculation: the seven tools (no Streamlit code) |
| `agent.py` | Tool registry, dispatcher, rules router, and the Gemini loop with its checks |
| `llm_client.py` | The only code that talks to the Gemini API |
| `data/` | The original E-Presso files; `data/modified/` holds the $1,000-test copy |
| `docs/` | Grain statements, validation table, $1,000 test, agent tests, Gemini design, team contributions, Power BI files and screenshots |
| `tests/` | Automated tests |
| `tools/convert_access.py` | One-time conversion of the Access tables to CSV (not used by the app) |
| `requirements.txt` | Packages for the hosted app, pinned to exact versions |

## Run it
**Hosted:** Streamlit Community Cloud, from this repository, main file `streamlit_app.py`. After
pushing a change to `analytics.py`, `data_prep.py`, `agent.py`, or `llm_client.py`, **reboot the
app** (Manage app → ⋮ → Reboot app). Streamlit Cloud can otherwise keep the old version of
those files in memory.

**Locally:** `pip install -r requirements-dev.txt`, then `streamlit run streamlit_app.py`. Run the
tests with `pytest`.

**Package versions** are pinned (e.g. `streamlit==1.66.1`) to the versions the hosted app runs,
so a new release cannot change the app while it is being graded. To upgrade: change a version,
run `pytest`, check the app locally, then push.

## Secrets
Never commit API keys, and never paste them into an AI chat.
- **Local:** copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` (git-ignored)
  and put the key in `GEMINI_API_KEY`.
- **Streamlit Community Cloud:** App settings → Secrets → paste the same line.
- **Optional:** `GEMINI_MODEL` to use another model.

The app reads the key only from Streamlit Secrets, never shows it, and removes it from error
messages. Without a key, the assistant uses the rules-based mode.

## Team
Nate Adams and Audrey Haley. Who did what: `docs/Team-Contributions.md`.
