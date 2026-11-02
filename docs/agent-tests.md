# Agent test log (Guide Section 8)

**Assistant tested:** rules-based assistant (Option B) in the app's Assistant tab. It matches
questions to fixed tools with keyword rules and does not use a language model.

**Status (Nov 2, 2026):** all five tests were run and **passed** in rules-based mode (Option B,
first table). They were then rerun in **Gemini mode (Option A)**, in the section "Gemini mode
(Option A) tests" below: Gemini answered every question itself, with 0 fallbacks; tests 1, 4, and
5 passed, and tests 2 and 3 were **partial**. Defect 1
was found, fixed, and retested (the "Extra" row). Defect 2 was found in the first live Gemini
call, fixed, and retested on the hosted app (Gemini answered).

**How the five tests were run:** the tests were **automated on the hosted app**
(https://nate-audrey-epresbianalyst.streamlit.app/) on Nov 2, 14:20:29–14:21:14. At Nate's request,
Claude ran a Playwright script (an automated Chrome browser) in its own browser session, after Nate
rebooted the app. The script typed each question into the app's real chat box, used the real file
uploader for test 5, opened each answer's tool-call log, and took a screenshot. Before testing, it
checked that the hosted app was running the current code: the Option B label was shown, and the
sidebar showed the data fingerprint. Screenshots (log expanded, raw JSON expanded for tests 1 and 5)
and the full text of every answer are in `docs/screenshots/agent-tests/formal/`.

**Independent check:** plain pandas on the source CSVs, with none of the app's code, gave
Website 2028 = $6,339,640.00; largest % decline 2025→2029 = SH11 at −66.81% (20 of 20 physical
stores declined); top revenue SH09 $2,527,100.00, SH15 $1,941,550.00, SH11 $1,751,090.00; no
cost or profit columns; satisfaction vs. store-year revenue r = 0.235 (n = 100); Chicago 2028 =
$269,100.00 (original) and $270,100.00 (modified file).

**Test harness note:** a first run at 14:18 got through tests 1–5b with the same results, then
stopped because the script could not find the uploader's delete button. After the reboot the hosted
app runs a newer Streamlit that shows uploads as "chips", with a "Remove Sales.csv" button. The
script was changed to find the button by that name, and all five tests were rerun in one session
(the run recorded here). This was a problem in the test script, not in the app.

## Agent test table

| Test | Question asked | Function(s) used | Expected result / behavior | Actual result | Pass / Fail | Revision made |
|---|---|---|---|---|---|---|
| 1. Numerical calculation | How much revenue did the website generate in 2028? | `get_total_revenue(year=2028, channel=Website)` | Scope "2028 (from your question); Website (from your question)". Total revenue matches an independent pandas calculation of the same filter. | Total revenue: **$6,339,640.00** (scope: 2028 and Website, both "from your question"). One logged call, `get_total_revenue` with `{year: [2028], channel: [Website]}`; raw result `value: 6339640`. Matches the independent pandas check exactly. Screenshot: `test-1-website-revenue-2028.png`. | **Pass** | None needed. |
| 2. Numerical comparison | Which store experienced the greatest percentage revenue decline? | `get_store_trends()` (2025 → 2029, physical stores) | Names the store with the largest % decline, with its Market tier, its rank within the tier, and its distance from the tier median. Says how many stores declined. If no store had declined, it should say so rather than name a "decliner". | "20 of 20 stores compared declined between 2025 and 2029." Largest decline: **SH11 – Chicago, IL (4-Large), $539,740.00 → $179,130.00, −66.81%**; ranks 1 of 3 in 4-Large; 19.54 points below the 4-Large median (−47.27%). Next: SH13 Denver −49.43%, SH06 Columbus −48.99%. Tier medians given; "every store compared declined, so the question is how much, not whether". Matches pandas (SH11, −66.81%, 20 of 20). Screenshot: `test-2-greatest-percentage-decline.png`. | **Pass** | None needed. The "no store declined" case cannot happen in this data (every store declined), so it is covered by an automated test on a small made-up table (`test_trend_answer_when_no_store_declined`). |
| 3. Missing information | Which E-Presso store is the most profitable? | `get_data_coverage()`, `get_revenue_breakdown(by=store, physical stores)` | Says profit cannot be calculated (no cost or profit columns), names the measures that exist, and shows the highest-revenue stores labelled "Highest revenue, not profit" with the Market-tier note. Next steps: "No recommendation is supported by this data." | "Profit cannot be calculated: the loaded data has no cost, expense, price, or profit columns." Lists the measures (Revenue; Satisfaction, Interest). "Highest revenue, not profit": SH09 Phoenix $2,527,100.00, SH15 Baltimore $1,941,550.00, SH11 Chicago $1,751,090.00, all 4-Large; "the top three are the three 4-Large stores … mostly reflects store size"; website excluded unless asked. Next steps: "No recommendation is supported by this data." Two logged calls. Matches pandas. Screenshot: `test-3-most-profitable-store.png`. | **Pass** | None needed. (Asked with the planned wording "Which E-Presso store…"; "Which store is the most profitable?" routes to the same tools.) |
| 4. Analytical judgment | Does higher customer satisfaction cause higher revenue? | `get_satisfaction_vs_revenue()` | Reports the correlation as an association, not causation; overall and within Market tiers (near zero except a weak, small-sample one among Large stores); Market-tier confounding; the survey reflects active customers only. Next steps: "No recommendation is supported by this data." | Correlation **+0.235 (weak), 100 store-years**. Within tiers: near zero in 1-Small (−0.01, n = 30), 2-Minor (−0.09, n = 30), 3-Medium (−0.01, n = 25); weak in 4-Large (+0.18, n = 15, a small sample). Interpretation: "an association, not causation"; Market-tier confounding; active customers only; 5 Website store-years excluded. Next steps: "No recommendation is supported by this data." r matches pandas (0.235, n = 100). Screenshot: `test-4-satisfaction-causes-revenue.png`. | **Pass** | None needed. (The tier wording was refined during development on Oct 30, at Nate's request, so it does not say "about zero everywhere".) |
| 5. Updated data | What was Chicago's revenue in 2028? (asked before and after uploading `data/modified/Sales.csv`, then restored) | `get_total_revenue(year=2028, store=SH11)` | The answer after the upload is exactly $1,000 higher; the tool-call log's data line changes from "(original (data/))" to "(uploaded)". This is also the assistant step of the $1,000 test (`docs/1000-test.md`). | **Before the upload: $269,100.00**, log data line "Sales.csv (original (data/)) · … revenue sum $42,174,440.00". After uploading `data/modified/Sales.csv` (sidebar: "(uploaded) · … $42,175,440.00"): **$270,100.00**, exactly **+$1,000.00**, log data line "Sales.csv (uploaded) · … $42,175,440.00". After removing the upload: back to **$269,100.00**, data line "(original (data/))". Same tool and arguments each time (`store: Chicago → SH11`, `year: 2028`); no code change, no restart. Screenshots: `test-5a-…before-upload.png`, `test-5b-…after-upload.png`, `test-5c-…after-restore.png`. | **Pass** | None needed. This also completes the $1,000 test's "ask the assistant before and after" step (`docs/1000-test.md`). |
| Extra: fix and retest | How did Orlando do in 2028? | Before the fix: none. After: `get_total_revenue(year=2028, store=Orlando)` | Recognised as a store revenue question; the dispatcher then reports that "Orlando" matches two stores (SH01 – Orlando, FL and SH08 – Orlando, FL) and asks which one. | Before the fix: the unsupported reply ("I can't answer that…"); no tool was run. After the fix (retest, Nov 2): the SH01/SH08 ambiguous-store answer, with one logged `get_total_revenue` call (status error). | **Fail** before the fix → **Pass** after | Router rule for casual store questions, plus logging of failed store lookups in trend questions. See "Defect 1" below. |

## Gemini mode (Option A) tests, Nov 2, 2026

**How they were run:** automated on the hosted app, 15:10:13–15:15:01, by Claude's Playwright
session, after the defect 2 retest passed. Before asking, the script checked that Gemini was the
default mode (the key is in Secrets). Questions were asked about 30 seconds apart, to stay under
the free-tier limit of about 15 requests per minute. Test 5 used the real uploader in the same
session. Screenshots (tool-call log open) and every answer's text:
`docs/screenshots/agent-tests/gemini/`.

**How often Gemini answered:** **8 of 8 questions** (9 of 9 including the defect 2 retest).
**0 fallbacks.** Each answer used 3–4 model calls. Every number shown passed the code check (each
must appear in a tool result, a tool argument, or the question), and every number agrees with
the Option B results and the independent pandas check.

| Test | Question | Tools Gemini chose (all via `run_tool`) | Gemini's answer (key points) | Result | Compared with Option B |
|---|---|---|---|---|---|
| 1. Numerical calculation | How much revenue did the website generate in 2028? | `get_total_revenue(year=2028, channel=Website)` | "$6,339,640 in the year 2028"; next step: a category breakdown | **Pass** | Same number |
| 2. Numerical comparison | Which store experienced the greatest percentage revenue decline? | `get_store_trends()` | SH11 Chicago, −66.81% (2025 $539,740 → 2029 $179,130, −$360,610); 4-Large tier; "ranked 1st out of 20 stores overall" | **Partial** | Correct store and numbers, but missing what the expected behavior asks for: SH11's rank within its tier, its distance from the tier median, and that all 20 stores declined. Option B gives all three. |
| 3. Missing information | Which E-Presso store is the most profitable? | `get_data_coverage()`, `get_revenue_breakdown(by=store)` | "does not contain any cost, expense, price, or profit columns"; "High revenue does not guarantee high profitability without cost data"; "No recommendation is supported by this data." | **Partial** | It recognises that profit cannot be calculated (the core of the test). But it lists all 21 stores in ID order, including the website, instead of ranking the highest-revenue stores labelled "not profit". It also does not note that the top stores are the three 4-Large ones. Option B does all of this. |
| 4. Analytical judgment | Does higher customer satisfaction cause higher revenue? | `get_satisfaction_vs_revenue()`, `get_data_coverage()` | Overall +0.235 (100 store-years); each tier's correlation, mean satisfaction, and n; "Association is not causation"; tier confounding; active customers only; 5 Website store-years excluded; "No recommendation…" | **Pass** | Equivalent; Gemini also restates each tier's mean satisfaction and revenue. |
| 5. Updated data | What was Chicago's revenue in 2028? (before upload / after `data/modified/Sales.csv` / after removing it) | `get_total_revenue(store=Chicago → SH11, year=2028)` each time | **$269,100 → $270,100 → $269,100**; log data line "(original (data/))" → **"(uploaded)"** → "(original (data/))" | **Pass** | Same numbers and data lines |
| Extra | How did we do in 2028? | `get_total_revenue(year=2028)`, `get_revenue_breakdown(by=channel, year=2028)`, `get_revenue_breakdown(by=category, year=2028)` | Total $8,969,470; Website $6,339,640 (70.68%); Brick & Mortar $2,629,830 (29.32%); each category's revenue and share | **Pass** | Option B cannot answer this (no store named, no money word): it gives the unsupported reply. Here Gemini does better. |

**Observations:**
- **Strength:** Gemini handles open questions that the keyword rules cannot ("How did we do in
  2028?").
- **Weakness:** for comparisons and profit, Gemini restates the tool results less carefully than
  the rules composer. It misses tier context in test 2, and lists every store unranked, website
  included, in test 3.
- **Minor:** Gemini sometimes adds "No recommendation is supported by this data." to purely
  descriptive questions (test 2, extra), and once added an irrelevant "association is not
  causation" line (test 5b).
- **Possible revision (not made yet):** tighten the Gemini instructions for store comparisons
  (give the rank within the tier, the tier median, and how many stores declined) and for profit
  questions (exclude the website unless asked, rank by revenue, show the top stores labelled
  "highest revenue, not profit", and note the tiers). Then rerun tests 2 and 3 as a fix and
  retest.

## Defect 1: casual store questions get the unsupported reply

| Item | Entry |
|---|---|
| Found by | Nate, testing the Assistant tab locally, Nov 2, 2026 |
| Question | "How did Orlando do in 2028?" |
| Expected behavior | Treated as a revenue question about a store. Orlando has two stores, so the dispatcher should answer that "Orlando" matches SH01 – Orlando, FL and SH08 – Orlando, FL, and ask about one store, as it already does for "What was Orlando's revenue in 2028?". |
| Actual result | The unsupported reply: "I can't answer that with my tools and the loaded data", followed by the list of questions it can answer. The tool-call log showed 0 calls. |
| Cause | The router (`agent.route()`) found the filters correctly (store "Orlando", year 2028), but none of its nine intent rules matched. The "total" rule needs a money word (revenue, sales, earn, …), and "how did … do" contains none. So the question fell through to the unsupported reply before the dispatcher could check the store. The same question with the word "revenue" works. Confirmed by running `agent.route()` on both questions. |
| Fix (Nov 2) | A new intent rule, `performance`, checked **last** so it only catches questions no other rule matched. It covers "how did/does/do/is/was/has/are … do/doing/perform/fare/go" and "how's …", and only when the question names a store. With one year ("How did Orlando do in 2028?"), it calls `get_total_revenue` for that store and year. Otherwise ("How is Chicago doing?"), it gives the store-trend answer focused on the named store(s), with Market-tier context. |
| Related bug fixed at the same time | When a store-trend question named a store that could not be resolved (e.g. "How did Orlando's revenue decline?"), the old code silently dropped it and described the largest decliner instead, with a misleading "store filter not applied" note. It now gives the ambiguous-store answer, and the scope names the focus store(s). |
| Automated tests | 12 new tests in `tests/test_router.py`: seven phrasings route to a revenue tool; "How did Orlando do in 2028?" gives the SH01/SH08 answer; the named-store focus; the related bug; and questions with no store ("How did we do in 2028?") stay unsupported. On the pre-fix code, 10 of the 12 fail (the 2 "stay unsupported" guards pass either way); with the fix all 12 pass, and all 220 tests pass. |
| Follow-up found during the retest | "How did Orlando do in 2028?" showed 1 call in the tool-call log, but "How did Orlando's revenue decline?" showed 0, though both end in the same ambiguous-store error. Cause: the store-trend answer looked up the store itself, outside the dispatcher, so the failed lookup was not logged. Fix: `get_store_trends` takes an optional `store` argument (the store(s) to focus on; they are still ranked among all stores), so the dispatcher checks the name and logs a failed attempt like any other. Tests: the failed lookup is logged with the same error as the total question, and six error answers (ambiguous city, unknown store ID, year not in the data, store decision) all log what was tried; two tool tests for the focus argument. All 229 tests pass. |
| Retest | **Nov 2, 2026.** Nate reported that all questions passed in a retest he describes as Claude running them in the browser on the local app while he reviewed. This session has no record of that run, so to make the record verifiable, Claude re-ran the same questions in a browser after the logging follow-up: Playwright driving Chrome and typing into the app's real chat box, local app on Streamlit 1.66, 14:11:01–14:11:20. The results matched Nate's report, and "How did Orlando's revenue decline?" now also shows one logged call. Screenshots and the full answer text: `docs/screenshots/agent-tests/defect-1-retest/`. |

### Retest results (Nov 2, browser, local app)

| Question | Tool-call log | Result | Pass? |
|---|---|---|---|
| How did Orlando do in 2028? | 1 call (`get_total_revenue`, error) | "Orlando" matches more than one store (SH01 – Orlando, FL, SH08 – Orlando, FL). Ask about one store ID. | ✓ |
| How did Chicago do in 2028? | 1 call | Total revenue: $269,100.00 (SH11, 2028) | ✓ |
| How is Chicago doing? | 1 call | Focus SH11: $539,740.00 (2025) → $179,130.00 (2029), −66.81%; ranks 1 of 3 in 4-Large; 19.54 points below the tier median | ✓ |
| How are the Phoenix and Tempe stores doing? | 1 call | One line each: Tempe (1-Small) −45.77%; Phoenix (4-Large) −11.76% | ✓ |
| Which E-Presso store is the most profitable? | 2 calls | Unchanged: "Profit cannot be calculated…", then "Highest revenue, not profit" | ✓ |
| How did Orlando's revenue decline? | **1 call** (`get_store_trends`, error); 0 before the follow-up | Asks which Orlando store (same message as above) | ✓ |

## Informal local check before the formal tests (Nov 2)

Nate asked the Assistant tab seven questions locally. Six were answered well:
- "Should E-Presso close the Chicago store?"
- a weather question (correctly unsupported)
- "Which store is the most profitable?"
- "Does satisfaction cause revenue?"
- "What was Orlando's revenue in 2028?" (the ambiguous-store answer)
- "Which store had the greatest % decline?"

The seventh found Defect 1. This was an informal check; the formal tests are recorded in the
table above.

## Defect 2: the first live Gemini call failed (role 'tool' rejected)

| Item | Entry |
|---|---|
| Found by | Nate, Nov 2, 2026, after adding the Gemini key to Streamlit Cloud: the first live question in Gemini mode was answered by the rules-based assistant, so he checked the Streamlit Cloud log |
| Question | "How much revenue did the website generate in 2028?" (agent test 1), the first question asked in Gemini mode on the hosted app, at about 14:58 on Nov 2, 2026 (time from the Streamlit Cloud log line) |
| Expected behavior | Gemini requests a tool, our dispatcher runs it, the result goes back to Gemini, and Gemini writes the answer ("Answered by: Gemini (gemini-3.5-flash-lite), function calling"). |
| Actual result | **The fallback worked as designed:** the rules-based assistant answered, labelled with a notice. But the notice gave the wrong reason: "Gemini could not be reached" (`unavailable`). The server log showed the real cause: `Assistant fallback (unavailable): Gemini request failed: 400 INVALID_ARGUMENT. Role 'tool' is not supported. Please use a valid role: SYSTEM, SYSTEM_1, USER, ASSISTANT, DEVELOPER, CONTEXT, USER_CONTEXT, MODEL, USER.` |
| Cause | `llm_client.py` sent our tool results back to Gemini in a message with `role='tool'`. I (Claude) took that role from a summary of the google-genai README while building part (a), and could not check it against the live API, because tests must not use the API. The live API accepts only `user` and `model` here. **Why the tests missed it:** the stand-in for the SDK (`StubSDK`) accepted any role, and the real-types test even asserted `'tool'`, so it locked the bug in. **Second problem:** `llm_client._as_llm_error()` labelled every unrecognised error, including this 400, as "could not be reached", which hid the cause from the app's notice. |
| Fix (Nov 2) | (1) Tool results are sent as `function_response` parts in a `role='user'` turn. (2) A new fallback kind, `bad_request`, for 400 INVALID_ARGUMENT: the notice says "Gemini rejected the request as invalid (400)" and shows the API's short message; an invalid key, also a 400, is still `key_rejected`. (3) `StubSDK`, now in `tests/fakes.py`, rejects any role except `user` and `model` with the same 400 as the live API. The `FakeClient` works above roles (it fakes `send_tool_results` itself), so it could not catch this bug; the request-level stub can. |
| Tests | The round-trip test expects the roles `user, model, user` and a `function_response` part. A new test sends a role `'tool'` message to the stub and gets `bad_request` with the API's message. New fallback and app tests show the notice with the short API message. **With `role='tool'` put back temporarily, the round-trip test fails** (the answer falls back to rules); with the fix it passes. All 294 tests pass with google-genai installed. |
| Retest | **Passed, Nov 2, 2026, 15:08:47**, on the hosted app after the fix was pushed (`23136a9`) and Nate rebooted the app. Automated: Claude's Playwright session typed the same question into the real chat box. Before asking, the script checked that the mode selector was present and that Gemini was selected by default, which means the key is in Secrets; no "no key" warning was shown. **Answered by: "Gemini (gemini-3.5-flash-lite), function calling · 3 model calls"**, with no fallback notice. Tool-call log: 1 call, `get_total_revenue` · ok · 240 rows, arguments `{"year": [2028], "channel": ["Website"]}` → used the same; data: Sales.csv (original (data/)). Scope (built by our code): "2028 (from your question); Website (from your question)". Finding: "The website channel generated $6,339,640 in revenue in 2028", which matches the independent pandas check. Session tally: "Gemini answered 1 of 1". Screenshot and full answer: `docs/screenshots/agent-tests/defect-2-retest/`. |
| Lesson | The fallback did its job (the manager still got a correct, labelled answer), and the server log made the cause visible. But a test double is only as good as the rules it enforces: our stub did not enforce the API's rules about roles. |
