AI Agent Assignment HELPER
Read this alongside the assignment. If the two differ, this guide controls.

1. Deliverables checklist
Due Sunday, November 15, 2026, 11:59 p.m. One package per Power BI Buddy team.

Done	Deliverable
☐	Live app URL. It opens without a login. Wake it up shortly before you submit.
☐	GitHub repository URL with README and requirements.txt. No passwords or API keys in the repo or its history.
☐	Validation evidence: Power BI vs. app table (five measures), one independent check, and the $1,000 modified-data test.
☐	Agent testing evidence: five required tests, plus one documented fix and retest.
☐	Team reflection (300–500 words).
☐	Team contribution statement.
☐	Commits from every team member in the repository history.
2. Timeline (suggested checkpoints)
Date	Checkpoint	What counts as done
Fri, Oct 23	Checkpoint 0: Hello World	Starter repo copied to your GitHub account, deployed, URL submitted, both teammates have committed once
Sun, Oct 25	Power BI assignment due	Unchanged
Wed, Oct 28	Checkpoint 1: First deployment	Hosted app loads the E-Presso files and shows a data profile; grain statements written (Section 5)
Sun, Nov 1	Checkpoint 2: Functional dashboard	Total revenue reconciled with Power BI; filters and three charts working; $1,000 test attempted
Wed, Nov 4	Checkpoint 3: Analytical functions	At least three tested functions and a dispatcher that runs them and logs each call
Sun, Nov 8	Checkpoint 4: Working assistant	Working assistant (rules-based is fine) with a tool-call log; validation table and $1,000 test complete
Sun, Nov 15	Final submission	Everything in Section 1
Use Nov 8–15 for the language-model upgrade, the five agent tests, your reflection, and defense preparation. I will schedule short individual defense meetings after the due date. Keep your app deployed until grades are posted.

3. Start here: Hello World (Checkpoint 0)
You do not need to know Python for this step.

All teammates create a free GitHub account.
Open the starter repository: https://github.com/jmmcallister/epresso-starter
Click Use this template → Create a new repository and name it something like epresso-bi-analyst. Public is fine because the data is fictional.
Go to share.streamlit.io, sign in with GitHub, choose Create app, select your repository, and set the main file to streamlit_app.py.
Open your URL, upload any small CSV, and confirm you see a preview and a data profile.
Second teammate: edit the app title on GitHub (pencil icon), commit, and watch the app redeploy.
Submit the URL on Canvas.
If deployment fails, read the log in Streamlit Community Cloud. The usual causes are a package missing from requirements.txt or the wrong main file name.

4. Recommended build order
Test each step before starting the next.

Deploy Hello World.
Load the E-Presso files and profile them. Write a grain statement for each table.
Compute one number, total revenue, and reconcile it with Power BI before building anything else.
Add filters and charts. Keep calculations in analytics.py and layout in streamlit_app.py.
Ask your AI assistant for tests that use a tiny made-up table where you can calculate the answer by hand.
Run the $1,000 test before touching the agent.
Build the dispatcher and rules-based assistant, then add the language model as an upgrade.
Commit often. Ask AI to explain your code as well as write it. You will need to explain it in your defense.

5. Data rules
Grain statements
The grain of a table is what one row represents. Most revenue errors come from joining tables at different grains. Before you join anything, complete one row of this table for every source table.

Table	Source file / sheet	One row = ___	Key column(s)	Row count	Contains revenue?
Two columns with the same name are not automatically a valid join key.

Merge checks
Around every merge, record the rows and revenue sum before and after. If the revenue sum changes, the join is duplicating or dropping revenue. Find out why before going further. The starter repo's check_merge() helper reports these numbers.

Merge	Rows before	Rows after	Revenue sum before	Revenue sum after	Explanation

What may change in updated data
Same: file names, sheet names, column names, and data types.
Different: values. Rows may be added or removed, some values may be blank, and a store, product, category, or year may appear or disappear.
Build filter lists (years, stores, categories, channels) from the loaded data. Never type them into your code.
Handle blank values without crashing and report them in the data-quality section.
If a required column is missing, show a plain message naming it instead of a Python error.
Never hardcode a total, a chart value, or an expected answer.
Caching warning
Streamlit can cache results so the app runs faster. If the cache is not tied to the uploaded file's contents, the app keeps showing the old numbers after you upload modified data. This is the most common reason teams fail the updated-data tests. Test by uploading the modified file without restarting the app.

6. The $1,000 modified-data test
Choose one row in the table that holds revenue. Record the table, a row identifier, the date, the store, the sales channel, and the original value.
If revenue is stored in a column, add exactly 1000 to it. If revenue is calculated (for example quantity × price), change the quantity or price on one row so calculated revenue rises by exactly $1,000, and show the arithmetic.
Predict before you upload: the new total, which chart point should change, and what each relevant filter combination should show. Also predict what should not change.
Upload the modified copy through the app. No code edits and no restart.
Record what actually happened. Ask your assistant the same revenue question before and after.
Restore the original data.

7. The analytical assistant
Allowed and not allowed
Allowed: the model (or your rules) chooses among your named functions and supplies parameters from a fixed list of allowed values. Your code runs the function. The model only explains the result.

Not allowed: LangChain's pandas DataFrame agent, PandasAI, code-interpreter features, Python eval() or exec() on anything the model produces, free-form model-written SQL or pandas code, and any function that changes the loaded data. If your AI coding assistant suggests one of these, ask it for function calling with a fixed set of tools instead.

