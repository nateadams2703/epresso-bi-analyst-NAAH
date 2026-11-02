# E-Presso BI Analyst (starter)

> Replace this README as you build. Your final version should cover every section below.

## What this application does
_One paragraph for a manager, not a programmer._

## Live app
_URL here. Note that the app may take a moment to wake up._

## How to use it
_Upload files, use filters, ask the assistant. Include the file names and sheets it expects._

## Data model
_Grain of each table, keys, and how they are joined. Include your merge checks._

## Metric definitions
_What "revenue" means here, and anything it does not mean._

## Assistant
The Assistant tab has **two modes**, chosen with a selector:

- **Gemini (Option A), the default when an API key is configured.** A live language model
  (`gemini-3.5-flash-lite`, free tier) chooses among our fixed analysis tools through
  **function calling**. Our code runs every tool through one dispatcher (`agent.run_tool`),
  checks the answer, and builds the scope line itself.
- **Rules-based (Option B).** Keyword rules map a question to the same tools.

**Tools** (`analytics.py`; each returns the same result structure: value, definition, scope,
rows used, caveats):

| Tool | What it calculates |
|---|---|
| `get_total_revenue` | total revenue for chosen years, channels, stores, categories |
| `get_revenue_breakdown` | revenue by one or two of year, month, channel, store, category |
| `get_monthly_share` | each month's share of revenue for the selected period |
| `get_store_trends` | each store's revenue change between two years, with its Market tier |
| `get_satisfaction_vs_revenue` | correlation of satisfaction with store-year revenue, overall and within tiers |
| `get_data_coverage` | what the loaded data contains (e.g. no cost data, so no profit) |
| `data_quality_report` | duplicates and missing values in the Sales table |

**What the assistant may not do:** run code (no code-execution tool, no `eval`/`exec`, no
model-written pandas or SQL), change the data, or state a number that is not in a tool result.
Every Gemini answer is checked: each number must come from a tool result, a tool argument, or
the question. Rounded or formatted versions such as $6.34M are allowed.

**Fallback.** If there is no key, the API fails, a free-tier limit is reached, the model needs
more than 5 model calls or 6 tool calls for one question, or its answer fails a check, the
rules-based assistant answers instead. The answer is labelled with the reason. Every answer says
which mode answered, and the tab shows how often Gemini answered in the current session.
Details: `docs/assistant-gemini.md`.

**Limits:** 15 questions per session. Free tier for `gemini-3.5-flash-lite`, as shown for the
team's key on AI Studio (Nov 2, 2026): about 15 requests per minute, 500 per day, and 250K
input tokens per minute. One question uses up to 5 requests (usually 3). A per-minute or daily
limit returns error 429; the app then falls back and says which limit was reached.

## Validation
_Link to or summarize your Power BI comparison, independent check, and $1,000 test._

## Limitations
_Revenue is not profit. What else can this app not tell a manager?_

- **Gemini free tier:** about 15 requests per minute and 500 per day (`gemini-3.5-flash-lite`,
  Nov 2, 2026), so heavy use falls back to the rules-based assistant. Google can change these
  limits.
- **Data sent to Google:** in Gemini mode, the question and the tool results are sent to Google.
  On the free tier, Google says this content may be used to improve its products. That is
  acceptable here only because E-Presso is fictional course data.

## Files
| File | Purpose |
|---|---|
| `streamlit_app.py` | Screen layout and interaction |
| `analytics.py` | Metrics and analytical functions (no Streamlit code) |
| `agent.py` | Tool registry, dispatcher, rules router, and the Gemini loop with its checks |
| `llm_client.py` | The only code that talks to the Gemini API (google-genai) |
| `tests/` | Tests with hand-checkable answers |
| `requirements.txt` | Packages the hosted app needs |

## Run it
Hosted: deploy from this repository on share.streamlit.io with main file `streamlit_app.py`.

**After pushing changes to a helper file** (`analytics.py`, `data_prep.py`, `agent.py`, `llm_client.py`), **reboot the app** in Streamlit Cloud (Manage app → ⋮ → Reboot app). A push reruns `streamlit_app.py`, but Streamlit Cloud can keep the old helper modules in memory, so the app may fail with errors such as `unexpected keyword argument` until it is rebooted.

Locally (optional): `pip install -r requirements-dev.txt`, then `streamlit run streamlit_app.py`. Run tests with `pytest`.

## Secrets
Never commit API keys. Use Streamlit Secrets (see `.streamlit/secrets.toml.example`).

- **Local:** copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` (git-ignored)
  and put the key in `GEMINI_API_KEY`.
- **Streamlit Community Cloud:** App settings → Secrets → paste the same line.
- **Optional:** `GEMINI_MODEL` to use another model.
- The app reads the key only from `st.secrets`, never shows it, and removes it from error
  messages. Without a key, the assistant uses the rules-based mode.
