# Build an AI Powered Analytics Application — The AI Business Intelligence Challenge
(Canvas assignment page, copied Oct 28, 2026. Where this differs from `project-guide.md`, the Guide controls.)

Due: Sun Nov 15, 2026 11:59pm · 70 points

**Final Deliverable:** A live, hosted business intelligence application, GitHub repository, validated analytical results, functioning analytical assistant, and brief project defense.

**Read this first:** The Project Guide and Addendum adds checkpoints, clarifies the data-update and $1,000 tests, sets rules for the analytical assistant, and provides submission templates and rubric descriptors. If it differs from this page, the Guide controls.

## Your Mission
You have already worked with Excel, data preparation, SQL concepts, statistical analysis, data visualization, and business intelligence. Now it's time to put those skills together in a new way.

Your challenge is to use artificial intelligence as a development partner to create a functioning business intelligence application. Rather than simply asking AI to answer questions or create charts, you will use AI to help you engineer software that other people can actually use.

You will build an interactive analytical application for E-Presso, the same fictional business you analyzed in your Power BI assignment. Your application must allow a user to explore business data, investigate performance, interact with visualizations, and ask questions of an analytical assistant.

You will use Python and Streamlit to create the application, GitHub to store your code, and Streamlit Community Cloud (or another approved hosting platform) to publish it. Your finished product must be accessible through a working URL.

I should be able to open your application, interact with the dashboard, upload or modify data, ask your analytical assistant questions, and evaluate the results. And you must be prepared to defend what happens behind the interface.

## An Important Note About This Assignment
Some of you have never created a website, used GitHub, written Python, or built an AI agent. That is okay. You are not expected to arrive with expertise in every technology involved. You are expected to research, experiment, troubleshoot, test, revise, and learn.

You may use AI throughout the project to help with coding, debugging, application design, documentation, and analytical development. However:

**AI can write code. You are responsible for what that code does.**

You must understand your application's analytical approach, verify its calculations, explain its assumptions, and demonstrate that its outputs are reliable. This project is intentionally challenging and iterative. Your first version is not expected to be your final version.

## The Three Stages

### Stage 1 — BUILD: Create a Hosted, Dynamic Dashboard
Develop an interactive business intelligence application using the E-Presso datasets. Your application should function as a small, reusable business intelligence product; not merely a static report or webpage.

**Minimum Dashboard Requirements.** Your application must:
- Load the supplied E-Presso data and display useful information about the datasets.
- Prepare and combine the data appropriately, documenting relevant table relationships.
- Calculate total revenue and other meaningful business performance metrics.
- Include at least three meaningful visualizations.
- Include interactive filters, such as year, product category, store, or sales channel.
- Recalculate relevant results when a filter changes.
- Accept an updated version of the dataset and recalculate results without modifying the application's source code. (The Project Guide, Section 5, describes what may change in the updated data.)
- Identify missing values, duplicates, or other potentially problematic data where applicable.
- Clearly label metrics, time periods, charts, and filters.
- Present information in a professional, understandable format.

You have flexibility in your dashboard's appearance, layout, and functionality. Think about your intended audience. What information would an E-Presso manager need? What business questions should your dashboard answer? How should the information be organized? You may create additional functionality beyond these minimum requirements.

**Working with the E-Presso Data.** Your previous Power BI assignment used multiple data sources, including an Excel workbook, a CSV/text file, and a Microsoft Access database. You may use exports of these tables in Excel or CSV format when developing your hosted application.

Your application should preserve the meaning and structure of the source data. Do not assume that two fields should be joined merely because their names or values appear similar. Verify relationships, data types, and the level of detail represented by each table. For example, combining tables incorrectly can duplicate revenue values and produce misleading results. Your data preparation logic must support the calculations used by your dashboard.

**Important:** Do not hardcode E-Presso revenue totals, chart values, or other analytical results into your application. Your application must calculate them from the currently loaded data.

