"""Tests for the assistant tools added in Checkpoint 3: get_store_trends,
get_satisfaction_vs_revenue, and get_data_coverage. Each tiny table can be checked by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import analytics  # noqa: E402
import data_prep  # noqa: E402


def sales_rows(spec):
    """Build a sales model from (store, channel, market, city, state, year, category, revenue)."""
    cols = ['Store ID', 'Channel', 'Market', 'City', 'State', 'Year', 'Category', 'Revenue']
    df = pd.DataFrame(spec, columns=cols)
    df['Year'] = df['Year'].astype('Int64')
    df['StoreYear'] = df['Store ID'] + '_' + (df['Year'] % 100).astype(str)
    return df


# ---------------------------------------------------------------- get_store_trends
@pytest.fixture
def trends():
    """2025 -> 2026. Physical: SH01 100 -> 50 (-50%), SH02 200 -> 220 (+10%),
    SH03 1000 -> 800 (-20%), SH04 1000 -> 1100 (+10%). Website SH00 100 -> 300 (+200%).
    SH01's 2025 revenue is split over two rows (Beans 60 + Syrups 40)."""
    W, B = 'Website', 'Brick & Mortar'
    return sales_rows([
        ('SH00', W, '5-Global', None, None, 2025, 'Beans', 100.0),
        ('SH00', W, '5-Global', None, None, 2026, 'Beans', 300.0),
        ('SH01', B, '1-Small', 'Orlando', 'FL', 2025, 'Beans', 60.0),
        ('SH01', B, '1-Small', 'Orlando', 'FL', 2025, 'Syrups', 40.0),
        ('SH01', B, '1-Small', 'Orlando', 'FL', 2026, 'Beans', 50.0),
        ('SH02', B, '1-Small', 'Boston', 'MA', 2025, 'Beans', 200.0),
        ('SH02', B, '1-Small', 'Boston', 'MA', 2026, 'Beans', 220.0),
        ('SH03', B, '4-Large', 'Chicago', 'IL', 2025, 'Beans', 1000.0),
        ('SH03', B, '4-Large', 'Chicago', 'IL', 2026, 'Beans', 800.0),
        ('SH04', B, '4-Large', 'Denver', 'CO', 2025, 'Beans', 1000.0),
        ('SH04', B, '4-Large', 'Denver', 'CO', 2026, 'Beans', 1100.0),
    ])


def test_store_trends_default_is_physical_stores_ranked_by_decline(trends):
    r = analytics.get_store_trends(trends)
    assert r.error is None
    stores = r.value['stores']
    assert [(s['store'], s['change_pct']) for s in stores] == [
        ('SH01', -50.0), ('SH03', -20.0), ('SH02', 10.0), ('SH04', 10.0)]
    assert stores[0]['revenue_2025'] == 100.0  # 60 + 40 added up per store and year
    assert r.value['declined'] == ['SH01', 'SH03']
    assert r.value['largest_decline']['store'] == 'SH01'
    assert r.scope['channel'] == 'Physical stores only (default)'
    assert any('website (SH00) is excluded by default' in c for c in r.caveats)


def test_store_trends_reports_market_tier_rank_and_tier_medians(trends):
    r = analytics.get_store_trends(trends)
    by_store = {s['store']: s for s in r.value['stores']}
    assert by_store['SH03']['market'] == '4-Large' and by_store['SH03']['rank_in_tier'] == 1
    assert by_store['SH04']['rank_in_tier'] == 2
    assert r.value['tiers'] == [
        {'market': '1-Small', 'stores': 2, 'median_change_pct': -20.0, 'stores_declined': 1},
        {'market': '4-Large', 'stores': 2, 'median_change_pct': -5.0, 'stores_declined': 1}]
    assert any('Market tier' in c for c in r.caveats)


def test_store_trends_distance_from_tier_median_and_counts(trends):
    r = analytics.get_store_trends(trends)
    gap = {s['store']: s['vs_tier_median_pts'] for s in r.value['stores']}
    # 1-Small median -20: SH01 -50 -> -30, SH02 +10 -> +30; 4-Large median -5: SH03 -20 -> -15
    assert gap == {'SH01': -30.0, 'SH03': -15.0, 'SH02': 30.0, 'SH04': 15.0}
    assert r.value['stores_compared'] == 4 and r.value['stores_declined'] == 2


