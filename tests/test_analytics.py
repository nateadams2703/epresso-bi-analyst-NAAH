"""Tests use a tiny made-up table so you can check every answer by hand."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
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


# The starter's dispatcher tests moved to tests/test_agent.py (new Context signature).


# ------------------------------------------------------ E-Presso revenue
@pytest.fixture
def model():
    """A tiny sales model: 2 years, 2 channels, 3 stores (two of them in Orlando).
    Total = 1,000. By year: 2025 = 175, 2026 = 825. By month: Jan = 500, Dec = 500."""
    return pd.DataFrame({
        'Year': pd.array([2025, 2025, 2025, 2026, 2026, 2026], dtype='Int64'),
        'Month': pd.array([1, 12, 12, 1, 12, 12], dtype='Int64'),
        'Channel': ['Website', 'Brick & Mortar', 'Brick & Mortar'] * 2,
        'Store ID': ['SH00', 'SH01', 'SH02'] * 2,
        'City': [None, 'Orlando', 'Orlando'] * 2,
        'State': [None, 'FL', 'FL'] * 2,
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


def test_no_matching_sales_is_zero_with_a_caveat_not_an_error(model):
    r = analytics.get_total_revenue(model, channel='Website', store='SH01')
    assert r.error is None and r.value == 0 and r.rows_used == 0
    assert 'No sales match these filters.' in r.caveats
    assert analytics.get_revenue_breakdown(model, 'year', channel='Website', store='SH01').value == []


# ------------------------------------------------------ breakdowns
def test_breakdown_by_year(model):
    r = analytics.get_revenue_breakdown(model, 'year')
    assert r.value == [{'year': 2025, 'revenue': 175.0, 'share_pct': 17.5},
                       {'year': 2026, 'revenue': 825.0, 'share_pct': 82.5}]
    assert type(r.value[0]['year']) is int  # plain Python, not numpy


def test_breakdown_by_category_and_year(model):
    r = analytics.get_revenue_breakdown(model, ['category', 'year'])
    revenue = {(x['category'], x['year']): x['revenue'] for x in r.value}
    assert revenue == {('Beans', 2025): 150.0, ('Beans', 2026): 700.0,
                       ('Syrups', 2025): 25.0, ('Syrups', 2026): 125.0}


def test_breakdown_adds_up_to_total_under_filters(model):
    for filters in ({}, {'channel': 'Brick & Mortar'}, {'year': 2026, 'category': 'Beans'}):
        parts = analytics.get_revenue_breakdown(model, ['year', 'channel'], **filters)
        total = analytics.get_total_revenue(model, **filters)
        assert sum(x['revenue'] for x in parts.value) == total.value
        assert parts.scope == total.scope


def test_breakdown_by_store_keeps_orlando_stores_separate(model):
    r = analytics.get_revenue_breakdown(model, 'store')
    assert [(x['store_label'], x['revenue']) for x in r.value] == [
        ('SH00 – Website', 500.0), ('SH01 – Orlando, FL', 350.0), ('SH02 – Orlando, FL', 150.0)]


def test_breakdown_rejects_dimensions_outside_the_fixed_list(model):
    for by in ('profit', ['year', 'year'], ['year', 'month', 'store'], []):
        r = analytics.get_revenue_breakdown(model, by)
        assert r.error and r.value is None


def test_breakdown_reports_rows_with_blank_group(model):
    model.loc[0, 'Channel'] = None  # row 0 is $100 of Website revenue in 2025
    r = analytics.get_revenue_breakdown(model, 'channel')
    assert r.value == [{'channel': 'Brick & Mortar', 'revenue': 500.0, 'share_pct': 55.5556},
                       {'channel': 'Website', 'revenue': 400.0, 'share_pct': 44.4444}]
    assert any('1 row(s) with a blank channel' in c for c in r.caveats)


# ------------------------------------------------------ monthly share
def test_monthly_share_uses_total_for_current_filters(model):
    def shares(**filters):
        r = analytics.get_monthly_share(model, **filters)
        return {x['month']: x['share_pct'] for x in r.value}
    assert shares() == {1: 50.0, 12: 50.0}               # 500 / 1,000 each
    assert shares(year=2025) == {1: 57.1429, 12: 42.8571}  # 100 / 175 and 75 / 175
    assert shares(store='SH02') == {12: 100.0}            # SH02 only sells in December
    r = analytics.get_monthly_share(model)
    assert r.tool == 'get_monthly_share' and 'not a percent of each year' in r.caveats[-1]


def test_monthly_share_error_keeps_its_own_tool_name(model):
    r = analytics.get_monthly_share(model, store='SH99')
    assert r.error and r.tool == 'get_monthly_share'


# ------------------------------------------------------ revenue change
def test_revenue_change_first_to_last_year(model):
    r = analytics.get_revenue_change(model)
    assert r.value == {'first_year': 2025, 'last_year': 2026, 'first_revenue': 175.0,
                       'last_revenue': 825.0, 'change': 650.0, 'change_pct': 371.43}
    assert analytics.get_revenue_change(model, store='SH01').value['change_pct'] == 500.0


def test_revenue_change_needs_two_years(model):
    r = analytics.get_revenue_change(model, year=2026)
    assert r.error is None and r.value is None
    assert any('two years' in c for c in r.caveats)


# ------------------------------------------------------ the real files vs. Power BI
@pytest.fixture(scope='module')
def real_model():
    import data_prep
    files, _ = data_prep.collect_files()
    tables, _ = data_prep.load_tables(files)
    return data_prep.build_sales_model(tables)[0]


def test_monthly_share_matches_power_bi_labels(real_model):
    """Power BI data labels from docs/powerbi/ screenshots (see docs/validation-table.md)."""
    company = {1: 7.74, 2: 3.83, 4: 5.15, 6: 6.50, 8: 6.45, 10: 8.31, 11: 12.71, 12: 25.61}
    chicago = {1: 7.87, 2: 3.91, 4: 5.19, 6: 6.51, 8: 6.37, 10: 8.52, 11: 13.21, 12: 24.75}
    for labels, filters in ((company, {}), (chicago, {'store': 'SH11'})):
        r = analytics.get_monthly_share(real_model, **filters)
        got = {x['month']: round(x['share_pct'], 2) for x in r.value}
        assert {m: got[m] for m in labels} == labels
        # each share is rounded to 4 decimals, so the twelve can miss 100 by a hair
        assert abs(sum(x['share_pct'] for x in r.value) - 100) < 0.001


def test_category_by_year_adds_up_to_yearly_totals(real_model):
    parts = analytics.get_revenue_breakdown(real_model, ['category', 'year']).value
    for year in {x['year'] for x in parts}:
        assert round(sum(x['revenue'] for x in parts if x['year'] == year), 2) == \
            analytics.get_total_revenue(real_model, year=year).value