### Stage 2 — VALIDATE: Prove Your Dashboard Works
A professional-looking dashboard is not necessarily an accurate dashboard. Your next responsibility is to verify that your application produces correct analytical results. You will use your completed E-Presso Power BI assignment as an important point of comparison.

**Required Validation.** Compare at least the following five measures:
- Total revenue across the five-year period.
- Website revenue versus brick-and-mortar revenue.
- Revenue trends by year.
- Monthly revenue patterns.
- One additional business measure or comparison of your choice.

Create a validation table similar to the following:

| Metric | Power BI Result | Streamlit Result | Match? / Explanation |
|---|---|---|---|
| Total revenue | | | |
| Website revenue | | | |
| Brick-and-mortar revenue | | | |
| Annual revenue comparison | | | |
| Additional measure | | | |

You must investigate and explain any discrepancies. Power BI itself is not automatically correct. If the two applications disagree, examine the source data, relationships, aggregation methods, filters, and calculations. Independently verify at least one important calculation using Excel, Python, or another reproducible method.

**Modified-Data Test.** You must demonstrate that your application responds correctly when the underlying data changes.
- Create a separate copy of the E-Presso dataset.
- Change one valid revenue value by adding exactly $1,000. Do not change any other values. If revenue is calculated (for example quantity × price) rather than stored, follow Section 6 of the Project Guide.
- Reload the modified data into your application.

Verify that:
- Total revenue increases by exactly $1,000.
- The appropriate visualization reflects the change.
- Relevant filtered results update correctly.
- The application does not require changes to its Python code.

Document the original value, modified value, expected result, and actual result. Restore the original dataset afterward. A dashboard that only displays the original E-Presso figures without recalculating from new data does not meet this requirement.

**Understanding Analytical Limitations.** Your validation should go beyond simply comparing numbers. Consider whether the underlying metrics are appropriate. For example:
- Revenue is not the same as profit.
- A percentage requires a clearly defined denominator.
- Relationships between datasets can introduce duplication.
- Correlation does not establish causation.
- Missing survey responses may limit conclusions about customer satisfaction.

You will apply these same principles when developing your AI analytical assistant.

### Stage 3 — EXTEND: Build an AI Analytical Agent
You have created a dashboard and validated its calculations. Now you will extend your application by building an analytical assistant that can answer business questions using the application's actual data.

This is more than simply asking ChatGPT to interpret a spreadsheet. Your goal is to create an assistant that works within your application, has access to approved analytical functions, and can support its responses with calculated evidence.

**What Is an AI Analytical Agent?** An AI agent can combine a language model with tools that allow it to perform defined tasks. For this project, your analytical agent should be able to receive a business question, identify an appropriate analytical operation, obtain results from your application, and communicate those results to a user.

**Example.** An E-Presso manager asks: "Which sales channel experienced the greatest revenue growth?" Your agent should:
- Interpret the question as a comparison of revenue over time.
- Identify the analytical function needed to answer it.
- Execute that function against the currently loaded data.
- Retrieve the calculated results.
- Explain the findings using the actual numbers.
- Identify relevant limitations or assumptions.

The model should not invent results or rely on previously memorized E-Presso figures.

**Required Agent Functionality.** Your analytical assistant must:
- Provide an interactive interface where users can submit business questions.
- Use at least three approved analytical functions that you design or implement.
- Obtain numerical results from the application's currently loaded data.
- Provide answers supported by actual calculations.
- Expose or identify the function or calculation used to produce an answer.
- Clearly distinguish factual findings from interpretations and recommendations.
- Explain when data is missing or insufficient for a reliable conclusion.
- Demonstrate that answers change appropriately when the underlying data changes.
- Show a visible tool-call log with each answer (function name, arguments, and raw result).
- Limit questions per session, and respond gracefully if the model API fails or its quota runs out.

The agent should use the same definitions and calculations as your validated dashboard. If your dashboard is filtered to a particular subset of data, your agent must make clear whether its answer applies to that subset or to the full dataset.

