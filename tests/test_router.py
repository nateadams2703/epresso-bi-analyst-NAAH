"""Tests for the rules router and the answer composer (Checkpoint 4, part a).
Routing, scope (question vs. sidebar filters), answer structure, and the rule that every
number in Findings comes from a tool result in the call log."""
import json
import os
import re
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import agent  # noqa: E402
import data_prep  # noqa: E402

DATA = data_prep.DATA_DIR


def context(uploads=None):
    files, _ = data_prep.collect_files(uploads)
    tables, _ = data_prep.load_tables(files)
    model = data_prep.build_sales_model(tables)[0]
    return agent.make_context(model, tables, data_prep.loaded_summary(files, tables))


@pytest.fixture(scope='module')
def ctx():
    return context()


def ask(ctx, question, **kwargs):
    return agent.answer_question(question, ctx, **kwargs)


def calls(answer):
    return [(e['tool'], e['arguments_used']) for e in answer['tool_log']]


# ---------------------------------------------------------------- the five agent tests
AGENT_TESTS = [
    ('How much revenue did the website generate in 2028?', 'total',
     [('get_total_revenue', {'year': [2028], 'channel': ['Website']})]),
    ('Which store experienced the greatest percentage revenue decline?', 'store_trends',
     [('get_store_trends', {})]),
    ('Which E-Presso store is the most profitable?', 'profit',
     [('get_data_coverage', {}),
      ('get_revenue_breakdown', {'by': ['store'], 'channel': ['Brick & Mortar']})]),
    ('Does higher customer satisfaction cause higher revenue?', 'satisfaction',
     [('get_satisfaction_vs_revenue', {})]),
    ("What was Chicago's revenue in 2028?", 'total',
     [('get_total_revenue', {'year': [2028], 'store': ['SH11']})]),
    ('Should E-Presso close the Chicago store?', 'decision',
     [('get_revenue_breakdown', {'by': ['year'], 'store': ['SH11']}),
      ('get_store_trends', {}), ('get_data_coverage', {})]),
]


@pytest.mark.parametrize('question, intent, expected', AGENT_TESTS)
def test_agent_test_questions_route_to_the_right_tools(ctx, question, intent, expected):
    answer = ask(ctx, question)
    assert answer['intent'] == intent
    assert calls(answer) == expected
    assert all(e['status'] == 'ok' for e in answer['tool_log'])


@pytest.mark.parametrize('question, intent, tool', [
    ('How much did we sell online in 2028?', 'total', 'get_total_revenue'),
    ('Total sales for beans in 2027', 'total', 'get_total_revenue'),
    ('Which shop had the biggest drop in sales?', 'store_trends', 'get_store_trends'),
    ('How did the large stores trend from 2026 to 2029?', 'store_trends', 'get_store_trends'),
    ('Is customer satisfaction related to sales?', 'satisfaction', 'get_satisfaction_vs_revenue'),
    ('What are our margins by store?', 'profit', 'get_data_coverage'),
    ('Should we shut down SH07?', 'decision', 'get_revenue_breakdown'),
    ('What was revenue by category in 2027?', 'breakdown', 'get_revenue_breakdown'),
    ('Compare revenue by channel and year', 'breakdown', 'get_revenue_breakdown'),
    ('Which months bring in the most revenue?', 'seasonality', 'get_monthly_share'),
    ('Are there missing values in the sales data?', 'quality', 'data_quality_report'),
    ('What can you help me with?', 'coverage', 'get_data_coverage'),
    ('What is the weather in Chicago?', None, None),
])
def test_rephrased_questions_route_by_intent(ctx, question, intent, tool):
    answer = ask(ctx, question)
    assert answer['intent'] == intent
    assert (answer['tool_log'][0]['tool'] if answer['tool_log'] else None) == tool


def test_trend_question_with_two_years_and_a_tier(ctx):
    answer = ask(ctx, 'How did the large stores trend from 2026 to 2029?')
    assert calls(answer) == [('get_store_trends',
                              {'start_year': 2026, 'end_year': 2029, 'market': ['4-Large']})]


def test_breakdown_dimensions_follow_the_question(ctx):
    answer = ask(ctx, 'Compare revenue by channel and year')
    assert calls(answer)[0][1]['by'] == ['channel', 'year']


