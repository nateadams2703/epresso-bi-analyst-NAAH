"""Tests use a tiny made-up table so you can check every answer by hand."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import agent  # noqa: E402
import analytics  # noqa: E402


@pytest.fixture
def df():
    return pd.DataFrame({
        'store': ['A', 'A', 'B', 'B', 'B'],
        'channel': ['web', 'shop', 'web', 'shop', 'shop'],
        'amount': [100, 200, 50, None, 150],
    })


def test_total_all_rows(df):
    r = analytics.get_total(df, 'amount')
    assert r.value == 500 and r.rows_used == 4
    assert any('missing' in c for c in r.caveats)


def test_total_filtered(df):
    assert analytics.get_total(df, 'amount', {'store': 'A'}).value == 300


def test_unknown_filter_value_returns_error_not_zero(df):
    r = analytics.get_total(df, 'amount', {'store': 'Z'})
    assert r.error and r.value is None


def test_group_total(df):
    assert analytics.group_total(df, 'amount', 'store').value == {'A': 300.0, 'B': 200.0}


def test_data_quality(df):
    r = analytics.data_quality_report(df)
    assert r.value['columns_with_missing'] == {'amount': 1}


def test_merge_without_fan_out(df):
    stores = pd.DataFrame({'store': ['A', 'B'], 'city': ['X', 'Y']})
    _, rep = analytics.check_merge(df, stores, on='store', value_col='amount')
    assert not rep['changed']


def test_merge_fan_out_is_detected(df):
    dup = pd.DataFrame({'store': ['A', 'A', 'B'], 'city': ['X', 'X2', 'Y']})
    _, rep = analytics.check_merge(df, dup, on='store', value_col='amount')
    assert rep['changed'] and rep['sum_after'] > rep['sum_before']


def test_dispatcher_rejects_unknown_tool_and_arguments(df):
    log = []
    assert agent.run_tool('run_python', {}, df, log).error
    assert agent.run_tool('get_total', {'value_col': 'amount', 'code': 'x'}, df, log).error


def test_unsupported_question(df):
    out = agent.answer_question('What is the meaning of life?', df)
    assert 'cannot answer' in out['findings']


# ------------------------------------------------------ E-Presso revenue
@pytest.fixture
def model():
    """A tiny sales model: 2 years, 2 channels, 3 stores. Total = 1,000."""
    return pd.DataFrame({
        'Year': pd.array([2025, 2025, 2025, 2026, 2026, 2026], dtype='Int64'),
        'Channel': ['Website', 'Brick & Mortar', 'Brick & Mortar'] * 2,
        'Store ID': ['SH00', 'SH01', 'SH02'] * 2,
        'Category': ['Beans', 'Beans', 'Syrups'] * 2,
        'Revenue': [100.0, 50.0, 25.0, 400.0, 300.0, 125.0],
    })


def test_total_revenue_all(model):
    r = analytics.get_total_revenue(model)
    assert r.value == 1000 and r.rows_used == 6 and r.error is None
    assert r.scope == {'year': 'All', 'channel': 'All', 'store': 'All', 'category': 'All'}
    assert 'not profit' in r.caveats[0]


def test_total_revenue_by_channel_and_year(model):
    assert analytics.get_total_revenue(model, channel='Website').value == 500
    assert analytics.get_total_revenue(model, channel='Brick & Mortar', year=2026).value == 425


def test_year_as_text_and_lists_work(model):
    assert analytics.get_total_revenue(model, year='2025').value == 175
    r = analytics.get_total_revenue(model, store=['SH01', 'SH02'], category='All')
    assert r.value == 500 and r.scope['store'] == ['SH01', 'SH02'] and r.scope['category'] == 'All'


def test_unknown_store_or_year_returns_error_not_zero(model):
    for kwargs in ({'store': 'SH99'}, {'year': 2031}, {'channel': 'Kiosk'}):
        r = analytics.get_total_revenue(model, **kwargs)
        assert r.error and r.value is None


def test_missing_model_returns_error(model):
    r = analytics.get_total_revenue(None)
    assert r.error and 'did not load' in r.error


def test_missing_revenue_and_channel_are_reported(model):
    model.loc[0, 'Revenue'] = None
    model.loc[1, 'Channel'] = None
    r = analytics.get_total_revenue(model, channel='Brick & Mortar')
    assert r.value == 450  # 25 + 300 + 125; the store with no channel is left out
    assert any('no channel' in c for c in r.caveats)
    assert any('1 row(s) with missing revenue' in c
               for c in analytics.get_total_revenue(model).caveats)
