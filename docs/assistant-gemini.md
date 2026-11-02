# Gemini assistant (Option A): design, limits, and fallback

**Status (Nov 2, 2026):** built and tested with a fake Gemini client (no API calls in tests). The
live check with the real key is still to do; it will be recorded here.

## How a question is answered
1. The app sends the question to Gemini (`gemini-3.5-flash-lite`). Gemini also receives a system
   instruction with our rules, and our **tool definitions**: `agent.tool_definitions()`, whose
   allowed values (years, stores, categories, …) come from the loaded data.
2. Gemini can only **ask** for one of our named tools. Automatic function calling is switched off,
   so the google-genai library never runs anything itself.
3. Our dispatcher, `agent.run_tool()`, checks each request and runs the tool on the data loaded
   now. Unknown tools, unexpected arguments, ambiguous cities, and values not in the data become
   error results. Every call, including errors, is logged.
4. The results go back to Gemini. This repeats at most until the limits below.
5. Gemini writes the answer as JSON: `findings`, `interpretation`, `next_steps`.
6. **Our code checks the answer before it is shown:**
   - Every number must come from a tool result, a tool argument, or the question. Rounded or
     formatted versions are allowed: $6.34M for 6,339,640; 0.24 for 0.235; −66.8% for −66.81.
   - "No recommendation is supported by this data." is placed first in Next steps for decision,
     profit, and satisfaction questions.
   - The **scope line is written by our code**, from the arguments each tool actually used. Each
     filter is labelled "from your question", "from the sidebar filter", or "chosen by the model".

Nothing in the app runs code written by the model: there is no code-execution tool, and no
`eval`, `exec`, or `compile` (checked by a test). No tool changes the data.

## Limits
| Limit | Value | Where it is set |
|---|---|---|
| Questions per session | 15 | `MAX_QUESTIONS` in `streamlit_app.py` |
| Model calls per question | 5 (up to 4 rounds of tool requests + 1 written answer; usually 3) | `agent.MAX_MODEL_CALLS` |
| Tool calls per question | 6 | `agent.MAX_TOOL_CALLS` |
| Time per model call | 30 seconds | `llm_client.TIMEOUT_SECONDS` |
| Gemini free tier, `gemini-3.5-flash-lite` | **about 15 requests per minute, 500 per day, 250K input tokens per minute** | Google; shown for the team's key on AI Studio's rate-limit page (checked by Audrey, Nov 2, 2026) |
| Gemini free tier, `gemini-3.6-flash` (not used) | about 5 requests per minute, 20 per day | same |

With up to 5 requests per question, the per-minute limit is reached after about 3 quick
questions. The daily limit allows roughly 100–160 questions. Google can change these limits.

## Fallback to the rules-based assistant
Every answer says which mode answered ("Answered by: Gemini (…)" or "Answered by: rules-based
assistant"). After a fallback, a notice gives the reason. The tab keeps a running count:
"Gemini answered N of M questions sent to it this session; fallbacks: …". Each fallback is also
written to the server log (`epresso.assistant`), with its reason and the question.

| Reason (kind) | When |
|---|---|
| `missing_key` | no `GEMINI_API_KEY` in Streamlit Secrets |
| `key_rejected` | Google rejected the key |
| `quota_minute` | 429: per-minute limit reached ("wait a minute and ask again") |
| `quota_day` | 429: daily limit reached ("it resets the next day") |
| `quota` | 429 without saying which limit |
| `timeout` | no answer within 30 seconds |
| `unavailable` | any other API error, or google-genai not installed |
| `bad_response` | the written answer was not valid JSON in the expected shape |
| `no_tool_called` | Gemini answered without running any tool |
| `no_successful_tool` | every tool Gemini asked for returned an error (e.g. an ambiguous city) |
| `call_limit` | more than 5 model calls or 6 tool calls were needed |
| `unsupported_number` | the answer contained a number not in any tool result (listed in the notice) |

If Gemini falls back on most of the five agent-test questions, that is a defect to fix, not to
hide.

## Setting the key (never in the code, the repo, or an AI chat)
- **Local:** copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`; it is
  git-ignored, as `git check-ignore` confirms. Put the key in `GEMINI_API_KEY`.
- **Streamlit Community Cloud:** App settings → Secrets → paste the same line, then reboot.
- **Optional:** `GEMINI_MODEL` to switch models without changing code.

## Data sent to Google
In Gemini mode, the question, the tool definitions, and the tool results are sent to Google. On
the free tier, Google's pricing page says this content may be used to improve its products. The
Guide allows only fictional data with external model providers; E-Presso is fictional.

## Tests (no quota used)
`tests/test_llm.py` plays back scripted Gemini conversations with a fake client (`tests/fakes.py`):
- realistic answers to the five agent-test questions pass the checks;
- invented numbers, unknown tools, bad arguments, call limits, API failures (including per-minute
  and daily 429s), and badly shaped answers fall back with the right reason;
- `llm_client.py` is tested against google-genai's real response objects, with no network.

`tests/test_app.py` checks the mode selector, the "Answered by" labels, the fallback notices, the
running count, and that the key is never displayed. An automatic fixture stops any app test from
creating a real Gemini client.