# ---------------------------------------------------------------- filters from the question
def test_filters_are_read_from_the_question_using_values_in_the_data(ctx):
    found = agent.extract_filters(
        "Online beans sales at Chicago's large stores in 2027 and 2028", ctx)
    assert found == {'year': [2027, 2028], 'store': ['Chicago'], 'channel': ['Website'],
                     'category': ['Beans'], 'market': ['4-Large']}


def test_largest_and_small_change_are_not_read_as_market_tiers(ctx):
    assert 'market' not in agent.extract_filters(
        'Which store had the largest decline, and was it a small change?', ctx)


def test_ambiguous_city_in_a_question_asks_which_store(ctx):
    answer = ask(ctx, 'What was Orlando revenue in 2027?')
    assert 'SH01 – Orlando, FL' in answer['findings'][0]
    assert 'SH08 – Orlando, FL' in answer['findings'][0]
    assert answer['tool_log'][0]['status'] == 'error'


def test_year_not_in_the_data_is_not_guessed(ctx):
    answer = ask(ctx, 'What was revenue in 2031?')
    assert 'not in the loaded data' in answer['findings'][0] and '2029' in answer['findings'][0]


# ---------------------------------------------------------------- scope
def test_scope_labels_question_and_sidebar_filters(ctx):
    answer = ask(ctx, 'What was revenue in 2028?', sidebar={'store': ['SH11'], 'year': [2025]})
    assert answer['scope'].startswith('Scope: ')
    assert '2028 (from your question)' in answer['scope']           # the question wins
    assert 'SH11 – Chicago, IL (from the sidebar filter)' in answer['scope']
    assert calls(answer)[0][1] == {'year': [2028], 'store': ['SH11']}


def test_sidebar_filters_can_be_switched_off(ctx):
    answer = ask(ctx, 'What was revenue in 2028?', sidebar={'store': ['SH11']},
                 use_sidebar=False)
    assert 'all stores' in answer['scope'] and 'store' not in calls(answer)[0][1]


def test_sidebar_filter_a_tool_cannot_use_is_reported(ctx):
    answer = ask(ctx, 'Which store declined most?', sidebar={'store': ['SH11']})
    assert 'Sidebar store filter not applied: this question compares stores.' in answer['scope']


def test_store_decision_ignores_sidebar_and_says_so(ctx):
    answer = ask(ctx, 'Should E-Presso close the Chicago store?', sidebar={'year': [2028]})
    assert 'sidebar filters not applied' in answer['scope']


# ---------------------------------------------------------------- answer structure
QUESTIONS = [q for q, _, _ in AGENT_TESTS] + [
    'What was revenue by category in 2027?', 'Which months bring in the most revenue?',
    'Which store had the highest revenue?', 'How did the large stores trend from 2026 to 2029?',
    'Are there missing values in the sales data?', 'What can you help me with?',
    'What is the weather in Chicago?', 'How is Chicago doing?', 'How did Chicago do in 2028?',
    'How are the Phoenix and Tempe stores doing?']


@pytest.mark.parametrize('question', QUESTIONS)
def test_every_answer_has_scope_findings_interpretation_and_next_steps(ctx, question):
    answer = ask(ctx, question)
    assert answer['scope'].startswith('Scope: ')
    assert answer['findings'] and answer['next_steps']
    assert isinstance(answer['interpretation'], list)


@pytest.mark.parametrize('question', ['Which E-Presso store is the most profitable?',
                                      'Does higher customer satisfaction cause higher revenue?',
                                      'Should E-Presso close the Chicago store?'])
def test_judgment_answers_make_no_recommendation(ctx, question):
    assert ask(ctx, question)['next_steps'][0] == agent.NO_RECOMMENDATION


NUMBER = re.compile(r'(?<![A-Za-z0-9.])[-+]?\$?\d[\d,]*(?:\.\d+)?')


def _numbers(text):
    """(absolute value, decimals) for every number in a text; IDs like SH11 are skipped."""
    out = []
    for token in NUMBER.findall(text):
        clean = token.replace('$', '').replace(',', '').lstrip('+-')
        out.append((abs(float(clean)), len(clean.split('.')[1]) if '.' in clean else 0))
    return out