**Designing Your Agent's Tools.** You must design at least three analytical functions that your agent is allowed to use. Possible examples include:
- `get_revenue_by_channel()` — Compare website and physical-store revenue.
- `get_store_trend()` — Calculate revenue changes for individual stores.
- `get_monthly_revenue_share()` — Calculate monthly revenue as a percentage of an appropriate annual total.
- `get_category_performance()` — Compare product categories.
- `get_data_quality_report()` — Identify missing or potentially problematic data.

These are examples, not required functions. You are responsible for deciding which capabilities would be most useful to an E-Presso manager. Start by creating and testing the analytical functions. Then connect them to your assistant.

**How Your Agent Will Respond.** For a live LLM-powered implementation, your application will typically contain five connected components:
1. **Chat Interface** — The user enters a question through your Streamlit application.
2. **Language Model** — An AI model interprets the question and identifies an appropriate analytical tool.
3. **Analytical Function** — Your Python application executes the selected function using the relevant data.
4. **Tool Result** — The calculated result is returned to the language model.
5. **User Response** — The model explains the finding, and your application displays the supporting evidence.

This process is commonly called function calling or tool calling. You may use AI coding assistance to help build the connection between these components.

**Implementation Expectations.** The preferred approach is a live language-model-powered agent that uses approved analytical functions. Possible model providers include Google Gemini and other providers offering suitable model APIs and function-calling capabilities. Students are not required to purchase paid API access. Free-tier access may be limited by provider, account eligibility, and usage restrictions.

If you cannot obtain an appropriate API connection without payment, you may implement a clearly identified rules-based analytical assistant that interprets supported questions and invokes real analytical functions. This alternative must still use the currently loaded data, demonstrate the same validation requirements, handle multiple business questions, and identify unsupported requests.

A rules-based analytical assistant is not technically equivalent to a language-model-powered agent. You must accurately describe what you built and document any API-access limitations. A live language-model agent that meets every requirement can earn all 15 points in the analytical assistant row. A rules-based assistant that meets every requirement can earn up to 12 of those 15 points.

A decorative chat interface or a collection of canned answers that does not perform live calculations will not receive credit as a functioning analytical assistant.

**Establishing Agent Boundaries.** You must decide what your agent is permitted to access and which actions it can perform. Your agent must not:
- Invent numerical findings.
- Claim that revenue establishes profitability.
- Present correlation as proof of causation.
- Silently modify the underlying dataset.
- Execute arbitrary AI-generated Python code or SQL in response to a user's question. This rules out LangChain's pandas DataFrame agent, PandasAI, code-interpreter features, and any use of eval() or exec() on model output. The model may only choose among your named functions.
- Make unsupported or overly confident business recommendations.
- Expose passwords, API keys, or other credentials.

**A Business Judgment Example.** Suppose a user asks: "Should E-Presso close its Chicago store?" Your agent may calculate Chicago's revenue trends and compare them with other stores. However, declining revenue alone does not establish whether closing the store is financially justified. A defensible response should explain the available evidence and identify additional information management would need, such as operating expenses, store profitability, lease obligations, and customer behavior. Your agent should be designed to recognize those limitations.

## Getting Started: Your Development Guide
You do not need to know how to perform every step before beginning. Use the following guidance to organize your work.

**Step 1 — Select an AI Development Assistant.** You may use one or more AI tools (ChatGPT, Codex, Claude, Gemini, GitHub Copilot) to help create your application. The purpose is to learn to use AI effectively as a development partner. You may ask AI to explain unfamiliar concepts, write code, troubleshoot errors, suggest designs, or help improve your application. But remember: you are responsible for verifying the code and understanding its analytical behavior. Do not purchase a subscription or API plan solely to complete this assignment.

