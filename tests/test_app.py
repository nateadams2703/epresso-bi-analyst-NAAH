"""App tests: run streamlit_app.py the way a browser visit would (Streamlit's AppTest) and
check that every result follows the sidebar filters. Expected numbers come from the
analytics.py functions, so these tests check the wiring; test_analytics.py checks the math."""
import os
import re
import sys

import pytest
from streamlit.testing.v1 import AppTest

try:
    from streamlit.testing.v1.errors import AppTestError
except ImportError:  # older Streamlit (e.g. 1.45) has no AppTestError and never raises it
    AppTestError = Exception

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import analytics  # noqa: E402
import data_prep  # noqa: E402

APP = os.path.join(ROOT, 'streamlit_app.py')
UNESCAPED_DOLLAR = re.compile(r'(?<!\\)\$')  # a $ without a backslash before it
KPI_LABELS = ('Total revenue', 'Website share', 'Revenue change')


@pytest.fixture(scope='module')
def model():
    files, _ = data_prep.collect_files()
    tables, _ = data_prep.load_tables(files)
    return data_prep.build_sales_model(tables)[0]


def run(**filters):
    """Open the app, set the sidebar filters (e.g. store=['SH11']), and return it."""
    at = AppTest.from_file(APP, default_timeout=90).run()
    for param, values in filters.items():
        at.multiselect(key=f'filter_{param}').set_value(values).run()
    return at


def kpis(at):
    return {m.label: m.value for m in at.metric if m.label in KPI_LABELS}


def captions(at):
    return [c.value for c in at.caption]


def n_charts(at):
    return len(at.get('plotly_chart'))


def markdown_texts(at):
    """Every piece of text Streamlit renders as Markdown (where $...$ would become math)."""
    texts = [e.value for kind in ('markdown', 'caption', 'info', 'warning', 'error', 'success')
             for e in getattr(at, kind)]
    return texts + [m.label for m in at.metric]


def assert_no_errors(at):
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


# ---------------------------------------------------------------- layout
def test_app_loads_with_three_tabs_and_four_charts():
    at = run()
    assert_no_errors(at)
    assert [t.label for t in at.tabs] == ['Data and profile', 'Dashboard', 'Assistant']
    assert n_charts(at) == 4


def test_filters_are_at_the_top_of_the_sidebar(model):
    at = run()
    assert at.sidebar.header[0].value == 'Dashboard filters'
    filters = {m.label: m for m in at.sidebar.multiselect}
    assert list(filters) == ['Year', 'Channel', 'Store', 'Category']
    # option lists come from the loaded data, not from the code
    assert len(filters['Store'].options) == model['Store ID'].nunique()
    assert len(filters['Year'].options) == model['Year'].nunique()


# ---------------------------------------------------------------- filters drive every result
def test_no_filters_matches_analytics(model):
    at = run()
    total = analytics.get_total_revenue(model).value
    change = analytics.get_revenue_change(model).value
    assert f'Exactly \\${total:,.2f}' in captions(at)
    assert kpis(at)['Revenue change'] == f'{change["change_pct"]:+.1f}%'
    assert any('Scope: all years; all channels; all stores; all categories' in m.value
               for m in at.markdown)


def test_store_filter_changes_every_kpi_and_chart(model):
    at = run(store=['SH11'])
    assert_no_errors(at)
    total = analytics.get_total_revenue(model, store='SH11').value
    change = analytics.get_revenue_change(model, store='SH11').value
    assert f'Exactly \\${total:,.2f}' in captions(at)
    assert kpis(at)['Website share'] == '0.0%'  # a physical store has no Website sales
    assert kpis(at)['Revenue change'] == f'{change["change_pct"]:+.1f}%'
    assert n_charts(at) == 4
    assert any(labels in m.value for m in at.markdown
               for labels in [analytics.store_labels(model)['SH11']])