@pytest.mark.parametrize('question', QUESTIONS)
def test_findings_only_contain_numbers_from_tool_results(ctx, question):
    answer = ask(ctx, question)
    logged = json.dumps([[e['result'], e['arguments_used']] for e in answer['tool_log']],
                        ensure_ascii=False)
    available = [value for value, _ in _numbers(logged)]
    for text in answer['findings']:
        for value, decimals in _numbers(text):
            assert any(round(a, decimals) == value for a in available), (value, text)


# ---------------------------------------------------------------- specific answers
def test_trend_answer_gives_tier_context_from_the_tool(ctx):
    answer = ask(ctx, 'Which store experienced the greatest percentage revenue decline?')
    largest = answer['tool_log'][0]['result']['value']['largest_decline']
    text = ' '.join(answer['findings'])
    assert f"Largest decline: {largest['store_label']} ({largest['market']})" in text
    assert f"{abs(largest['vs_tier_median_pts']):.2f} points below its tier's median" in text


def test_trend_answer_when_no_store_declined():
    model = pd.DataFrame({
        'Store ID': ['SH01', 'SH01', 'SH02', 'SH02'], 'Channel': ['Brick & Mortar'] * 4,
        'Market': ['1-Small'] * 4, 'City': ['Tempe', 'Tempe', 'Omaha', 'Omaha'],
        'State': ['AZ', 'AZ', 'NE', 'NE'], 'Category': ['Beans'] * 4,
        'Year': pd.array([2025, 2026, 2025, 2026], dtype='Int64'),
        'Revenue': [100.0, 150.0, 200.0, 220.0]})
    answer = ask(agent.Context(model=model), 'Which store declined most?')
    assert any('No store declined between 2025 and 2026. Smallest growth: SH02 – Omaha, NE '
               '(1-Small) +10.00%.' in f for f in answer['findings'])


def test_profit_answer_says_profit_is_unavailable_and_labels_revenue(ctx):
    answer = ask(ctx, 'Which E-Presso store is the most profitable?')
    assert answer['findings'][0].startswith('Profit cannot be calculated')
    assert 'Highest revenue, not profit:' in answer['findings']
    top = sorted(answer['tool_log'][1]['result']['value'], key=lambda x: -x['revenue'])[:3]
    if len({x['market'] for x in top}) == 1:  # in the original data: the three 4-Large stores
        assert any(i.startswith(f"The top three are the three {top[0]['market']} stores")
                   for i in answer['interpretation'])
    assert any('is a separate sales channel and is excluded unless you ask' in i
               for i in answer['interpretation'])
    assert sum(i.startswith('Revenue is not profit') for i in answer['interpretation']) == 0
    assert sum('Revenue is not profit' in i for i in answer['interpretation']) == 1


def test_profit_answer_includes_the_website_when_asked(ctx):
    answer = ask(ctx, 'Is the website or the physical channel more profitable?')
    assert not any('excluded unless you ask' in i for i in answer['interpretation'])
    assert 'channel' in calls(answer)[1][1] and len(calls(answer)[1][1]['channel']) == 2


def test_close_store_answer_shows_evidence_then_what_is_missing(ctx):
    answer = ask(ctx, 'Should E-Presso close the Chicago store?')
    text = ' '.join(answer['findings'])
    assert text.startswith('SH11 – Chicago, IL revenue by year: 2025 $')
    assert 'Within 4-Large it ranks' in text and 'points below its tier' in text
    missing = ' '.join(answer['interpretation'])
    for item in ('operating costs and profit', 'lease obligations', 'customer behavior'):
        assert item in missing
    assert answer['next_steps'][0] == agent.NO_RECOMMENDATION


def test_unsupported_question_lists_what_the_assistant_can_answer(ctx):
    answer = ask(ctx, 'What is the weather in Chicago?')
    assert answer['intent'] is None and answer['tool_log'] == []
    for _, example in agent.CAPABILITIES:
        assert any(example in step for step in answer['next_steps'])


# ---------------------------------------------------------------- agent test 5 (updated data)
def test_agent_test_5_same_question_after_upload(ctx):
    question = "What was Chicago's revenue in 2028?"
    before = ask(ctx, question)
    after = ask(context({'Sales.csv': (DATA / 'modified' / 'Sales.csv').read_bytes()}), question)
    b, a = before['tool_log'][0], after['tool_log'][0]
    assert round(a['result']['value'] - b['result']['value'], 2) == 1000.00
    assert before['findings'][0] != after['findings'][0]
    assert '(original (data/))' in b['data'] and '(uploaded)' in a['data']