def test_store_breakdown_includes_market_tier(trends):
    r = analytics.get_revenue_breakdown(trends, 'store')
    assert {x['store']: x['market'] for x in r.value}['SH03'] == '4-Large'


def test_store_trends_when_no_store_declined(trends):
    trends.loc[4, 'Revenue'] = 150.0   # SH01 2026: 100 -> 150
    trends.loc[8, 'Revenue'] = 1200.0  # SH03 2026: 1000 -> 1200
    r = analytics.get_store_trends(trends)
    assert r.value['declined'] == [] and r.value['largest_decline'] is None
    assert "No store's revenue declined between 2025 and 2026." in r.caveats


def test_store_trends_channel_market_and_category_options(trends):
    web = analytics.get_store_trends(trends, channel='Website')
    assert [s['store'] for s in web.value['stores']] == ['SH00']
    assert any('separate sales channel' in c for c in web.caveats)
    both = analytics.get_store_trends(trends, channel=['Website', 'Brick & Mortar'])
    assert both.value['stores'][-1]['store'] == 'SH00'  # +200%, the largest growth
    large = analytics.get_store_trends(trends, market='4-Large')
    assert [s['store'] for s in large.value['stores']] == ['SH03', 'SH04']
    # Beans only: SH01 60 -> 50 (-16.67%), SH03 1000 -> 800 (-20%), so SH03 declined most
    beans = analytics.get_store_trends(trends, category='Beans')
    assert [(s['store'], s[f'revenue_2025'], s['change_pct']) for s in beans.value['stores'][:2]] \
        == [('SH03', 1000.0, -20.0), ('SH01', 60.0, -16.67)]


def test_store_trends_store_with_no_start_year_sales(trends):
    extra = sales_rows([('SH05', 'Brick & Mortar', '1-Small', 'Tempe', 'AZ', 2026, 'Beans', 90.0)])
    r = analytics.get_store_trends(pd.concat([trends, extra], ignore_index=True))
    assert r.value['stores'][-1]['store'] == 'SH05'
    assert r.value['stores'][-1]['change_pct'] is None
    assert any('no sales in 2025' in c for c in r.caveats)


def test_store_trends_store_with_no_end_year_sales_is_minus_100_percent(trends):
    trends = trends[~((trends['Store ID'] == 'SH02') & (trends['Year'] == 2026))]
    r = analytics.get_store_trends(trends)
    assert r.value['stores'][0] == {**r.value['stores'][0], 'store': 'SH02',
                                    'revenue_2026': 0.0, 'change_pct': -100.0}


@pytest.mark.parametrize('kwargs', [{'start_year': 2031}, {'start_year': 2026, 'end_year': 2025},
                                    {'market': '9-Huge'}, {'channel': 'Kiosk'},
                                    {'market': '5-Global'}])
def test_store_trends_invalid_requests_return_errors(trends, kwargs):
    r = analytics.get_store_trends(trends, **kwargs)
    assert r.error and r.value is None


# ---------------------------------------------------------------- get_satisfaction_vs_revenue
@pytest.fixture
def survey_case():
    """Six physical store-years plus one Website store-year with no survey score.
    Each store-year's revenue is split over two sales rows, as in the real Sales table.
    1-Small: (sat 1, rev 100), (2, 200), (3, 300) -> correlation +1.
    4-Large: (sat 1, rev 1000), (3, 900), (2, 950) -> correlation -1."""
    W, B = 'Website', 'Brick & Mortar'
    store_years = [('SH00', W, '5-Global', 2025, 500.0, None),
                   ('SH01', B, '1-Small', 2025, 100.0, 1.0),
                   ('SH01', B, '1-Small', 2026, 200.0, 2.0),
                   ('SH02', B, '1-Small', 2025, 300.0, 3.0),
                   ('SH03', B, '4-Large', 2025, 1000.0, 1.0),
                   ('SH03', B, '4-Large', 2026, 900.0, 3.0),
                   ('SH04', B, '4-Large', 2025, 950.0, 2.0)]
    rows = []
    for store, channel, market, year, revenue, _ in store_years:
        rows += [(store, channel, market, None, None, year, 'Beans', revenue * 0.6),
                 (store, channel, market, None, None, year, 'Syrups', revenue * 0.4)]
    model = sales_rows(rows)
    survey = pd.DataFrame({
        'Survey ID': [f'{s}_{y % 100}' for s, _, _, y, _, _ in store_years],
        'Store ID': [s for s, *_ in store_years],
        'Year': [f'Y{y}' for _, _, _, y, _, _ in store_years],
        'Satisfaction': [sat for *_, sat in store_years],
        'Interest': [80.0] * len(store_years)})
    return model, survey