**Step 2 — Create Your GitHub Repository.** Both teammates should create a free GitHub account. For Checkpoint 0, create your repository from the course starter template (Project Guide, Section 3) with Use this template → Create a new repository. The starter template already includes a README file, which you will revise as you build. Your README will eventually describe what your application does, how the files are organized, how to use it, and any important limitations. A public repository is acceptable because E-Presso uses fictional course data. Never place passwords, API keys, or confidential information in a public GitHub repository.

**Step 3 — Learn the Basics of Streamlit.** Streamlit is a Python framework for creating interactive data applications — dashboards, data-upload interfaces, visualizations, filters, and conversational interfaces without extensive front-end programming. The starter template already contains a small Streamlit app that uploads and previews a file. Deploy it first (Checkpoint 0), then use an AI assistant to learn how it works. Suggested prompt: *"I am a graduate data science student learning Streamlit for the first time. Here is the code for my starter app: [paste streamlit_app.py]. Explain what each section of the code does and what each required Python package is for. Help me make small, testable changes, one at a time."* Your first milestone is simply getting something working in a browser.

**Step 4 — Begin Developing Your E-Presso Dashboard.** Once your starter app is deployed, begin extending it to support the E-Presso datasets. A possible starting prompt: *"I am creating a business intelligence application using Python and Streamlit. My application will analyze E-Presso retail data containing sales, products, categories, stores, and customer satisfaction information. I want a dynamic dashboard with revenue KPIs, interactive visualizations, filters, and data-quality checks. Help me plan the application architecture, file structure, Python libraries, data preparation requirements, and calculations. Do not assume that the source tables are already joined correctly. Help me build the project in manageable stages, testing each feature before moving to the next."* Developing effective instructions for your AI coding assistant is part of the learning process. Do not try to build the entire application in one prompt. Build one component, test it, and then move to the next.

**Step 5 — Organize Your Application.** Possible files: `streamlit_app.py` (main web application), `analytics.py` (business metrics and analytical functions), `agent.py` (agent configuration and analytical tool connections), `requirements.txt` (required Python packages), `README.md` (project description, setup, and limitations). You may use a different structure if appropriate. The important requirement is that your code is organized, functional, and understandable. Your `requirements.txt` file should identify the external Python libraries the hosted application needs.

**Step 6 — Deploy Your Application.** Sign in to Streamlit Community Cloud, connect GitHub, create a new app from your repository and branch, set the main file (e.g., `streamlit_app.py`), deploy, and verify the URL works. Use deployment messages and error logs to diagnose problems. When you revise your code in GitHub, Streamlit Community Cloud can redeploy the updated application. You may work locally, through GitHub Codespaces, or another suitable Python environment. The essential final requirement is that your application is hosted and accessible through a URL.

**Step 7 — Validate the Dashboard Before Adding AI.** Check table relationships and revenue totals. Test interactive filters. Compare results with Power BI. Test your application with the modified dataset. This matters because your AI agent will rely on the analytical functions you create. If the underlying functions produce incorrect results, connecting them to a language model does not make those results correct.

**Step 8 — Build the Analytical Functions.** Create at least three Python functions that answer meaningful business questions. Test each function independently (e.g., verify a revenue-by-channel function returns the correct results before connecting it to AI). Your functions should work with the data currently loaded by the application. Do not allow the model to invent values or substitute estimated figures when exact calculations are available.

**Step 9 — Connect Your Agent.** Build a dispatcher and a rules-based assistant first, then add the language model as an upgrade (Project Guide, Section 7). Your AI development assistant can help you: build a Streamlit chat interface; select an available model and API that support function calling; define which analytical functions the model may invoke; configure the application to execute approved tool requests; return the calculated results to the model; display the response and supporting evidence; handle unsupported questions or unavailable model access appropriately.

Suggested agent-development prompt: *"I have built a Streamlit dashboard that analyzes business data using Python and Pandas. I now want to integrate an AI analytical agent that can answer business questions by calling approved Python functions. Help me build this step by step. First, explain the differences between a chat interface, a language model, and a tool-using agent. Next, help me connect my existing analytical functions to a language model through function calling. The agent must retrieve actual calculations from the currently loaded data. It must identify the function used, provide evidence supporting its response, and recognize when the available data is insufficient. Do not allow unrestricted code execution or modification of the underlying data. Explain how to configure API credentials securely, test the connection, and verify that the model is actually invoking the functions."*

