"""Tests for the assistant's registry, dispatcher (run_tool), and call log.
They use the original E-Presso files; expected values come from calling the analytics
functions directly, so these tests check the dispatcher, not the arithmetic."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import agent  # noqa: E402
import analytics  # noqa: E402
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


# ---------------------------------------------------------------- registry
def test_registry_has_the_planned_tools_and_not_the_generic_starter_ones():
    assert {'get_total_revenue', 'get_revenue_breakdown', 'get_monthly_share',
            'get_store_trends', 'get_satisfaction_vs_revenue',
            'get_data_coverage'} <= set(agent.TOOLS)
    assert 'get_total' not in agent.TOOLS and 'group_total' not in agent.TOOLS
    for name, spec in agent.TOOLS.items():
        assert set(spec['params']) <= set(agent.PARAMS), name
        assert set(spec['required']) <= set(spec['params']), name
        assert set(spec['inputs']) <= set(agent.INPUTS), name


def test_tool_definitions_take_allowed_values_from_the_data(ctx):
    defs = {d['name']: d for d in agent.tool_definitions(ctx)}
    assert set(defs) == set(agent.TOOLS)
    year = defs['get_total_revenue']['parameters']['properties']['year']
    assert year['items']['enum'] == sorted(ctx.model['Year'].dropna().unique().tolist())
    assert defs['get_revenue_breakdown']['parameters']['required'] == ['by']
    assert defs['get_store_trends']['parameters']['properties']['start_year']['type'] == 'integer'


# ---------------------------------------------------------------- normalizing arguments
def test_arguments_are_normalized_before_the_tool_runs(ctx):
    log = []
    result = agent.run_tool('get_total_revenue', {'year': '2028', 'channel': 'website'}, ctx, log)
    direct = analytics.get_total_revenue(ctx.model, year=2028, channel='Website')
    assert result.value == direct.value and result.error is None
    assert log[0]['arguments'] == {'year': '2028', 'channel': 'website'}
    assert log[0]['arguments_used'] == {'year': [2028], 'channel': ['Website']}


def test_survey_style_year_is_accepted(ctx):
    assert agent.normalize('year', 'Y2027', ctx) == ([2027], None)


@pytest.mark.parametrize('given', ['Chicago', 'chicago', 'SH11', 'sh11', 'SH11 – Chicago, IL'])
def test_store_can_be_an_id_a_label_or_a_city_with_one_store(ctx, given):
    assert agent.normalize('store', given, ctx) == (['SH11'], None)


def test_ambiguous_city_is_an_error_naming_the_stores(ctx):
    value, err = agent.normalize('store', 'Orlando', ctx)
    assert value is None
    assert 'SH01 – Orlando, FL' in err and 'SH08 – Orlando, FL' in err


@pytest.mark.parametrize('param, given, words', [
    ('store', 'Paris', 'not in the loaded data'),
    ('year', 2031, 'Valid values: 2025'),
    ('channel', 'Kiosk', 'Valid values: Brick & Mortar, Website'),
    ('by', 'profit', 'Valid values: year, month'),
    ('start_year', [2025, 2026], 'takes one value'),
])
def test_values_not_in_the_data_are_errors_never_guesses(ctx, param, given, words):
    value, err = agent.normalize(param, given, ctx)
    assert value is None and words in err


def test_empty_or_all_means_no_filter(ctx):
    for given in (None, 'All', [], ['All'], ''):
        assert agent.normalize('channel', given, ctx) == (None, None)


# ---------------------------------------------------------------- dispatcher
def test_unknown_tool_is_rejected_and_logged(ctx):
    log = []
    result = agent.run_tool('run_python', {'code': 'print(1)'}, ctx, log)
    assert result.error and 'Unknown tool' in result.error
    assert log[0]['tool'] == 'run_python' and log[0]['status'] == 'error'


def test_unexpected_and_missing_arguments_are_rejected(ctx):
    log = []
    assert 'Unexpected argument' in agent.run_tool(
        'get_total_revenue', {'code': 'x'}, ctx, log).error
    assert 'Missing required argument' in agent.run_tool(
        'get_revenue_breakdown', {}, ctx, log).error
    assert 'Missing required argument' in agent.run_tool(
        'get_revenue_breakdown', {'by': 'All'}, ctx, log).error
    assert [entry['status'] for entry in log] == ['error', 'error', 'error']


def test_bad_value_error_comes_from_the_dispatcher_with_valid_values(ctx):
    result = agent.run_tool('get_store_trends', {'market': '9-Huge'}, ctx, [])
    assert result.error and '4-Large' in result.error


def test_a_crashing_tool_returns_an_error_result_not_a_traceback(ctx, monkeypatch):
    def broken(model, **kwargs):
        raise ValueError('boom')
    monkeypatch.setitem(agent.TOOLS['get_total_revenue'], 'fn', broken)
    log = []
    result = agent.run_tool('get_total_revenue', {}, ctx, log)
    assert result.error == 'The tool failed: ValueError: boom'
    assert log[0]['status'] == 'error'


def test_every_tool_runs_through_the_dispatcher(ctx):
    calls = {'get_total_revenue': {'store': 'Chicago', 'year': 2028},
             'get_revenue_breakdown': {'by': ['category', 'year']},
             'get_monthly_share': {'store': 'SH11'},
             'get_store_trends': {'start_year': 2025, 'end_year': 2029},
             'get_satisfaction_vs_revenue': {},
             'get_data_coverage': {},
             'data_quality_report': {}}
    assert set(calls) == set(agent.TOOLS)
    log = []
    for name, args in calls.items():
        result = agent.run_tool(name, args, ctx, log)
        assert result.error is None, (name, result.error)
    assert [e['tool'] for e in log] == list(calls) and [e['call'] for e in log] == [1, 2, 3, 4, 5, 6, 7]


# ---------------------------------------------------------------- call log
def test_log_entry_records_everything_needed_for_the_tool_call_log(ctx):
    log = []
    agent.run_tool('get_store_trends', {'market': '4-large'}, ctx, log)
    entry = log[0]
    assert set(entry) == {'call', 'time', 'tool', 'arguments', 'arguments_used', 'status',
                          'rows_used', 'duration_ms', 'data', 'result'}
    assert entry['arguments_used'] == {'market': ['4-Large']}
    assert entry['result']['tool'] == 'get_store_trends'
    assert set(entry['result']) >= {'tool', 'value', 'definition', 'scope', 'rows_used', 'caveats'}
    assert entry['data'].startswith('Sales.csv (original (data/)) · ')


def test_tools_called_through_the_dispatcher_do_not_change_the_data(ctx):
    model, tables = ctx.model.copy(), {k: v.copy() for k, v in ctx.tables.items()}
    log = []
    for name in agent.TOOLS:
        agent.run_tool(name, {'by': 'store'} if name == 'get_revenue_breakdown' else {}, ctx, log)
    pd.testing.assert_frame_equal(ctx.model, model)
    for name, table in tables.items():
        pd.testing.assert_frame_equal(ctx.tables[name], table)


# ---------------------------------------------------------------- agent test 5 (updated data)
def test_same_question_after_upload_gives_the_new_answer_and_the_log_shows_it(ctx):
    """Agent test 5 plan: 'What was Chicago's revenue in 2028?' before and after uploading
    data/modified/Sales.csv (the $1,000 test file)."""
    question = {'store': 'Chicago', 'year': 2028}
    before_log, after_log = [], []
    before = agent.run_tool('get_total_revenue', question, ctx, before_log)
    updated = context({'Sales.csv': (DATA / 'modified' / 'Sales.csv').read_bytes()})
    after = agent.run_tool('get_total_revenue', question, updated, after_log)
    assert round(after.value - before.value, 2) == 1000.00
    assert '(original (data/))' in before_log[0]['data']
    assert '(uploaded)' in after_log[0]['data']
    assert before_log[0]['data'] != after_log[0]['data']


# ---------------------------------------------------------------- moved from the starter tests
def test_unsupported_question(ctx):
    out = agent.answer_question('What is the meaning of life?', ctx)
    assert 'cannot answer' in out['findings'] and out['tool_log'] == []


def test_data_quality_question_still_works_through_the_dispatcher(ctx):
    out = agent.answer_question('Are there any missing values?', ctx)
    assert out['tool_log'][0]['tool'] == 'data_quality_report'
    assert out['tool_log'][0]['status'] == 'ok'