# ---------------------------------------------------------------- defect 1: casual phrasing
# Found Nov 2 (docs/agent-tests.md): "How did Orlando do in 2028?" got the unsupported reply,
# because no intent rule matched a store question without a money word.
@pytest.mark.parametrize('question, tool, used', [
    ('How did Chicago do in 2028?', 'get_total_revenue', {'year': [2028], 'store': ['SH11']}),
    ('How did Chicago fare in 2027?', 'get_total_revenue', {'year': [2027], 'store': ['SH11']}),
    ('How is Chicago doing?', 'get_store_trends', {'store': ['SH11']}),
    ("How's Boulder doing?", 'get_store_trends', {'store': ['SH03']}),
    ('How does SH07 perform?', 'get_store_trends', {'store': ['SH07']}),
    ('How has Denver performed from 2026 to 2029?', 'get_store_trends',
     {'start_year': 2026, 'end_year': 2029, 'store': ['SH13']}),
    ('How are the Phoenix and Tempe stores doing?', 'get_store_trends',
     {'store': ['SH09', 'SH20']}),
])
def test_casual_store_questions_route_to_a_revenue_tool(ctx, question, tool, used):
    answer = ask(ctx, question)
    assert answer['intent'] == 'performance'
    assert calls(answer) == [(tool, used)]
    assert answer['tool_log'][0]['status'] == 'ok'


def test_defect_1_how_did_orlando_do_in_2028_gives_the_ambiguous_store_answer(ctx):
    answer = ask(ctx, 'How did Orlando do in 2028?')
    assert answer['intent'] == 'performance'
    assert answer['tool_log'][0]['tool'] == 'get_total_revenue'
    assert answer['tool_log'][0]['status'] == 'error'
    assert 'SH01 – Orlando, FL' in answer['findings'][0]
    assert 'SH08 – Orlando, FL' in answer['findings'][0]


def test_casual_store_trend_focuses_on_the_named_stores(ctx):
    answer = ask(ctx, 'How are the Phoenix and Tempe stores doing?')
    assert answer['scope'].startswith(
        'Scope: focus: SH09 – Phoenix, AZ, SH20 – Tempe, AZ (from your question); ')
    assert 'store filter not applied' not in answer['scope']
    assert any(f.startswith('SH09 – Phoenix, AZ (4-Large)') for f in answer['findings'])
    assert any(f.startswith('SH20 – Tempe, AZ (1-Small)') for f in answer['findings'])
    assert not any(f.startswith('Largest decline') for f in answer['findings'])


def test_named_store_that_cannot_be_resolved_is_not_replaced_by_another_store(ctx):
    answer = ask(ctx, "How did Orlando's revenue decline?")
    assert 'matches more than one store' in answer['findings'][0]
    assert not any('Largest decline' in f for f in answer['findings'])


@pytest.mark.parametrize('question', ['How did we do in 2028?', 'How is the weather doing?'])
def test_casual_phrasing_without_a_store_is_still_unsupported(ctx, question):
    answer = ask(ctx, question)
    assert answer['intent'] is None and answer['tool_log'] == []


# Retest follow-up (Nov 2): "How did Orlando's revenue decline?" showed 0 calls in the tool-call
# log, while "How did Orlando do in 2028?" showed 1, though both end in the same error.
def test_failed_store_lookup_in_a_trend_question_is_logged(ctx):
    trend = ask(ctx, "How did Orlando's revenue decline?")
    total = ask(ctx, 'How did Orlando do in 2028?')
    assert [(e['tool'], e['status']) for e in trend['tool_log']] == [('get_store_trends', 'error')]
    assert trend['tool_log'][0]['arguments'] == {'store': ['Orlando']}
    assert trend['tool_log'][0]['result']['error'] == total['tool_log'][0]['result']['error']


@pytest.mark.parametrize('question', ["How did Orlando's revenue decline?",
                                      'How did Orlando do in 2028?',
                                      "What was Orlando's revenue in 2027?",
                                      'Should E-Presso close the Orlando store?',
                                      'How is SH99 doing?', 'What was revenue in 2031?'])
def test_every_error_answer_logs_what_was_tried(ctx, question):
    answer = ask(ctx, question)
    assert answer['findings'][0].startswith('The request could not be completed')
    assert answer['tool_log'] and answer['tool_log'][-1]['status'] == 'error'