Resources: Streamlit — Building a Conversational App; Google Gemini — Function Calling; Google AI Studio — API Keys; Streamlit — Secrets Management.

**A Note About API Keys.** An API key is a credential that authorizes your application to make requests. Do not place an API key directly in Python code that you publish on GitHub. Use secure environment variables or Streamlit's Secrets management feature. Check the provider's eligibility, privacy practices, and free-tier limits before enabling an API. Use only fictional or instructor-approved datasets. A publicly accessible application with an AI integration should also limit usage so that unexpected requests do not exhaust a free quota or create charges. If you encounter an API-access limitation, document the issue and use the permitted rules-based alternative.

**Step 10 — Troubleshoot, Test, and Iterate.** Expect problems. When something breaks: identify the problem; examine the error message or unexpected result; ask your AI development assistant to explain the likely cause; propose and implement a correction; retest the affected function; verify that the correction did not break something else; document meaningful revisions. Useful debugging prompt: *"My Streamlit application produced the following error: [paste error]. Explain what it means, identify the likely cause, and suggest the smallest reasonable correction. Do not rewrite the entire application unless necessary. Explain how I can test the correction and verify that other functionality still works."*

## Required Agent Testing
Your analytical assistant must be evaluated — not merely demonstrated. Test at least five questions, including:

- **Test 1 — Numerical Calculation.** Ask a question requiring a calculated business metric (e.g., "How much revenue did the website generate in 2028?"). Verify the result independently.
- **Test 2 — Numerical Comparison.** Ask a question requiring comparisons across categories, periods, stores, or channels (e.g., "Which store experienced the greatest percentage revenue decline?"). Verify the calculation and interpretation. Consider what the assistant should say if no store declined.
- **Test 3 — Missing Information.** Ask a question the available data cannot reliably answer (e.g., "Which E-Presso store is the most profitable?"). The assistant should recognize that revenue alone is insufficient to calculate store profitability.
- **Test 4 — Analytical Judgment.** Ask a question requiring interpretation or a business recommendation (e.g., "Does higher customer satisfaction cause higher revenue?"). Evaluate whether the assistant distinguishes association from causation and acknowledges important limitations.
- **Test 5 — Updated Data.** Repeat an appropriate numerical question after modifying the data. Does the agent retrieve the updated result? Does its response reflect the change? An agent that continues reporting the original result without acknowledging the changed data has not passed this test.

**Documenting Your Tests:**

| Test | Question | Function Used | Expected Result/Behavior | Actual Result | Pass/Fail | Revision Made |
|---|---|---|---|---|---|---|
| Test 1 | | | | | | |
| Test 2 | | | | | | |
| Test 3 | | | | | | |
| Test 4 | | | | | | |
| Test 5 | | | | | | |

Include evidence of the calculation or tool invocation for applicable tests. At least one test must demonstrate an actual correction or meaningful improvement, followed by a retest. If all initial tests pass, deliberately test an additional edge case and document any refinement or confirmed robustness. A failed test is not automatically evidence of a failed project. Identifying a defect, explaining its cause, correcting it, and demonstrating that the correction works is valuable evidence of the development process.