The tool contract
Every analytical function returns the same structure, so the assistant never has to guess what a number means. The numbers below are made up.

{
  'tool': 'get_revenue_by_channel',
  'value': {'Website': 1234567.89, 'Brick-and-mortar': 2345678.90},
  'definition': 'Sum of line-item revenue, grouped by sales channel',
  'scope': {'year': 'All', 'store': 'All'},
  'rows_used': 48210,
  'caveats': ['Revenue is not profit', '3 rows with missing channel were excluded'],
}
Functions take explicit parameters (year, channel, store). They do not read hidden filter state.
Check parameters against values that exist in the loaded data. An unknown store returns an error result, not a guess.
The assistant may only state numbers that appear in a tool result.
Start every answer with its scope, for example "Scope: all stores, all years" or "Scope: Chicago, 2027 (from the sidebar filter)."
Build the dispatcher first
Functions: write and test at least three analytical functions.
Dispatcher and rules-based router: one place that maps a tool name to a function, runs it, and logs the call.
Language-model router: replace the keyword router with a model that picks the tool and writes the explanation.
Option A and Option B
Option A is a live language-model agent using function calling. Option B is a rules-based assistant that routes supported questions to real functions. Both must use the currently loaded data, handle several kinds of questions, identify unsupported requests, change when the data changes, and meet the interface requirements below. Option A can earn up to 15 of 15 agent points. Option B can earn up to 12 of 15. Describe what you built accurately in the app, the README, and your reflection.
Required interface features
A chat box for business questions.
A tool-call log under each answer showing the function name, arguments, and raw result.
Answers organized as Findings (from tool results), Interpretation, and Next steps (or "no recommendation is supported by this data").
A per-session question limit (about 15) with a clear message when it is reached.
A graceful response when the API fails or the quota is used up: a plain message or a switch to the rules-based assistant.
A clear reply to unsupported questions that says what the assistant can answer.
API keys
Keep keys in Streamlit Secrets, and add secret files to .gitignore.
Never paste a key into an AI chat.
If you commit a key by accident, revoke it and create a new one. Deleting the file is not enough because the history still contains it.
Use only the fictional E-Presso data with external model providers.

8. Submission templates
Validation table
Metric	Power BI result	App result	Match? / Explanation
Total revenue (five years)
Website revenue
Brick-and-mortar revenue
Revenue by year
Monthly revenue pattern
Additional measure (your choice)
Also document one independent check (Excel pivot table, short Python script, or another reproducible method): what you calculated, how, and what you got.

Modified-data test record
Item	Entry
Table and row identifier
Date / store / channel of the row
Original value
Modified value
Expected total revenue after change
Actual total revenue after change
Chart that should change, and what you saw
Filter combinations checked (changed / unchanged)
Code changes required?
Original data restored?

Agent test table
Test	Question asked	Function(s) used	Expected result / behavior	Actual result	Pass / Fail	Revision made
1. Numerical calculation
2. Numerical comparison
3. Missing information
4. Analytical judgment
5. Updated data
Extra: fix and retest
Attach screenshots of the tool-call log for the numerical tests. For Test 2, consider what the assistant should say if no store declined.

Team contribution statement
Team member	Main responsibilities	Key calculation or design decision I can explain	Approximate commits

Reflection (300–500 words)
Address: which AI tools you used and for what; the biggest technical or analytical challenge and how you diagnosed it; where the AI helped and where it struggled; what required your own judgment; and whether you would trust this application for real business decisions, and what safeguards it would need.

9. Rubric (70 points)
Component	Full credit looks like	Falls short when
Hosted app (10)	URL opens without a login, loads the supplied data, every feature works on a fresh load, and a modified file works with no code changes.	Features fail, the app depends on your own environment, or it is a static page.
Data handling and accuracy (15)	Grain stated per table; joins verified with before/after counts and no duplicated revenue; metrics calculated from loaded data with nothing hardcoded; data-quality issues found and reported.	Totals are wrong, a discrepancy is unexplained, or values are hardcoded.
Visualizations and usability (10)	At least three clear, labeled charts; filters update every dependent result; metrics, periods, and filters labeled; suitable for a manager.	Fewer than three charts, or filters update only some results.
Validation and updated-data testing (15)	All five comparisons, every discrepancy investigated, a reproducible independent check, and a fully documented $1,000 test with predictions made before upload.	Comparisons without investigation, or the $1,000 test fails or is undocumented.
Analytical assistant (15)	At least three functions using the tool contract; answers come from real calculations; visible tool log; scope stated; profit and causation questions handled well; unsupported questions identified; five tests plus a documented fix and retest; no banned approaches; no exposed keys. (Option B maximum: 12.)	Answers are canned or not tied to calculations, controls are missing, banned approaches are used, or keys are exposed.
Documentation, iteration, defense (5)	Clear README, commits from every teammate showing real iteration, and each member explains key calculations and limitations.	Sparse documentation, a one-person repository, or inability to explain the application.

10. Common problems
Symptom	Likely cause
Deployment fails with ModuleNotFoundError	A package is missing from requirements.txt
App shows old numbers after uploading new data	Cache not tied to the file contents
Revenue total jumped after a merge	The join duplicated rows. Check grain and keys
Assistant works locally but not hosted	Secrets were not added in Streamlit Cloud
App takes a long time to open	It was asleep. Open it once before demos and submission

Working with AI well: build one piece at a time; ask for the smallest change that fixes a problem; ask the AI to explain each function in plain English; and keep notes on the prompts that mattered for your reflection.