def test_combination_with_no_sales_shows_a_message_not_an_error():
    at = run(store=['SH11'], channel=['Website'])
    assert_no_errors(at)
    assert any('No sales match these filters' in w.value for w in at.warning)
    assert n_charts(at) == 0 and kpis(at) == {}


def test_single_year_has_no_revenue_change():
    at = run(year=[2028])
    assert_no_errors(at)
    assert kpis(at)['Revenue change'] == 'n/a'


def test_selection_missing_from_new_data_is_cleared_with_a_note():
    at = AppTest.from_file(APP, default_timeout=90)
    at.session_state['filter_store'] = ['SH99']  # e.g. a store removed in an uploaded file
    at.run()
    assert_no_errors(at)
    assert any('were cleared' in i.value for i in at.info)
    assert at.multiselect(key='filter_store').value == []


# ---------------------------------------------------------------- store chart
def test_store_chart_excludes_website_until_box_is_ticked(model):
    web_ids = sorted(model.loc[model['Channel'] == data_prep.WEBSITE_TYPE, 'Store ID'].unique())
    at = run()
    box = at.checkbox(key='store_chart_include_website')
    assert box.label == f'Include the website ({", ".join(web_ids)})' and box.value is False
    assert any('is excluded from this chart' in c for c in captions(at))
    assert n_charts(at) == 4
    store_chart = at.get('plotly_chart')[-1].proto.spec
    assert 'SH01' in store_chart  # sanity check: this really is the store chart
    assert all(i not in store_chart for i in web_ids)

    at = box.check().run()
    assert n_charts(at) == 4  # ticking the box once made the store chart disappear
    assert not any('is excluded from this chart' in c for c in captions(at))
    assert all(i in at.get('plotly_chart')[-1].proto.spec for i in web_ids)


def test_store_chart_with_only_website_selected_explains_itself():
    at = run(channel=['Website'])
    assert_no_errors(at)
    assert any('Only the website is selected' in i.value for i in at.info)


# ---------------------------------------------------------------- dollar signs
def test_unescaped_dollar_check_catches_the_original_bug():
    assert UNESCAPED_DOLLAR.search('$7,181,750 → $9,181,550')
    assert not UNESCAPED_DOLLAR.search(r'\$7,181,750 → \$9,181,550')


@pytest.mark.parametrize('filters', [{}, {'store': ['SH11']}, {'year': [2028]},
                                     {'store': ['SH11'], 'channel': ['Website']}])
def test_dollar_signs_are_escaped_everywhere(filters):
    at = run(**filters)
    bad = [t for t in markdown_texts(at) if UNESCAPED_DOLLAR.search(t)]
    assert bad == []


# ---------------------------------------------------------------- data-quality notes
def test_notes_have_a_summary_are_ordered_and_state_the_caveat_once():
    at = run()
    texts = '\n'.join(m.value for m in at.markdown)
    assert '**4 to review · 1 info · 1 expected**' in texts
    assert texts.index('**Review**') < texts.index('**Info**') < texts.index('**Expected**')
    assert 'sales territories' not in texts  # not repeated inside the notes
    assert sum('sales territories' in c.value for c in at.caption) == 1


def test_website_share_is_zero_when_only_physical_stores_are_selected():
    at = run(channel=['Brick & Mortar'])
    assert_no_errors(at)
    assert kpis(at)['Website share'] == '0.0%'


# ---------------------------------------------------------------- loaded-file fingerprint
def test_sidebar_shows_rows_and_revenue_sum_for_each_loaded_file():
    files, _ = data_prep.collect_files()
    tables, _ = data_prep.load_tables(files)
    revenue = tables['Sales']['Revenue'].sum()
    at = run()
    lines = [m.value for m in at.sidebar.markdown]
    assert (f'**Sales:** `Sales.csv` (original (data/)) · {len(tables["Sales"]):,} rows · '
            f'revenue sum \\${revenue:,.2f}') in lines
    assert any(line.startswith('**Stores:**') and line.endswith(f'{len(tables["Stores"])} rows')
               for line in lines)


