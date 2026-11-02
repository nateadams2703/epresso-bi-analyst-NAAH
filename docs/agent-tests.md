# Agent test log (Guide Section 8)

**Assistant tested:** rules-based assistant (Option B) in the app's Assistant tab. It matches
questions to fixed tools with keyword rules and does not use a language model.

**Status (Nov 2, 2026):** tests 1–5 are planned but not yet run formally. The question,
functions, and expected behavior below come from the design; "Actual result", "Pass / Fail", and
"Revision made" are filled in when each test is run. One defect was found, fixed, and retested
(the "Extra" row below). Attach screenshots of the tool-call log for the numerical tests
(1, 2, 5).

## Agent test table

| Test | Question asked | Function(s) used | Expected result / behavior | Actual result | Pass / Fail | Revision made |
|---|---|---|---|---|---|---|
| 1. Numerical calculation | How much revenue did the website generate in 2028? | `get_total_revenue(year=2028, channel=Website)` | Scope "2028 (from your question); Website (from your question)". Total revenue matches an independent pandas calculation of the same filter. | | | |
| 2. Numerical comparison | Which store experienced the greatest percentage revenue decline? | `get_store_trends()` (2025 → 2029, physical stores) | Names the store with the largest % decline, with its Market tier, its rank within the tier, and its distance from the tier median. Says how many stores declined. If no store had declined, it should say so rather than name a "decliner". | | | |
| 3. Missing information | Which E-Presso store is the most profitable? | `get_data_coverage()`, `get_revenue_breakdown(by=store, physical stores)` | Says profit cannot be calculated (no cost or profit columns), names the measures that exist, and shows the highest-revenue stores labelled "Highest revenue, not profit" with the Market-tier note. Next steps: "No recommendation is supported by this data." | | | |
| 4. Analytical judgment | Does higher customer satisfaction cause higher revenue? | `get_satisfaction_vs_revenue()` | Reports the correlation as an association, not causation; overall and within Market tiers (near zero except a weak, small-sample one among Large stores); Market-tier confounding; the survey reflects active customers only. Next steps: "No recommendation is supported by this data." | | | |
| 5. Updated data | What was Chicago's revenue in 2028? (asked before and after uploading `data/modified/Sales.csv`, then restored) | `get_total_revenue(year=2028, store=SH11)` | The answer after the upload is exactly $1,000 higher; the tool-call log's data line changes from "(original (data/))" to "(uploaded)". This is also the assistant step of the $1,000 test (`docs/1000-test.md`). | | | |
| Extra: fix and retest | How did Orlando do in 2028? | Before the fix: none. After: `get_total_revenue(year=2028, store=Orlando)` | Recognised as a store revenue question; the dispatcher then reports that "Orlando" matches two stores (SH01 – Orlando, FL and SH08 – Orlando, FL) and asks which one. | Before the fix: the unsupported reply ("I can't answer that…"); no tool was run. After the fix (retest, Nov 2): the SH01/SH08 ambiguous-store answer, with one logged `get_total_revenue` call (status error). | **Fail** before the fix → **Pass** after | Router rule for casual store questions, plus logging of failed store lookups in trend questions. See "Defect 1" below. |

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
