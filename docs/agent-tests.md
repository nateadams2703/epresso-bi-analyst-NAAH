# Agent test log (Guide Section 8)

**Assistant tested:** rules-based assistant (Option B) in the app's Assistant tab. It matches
questions to fixed tools with keyword rules and does not use a language model.

**Status (Nov 2, 2026):** all five tests were run and **passed**, and one defect was found,
fixed, and retested (the "Extra" row).

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