def test_satisfaction_uses_one_score_per_store_year(survey_case):
    model, survey = survey_case
    r = analytics.get_satisfaction_vs_revenue(model, survey)
    assert r.error is None
    assert r.value['store_years_used'] == 6       # store-years, not the 12 physical sales rows
    assert r.value['store_years_excluded'] == 1   # the Website store-year
    small = next(t for t in r.value['by_tier'] if t['market'] == '1-Small')
    assert small == {'market': '1-Small', 'store_years': 3, 'correlation': 1.0,
                     'mean_satisfaction': 2.0, 'mean_store_year_revenue': 200.0}
    large = next(t for t in r.value['by_tier'] if t['market'] == '4-Large')
    assert large['correlation'] == -1.0
    check = r.value['merge_check']
    assert check['rows_before'] == check['rows_after'] == 7
    assert check['sum_before'] == check['sum_after'] == 3950.0


def test_satisfaction_overall_correlation_matches_numpy(survey_case):
    model, survey = survey_case
    r = analytics.get_satisfaction_vs_revenue(model, survey)
    expected = np.corrcoef([1, 2, 3, 1, 3, 2], [100, 200, 300, 1000, 900, 950])[0, 1]
    assert r.value['correlation'] == round(expected, 3)


def test_satisfaction_caveats_cover_causation_tiers_survey_and_website(survey_case):
    caveats = ' '.join(analytics.get_satisfaction_vs_revenue(*survey_case).caveats)
    for phrase in ('association, not causation', 'Market tier confounds',
                   'active customers only', '1 Website store-year(s) were excluded',
                   'Based on 6 store-years'):
        assert phrase in caveats


def test_satisfaction_too_few_store_years_gives_no_correlation(survey_case):
    r = analytics.get_satisfaction_vs_revenue(*survey_case, year=2026)
    assert r.value['store_years_used'] == 2 and r.value['correlation'] is None
    assert any('Too few store-years' in c for c in r.caveats)


def test_satisfaction_duplicate_survey_id_is_an_error(survey_case):
    model, survey = survey_case
    r = analytics.get_satisfaction_vs_revenue(model, pd.concat([survey, survey.iloc[[1]]]))
    assert r.error and 'duplicated' in r.error


def test_satisfaction_missing_survey_or_bad_filter_returns_error(survey_case):
    model, survey = survey_case
    assert analytics.get_satisfaction_vs_revenue(model, None).error
    assert analytics.get_satisfaction_vs_revenue(model, survey, market='9-Huge').error


# ---------------------------------------------------------------- get_data_coverage
@pytest.fixture
def coverage_tables(trends, survey_case):
    sales = trends[['Store ID', 'Category', 'Revenue']]
    stores = pd.DataFrame({'ID': ['SH00', 'SH01'], 'PostalCode': [None, '32822']})
    return {'Sales': sales, 'Survey': survey_case[1], 'Stores': stores}


def test_coverage_lists_measures_and_says_profit_is_unavailable(trends, coverage_tables):
    r = analytics.get_data_coverage(trends, coverage_tables)
    assert r.value['measures'] == {'Sales': ['Revenue'], 'Survey': ['Satisfaction', 'Interest']}
    assert r.value['cost_or_profit_columns'] == []
    assert r.value['years'] == [2025, 2026] and r.value['physical_stores'] == 4
    assert r.value['market_tiers'] == ['1-Small', '4-Large', '5-Global']
    assert any('profit and margins cannot be calculated' in c for c in r.caveats)