# ---------------------------------------------------------------- assistant tab
def test_assistant_question_runs_through_the_dispatcher_and_logs_the_data():
    at = run()
    at.chat_input[0].set_value('Are there any missing values?').run()
    assert_no_errors(at)
    entry = at.session_state['history'][-1]['answer']['tool_log'][0]
    assert entry['tool'] == 'data_quality_report' and entry['status'] == 'ok'
    assert entry['data'].startswith('Sales.csv (original (data/)) · 25,200 rows')


# ---------------------------------------------------------------- assistant tab (Checkpoint 4)
def ask_app(at, question):
    at.chat_input[0].set_value(question).run()
    return at


def history(at):
    return at.session_state['history']


def test_assistant_says_it_is_rules_based_option_b():
    at = run()
    assert any('Option B' in c.value and 'does not use a language model' in c.value
               for c in at.caption)


def test_answer_shows_scope_sections_and_tool_call_log():
    at = ask_app(run(), 'How much revenue did the website generate in 2028?')
    assert_no_errors(at)
    texts = [m.value for m in at.markdown]
    assert any(t.startswith('**Scope: 2028 (from your question)') for t in texts)
    for title in ('**Findings**', '**Interpretation**', '**Next steps**'):
        assert any(t.startswith(title) for t in texts), title
    assert any(e.label == 'Tool-call log (1 call)' for e in at.expander)
    assert any(t.startswith('**1. get_total_revenue** · ok') for t in texts)
    assert any(t.startswith('Arguments: {"year": [2028], "channel": ["Website"]}') for t in texts)
    assert len(at.get('json')) >= 1  # the raw tool result
    assert any('Questions used: 1 of 15' in c.value for c in at.caption)


def test_unsupported_question_shows_no_tool_was_run():
    at = ask_app(run(), 'What is the weather in Chicago?')
    assert any(e.label == 'Tool-call log (0 calls)' for e in at.expander)
    assert any('No tool was run for this question.' in c.value for c in at.caption)


def test_sidebar_filters_apply_to_questions_until_switched_off():
    at = run(store=['SH11'])
    assert any('Sidebar filters that will apply:' in c.value and 'SH11 – Chicago, IL' in c.value
               for c in at.caption)
    ask_app(at, 'What was revenue in 2028?')
    assert 'SH11 – Chicago, IL (from the sidebar filter)' in history(at)[-1]['answer']['scope']
    at.checkbox(key='assistant_use_sidebar').uncheck().run()
    ask_app(at, 'What was revenue in 2028?')
    assert 'all stores' in history(at)[-1]['answer']['scope']


def test_question_limit_stops_at_15_with_a_clear_message():
    at = AppTest.from_file(APP, default_timeout=90)
    at.session_state['n_questions'] = 14
    at.run()
    ask_app(at, 'What was revenue in 2028?')  # the 15th question is still answered
    assert len(history(at)) == 1
    assert any("You've reached this session's limit of 15 questions" in w.value
               for w in at.warning)
    assert at.chat_input[0].proto.disabled  # the chat box is disabled at the limit
    try:
        ask_app(at, 'And in 2029?')           # a 16th question is not answered
    except AppTestError:
        pass  # newer Streamlit refuses to type into a disabled chat box, like a browser
    assert len(history(at)) == 1 and at.session_state['n_questions'] == 15


@pytest.mark.parametrize('question', ['How much revenue did the website generate in 2028?',
                                      'Should E-Presso close the Chicago store?',
                                      'Which E-Presso store is the most profitable?'])
def test_dollar_signs_in_answers_are_escaped(question):
    at = ask_app(run(), question)
    assert any('$' in t for t in markdown_texts(at))  # the answer does contain dollars
    assert [t for t in markdown_texts(at) if UNESCAPED_DOLLAR.search(t)] == []