## Development Checkpoints
These checkpoints are intended to help you manage an ambitious development project. They are progress expectations, not requirements to produce polished final submissions at each stage. (Dates below are from the Canvas page; the Guide's Section 2 dates differ slightly and the Guide controls.)

| Date | Checkpoint | Expected Progress |
|---|---|---|
| Oct 25 | Original Power BI Assignment Due | Completed E-Presso Power BI analysis |
| Oct 26 | Checkpoint 0 — Hello World | Starter repository copied to your GitHub account, deployed, URL submitted |
| Oct 28 | Checkpoint 1 — First Deployment | Hosted app loads the E-Presso files and shows a data profile; grain statements written |
| Nov 1 | Checkpoint 2 — Functional Dashboard | Data loading, calculations, charts, filtering, and initial validation |
| Nov 4 | Checkpoint 3 — Analytical Functions | At least three tested functions and a dispatcher |
| Nov 8 | Checkpoint 4 — Working Assistant | Working assistant with a tool-call log; validation table and $1,000 test complete |
| Nov 15 | Final Project Due | Complete dashboard, analytical assistant, validation, testing, and documentation |

## What to Submit to Canvas
Submit one project package per Power BI Buddy team.
1. **Live Application URL** — accessible to the instructor without your personal environment or private credentials. Verify the link before submitting. Keep the app deployed and repo intact until grades are posted.
2. **GitHub Repository URL** — source code, dependency information, and README documentation. No API keys or confidential credentials.
3. **Validation Evidence** — Power BI vs. Streamlit validation table, at least one independently verified calculation, and the $1,000 modified-data test results. Explain any discrepancies or unresolved limitations.
4. **Agent Testing Evidence** — five required agent tests with questions, expected behaviors, actual results, analytical functions, outcomes, and documented revisions. Enough evidence to show the assistant used actual application calculations.
5. **Development Reflection** — team reflection of ~300–500 words: which AI tools you used and how; the most significant technical or analytical challenge; how you diagnosed and resolved it; what your AI assistant handled well and where it struggled; what required human analytical judgment; whether you would trust your application for real business decisions, and what additional safeguards would be necessary. Your GitHub revision history and README should support this.
6. **Team Contribution and Project Defense** — responsibilities and contributions of each team member. Every team member should understand the application's key calculations, major design decisions, and analytical limitations. Be prepared to demonstrate the application and explain how your agent obtains answers. Each team member should expect a short individual oral check after the due date. The instructor may test the application using modified data or a business question not included in your original test cases.

## Grading Rubric — 70 Points
| Assessment Component | Points |
|---|---|
| Successfully deployed, functioning hosted application | 10 |
| Data handling, modeling, and calculation accuracy | 15 |
| Meaningful, interactive visualizations and usability | 10 |
| Independent validation and updated-data testing | 15 |
| Analytical assistant design, controls, and evaluation | 15 |
| Documentation, iteration, and project defense | 5 |
| **TOTAL** | **70** |

Descriptors for each component are in the Project Guide (Section 9).

## What Matters Most
Your grade will emphasize: whether your application actually works; whether its calculations are accurate; whether it can analyze updated data; whether the AI assistant retrieves genuine analytical results; whether the system can recognize its limitations; whether you can explain and defend your work.

Visual polish is valuable, but an attractive dashboard with incorrect calculations will not receive a high score. Extra functionality does not compensate for inaccurate results. You are encouraged to experiment with additional analytical features (forecasting, anomaly detection, enhanced data validation, additional visualizations, more sophisticated agent capabilities). These extensions are welcome but are not required for full credit.

## Final Application Challenge
I will test your application using a modified E-Presso dataset and a business question you have not previously encountered. Your application should respond appropriately without requiring changes to the underlying code. Your analytical assistant should use the current data, identify relevant evidence, and acknowledge uncertainty when the requested conclusion is not supported. The purpose is to demonstrate that you have built a functioning analytical system rather than a static presentation of predetermined results.

## A Final Thought
This project is not about proving that AI is good or bad at data science. It is about learning how to use powerful technology responsibly and effectively. You are being asked to think like data scientists: define a problem, design an approach, build a solution, test assumptions, evaluate evidence, and communicate defensible conclusions. You should expect to encounter obstacles, revise your approach, and see AI-generated code occasionally fail. Your responsibility is to recognize those problems, investigate them, and improve your solution.

**You are allowed to use AI to help build your application. You are not allowed to outsource accountability for its results.**