def test_coverage_notices_a_cost_column_if_one_is_ever_loaded(trends, coverage_tables):
    coverage_tables['Sales'] = coverage_tables['Sales'].assign(**{'Unit Cost': 1.0})
    r = analytics.get_data_coverage(trends, coverage_tables)
    assert r.value['cost_or_profit_columns'] == ['Sales.Unit Cost']
    assert not any('cannot be calculated' in c for c in r.caveats)


# ---------------------------------------------------------------- the real files
@pytest.fixture(scope='module')
def real():
    files, _ = data_prep.collect_files()
    tables, _ = data_prep.load_tables(files)
    return data_prep.build_sales_model(tables)[0], tables


def test_real_store_trends_agree_with_get_revenue_change(real):
    model, _ = real
    r = analytics.get_store_trends(model)
    physical = model.loc[model['Channel'] != analytics.WEBSITE_TYPE, 'Store ID'].nunique()
    assert len(r.value['stores']) == physical
    for s in r.value['stores']:
        change = analytics.get_revenue_change(model, store=s['store']).value
        assert s['change_pct'] == change['change_pct']


def test_real_satisfaction_join_keeps_store_year_revenue(real):
    model, tables = real
    r = analytics.get_satisfaction_vs_revenue(model, tables['Survey'])
    survey = tables['Survey']
    website = model.loc[model['Channel'] == analytics.WEBSITE_TYPE, 'StoreYear'].nunique()
    assert r.value['store_years_used'] == survey['Satisfaction'].notna().sum()
    assert r.value['store_years_excluded'] == website
    check = r.value['merge_check']
    assert check['rows_before'] == check['rows_after'] == model['StoreYear'].nunique()
    assert check['sum_before'] == check['sum_after'] == model['Revenue'].sum()


def test_real_coverage_has_no_cost_columns(real):
    model, tables = real
    r = analytics.get_data_coverage(model, tables)
    assert r.value['cost_or_profit_columns'] == []
    assert r.value['years'] == sorted(model['Year'].dropna().unique().tolist())


def test_tools_do_not_change_the_loaded_data(real):
    model, tables = real
    before = model.copy(), tables['Survey'].copy()
    analytics.get_store_trends(model, channel=['Website', 'Brick & Mortar'])
    analytics.get_satisfaction_vs_revenue(model, tables['Survey'])
    analytics.get_data_coverage(model, tables)
    pd.testing.assert_frame_equal(model, before[0])
    pd.testing.assert_frame_equal(tables['Survey'], before[1])


# ---------------------------------------------------------------- correlation wording
@pytest.mark.parametrize('r, word', [(0.0, 'near zero'), (-0.09, 'near zero'), (0.18, 'weak'),
                                     (-0.29, 'weak'), (0.3, 'moderate'), (0.5, 'strong'),
                                     (-1.0, 'strong')])
def test_correlation_strength_bands(r, word):
    assert analytics.correlation_strength(r) == word


def test_tier_caveat_is_built_from_the_results(survey_case):
    caveats = analytics.get_satisfaction_vs_revenue(*survey_case).caveats
    assert ('Within Market tiers, the correlation is strong in 1-Small (+1.00, n = 3, a small '
            'sample) and 4-Large (-1.00, n = 3, a small sample).') in caveats


def test_real_tier_caveat_labels_each_tier_and_flags_small_samples(real):
    model, tables = real
    r = analytics.get_satisfaction_vs_revenue(model, tables['Survey'])
    caveat = next(c for c in r.caveats if c.startswith('Within Market tiers'))
    # "...is near zero in A (...), B (...), and C (...); weak in D (...)." -> {word: text}
    groups = dict(part.split(' in ', 1) for part in
                  caveat.removeprefix('Within Market tiers, the correlation is ')
                  .rstrip('.').split('; '))
    for t in r.value['by_tier']:
        small = ', a small sample' if t['store_years'] < analytics.SMALL_SAMPLE else ''
        fragment = f"{t['market']} ({t['correlation']:+.2f}, n = {t['store_years']}{small})"
        assert fragment in groups[analytics.correlation_strength(t['correlation'])]
