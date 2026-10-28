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
_State exactly what you built (live language-model agent, or rules-based assistant). List each tool, what it calculates, and what the assistant is not allowed to do._

## Validation
_Link to or summarize your Power BI comparison, independent check, and $1,000 test._

## Limitations
_Revenue is not profit. What else can this app not tell a manager?_

## Files
| File | Purpose |
|---|---|
| `streamlit_app.py` | Screen layout and interaction |
| `analytics.py` | Metrics and analytical functions (no Streamlit code) |
| `agent.py` | Tool registry, dispatcher, and routers |
| `tests/` | Tests with hand-checkable answers |
| `requirements.txt` | Packages the hosted app needs |

## Run it
Hosted: deploy from this repository on share.streamlit.io with main file `streamlit_app.py`.

**After pushing changes to a helper file** (`analytics.py`, `data_prep.py`, `agent.py`), **reboot the app** in Streamlit Cloud (Manage app → ⋮ → Reboot app). A push reruns `streamlit_app.py`, but Streamlit Cloud can keep the old helper modules in memory, so the app may fail with errors such as `unexpected keyword argument` until it is rebooted.

Locally (optional): `pip install -r requirements-dev.txt`, then `streamlit run streamlit_app.py`. Run tests with `pytest`.

## Secrets
Never commit API keys. Use Streamlit Secrets (see `.streamlit/secrets.toml.example`).
