"""Tests for data_prep.py. Each test builds a tiny made-up E-Presso dataset, breaks one
thing on purpose, and checks that the problem is reported in plain English."""
import io
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import data_prep  # noqa: E402


@pytest.fixture
def dfs():
    """Three stores (website + two physical), one product, one sales row per store."""
    return {
        'Stores': pd.DataFrame({
            'ID': ['SH00', 'SH01', 'SH02'],
            'City': [None, 'Boston', 'Austin'],
            'State': [None, 'MA', 'TX'],
            'PostalCode': [None, '02134', '78701'],
            'Phone': ['1-800-555-0000', '(617) 555-0100', '(512) 555-0100'],
            'StoreType': ['Website', 'Brick & Mortar', 'Brick & Mortar'],
            'Market': ['5-Global', '1-Small', '1-Small'],
            'Location': ['Website', 'East', 'Southwest'],
            'Manager': ['A, B', 'C, D', 'E, F'],
        }),
        'Categories': pd.DataFrame({'Category ID': ['C1'], 'Category': ['Beans']}),
        'Products': pd.DataFrame({'Product ID': ['P01'], 'Product': ['House Blend']}),
        'Sales': pd.DataFrame({
            'Sales ID': ['S1', 'S2', 'S3'],
            'Date': ['2025-01-31'] * 3,
            'Store ID': ['SH00', 'SH01', 'SH02'],
            'StoreYear': ['SH00_25', 'SH01_25', 'SH02_25'],
            'Category ID': ['C1'] * 3,
            'Product ID': ['P01'] * 3,
            'Revenue': [100.0, 200.0, 300.0],
        }),
        'Survey': pd.DataFrame({
            'Survey ID': ['SH00_25', 'SH01_25', 'SH02_25'],
            'Store ID': ['SH00', 'SH01', 'SH02'],
            'Year': ['Y2025'] * 3,
            'Satisfaction': [None, 4.5, 3.0],
            'Interest': [None, 80, 70],
        }),
    }


def to_uploads(dfs):
    """Turn the DataFrames into file bytes, laid out like the real files."""
    uploads = {}
    for table, df in dfs.items():
        name = data_prep.TABLE_SPECS[table]['file']
        if name.endswith('.xlsx'):
            buffer = io.BytesIO()
            df.to_excel(buffer, sheet_name='Survey Results', startrow=2, index=False)
            uploads[name] = buffer.getvalue()
        else:
            sep = '\t' if table == 'Stores' else ','  # the real Stores file is tab-separated
            uploads[name] = df.to_csv(index=False, sep=sep).encode()
    return uploads


def load(dfs, tmp_path):
    """Load everything as uploads, with an empty data/ folder behind them."""
    files, problems = data_prep.collect_files(to_uploads(dfs), data_dir=tmp_path)
    tables, load_problems = data_prep.load_tables(files)
    return tables, problems + load_problems


def notes_text(tables, level=None):
    notes = data_prep.data_quality_notes(tables)
    if level:
        notes = notes[notes['level'] == level]
    return ' | '.join(notes['note'])


# ---------------------------------------------------------------- loading
def test_clean_dataset_loads_with_no_problems(dfs, tmp_path):
    tables, problems = load(dfs, tmp_path)
    assert problems == []
    assert set(tables) == set(data_prep.TABLE_SPECS)


def test_tab_separated_stores_keeps_zip_as_text(dfs, tmp_path):
    tables, _ = load(dfs, tmp_path)
    stores = tables['Stores'].set_index('ID')
    assert stores.loc['SH01', 'PostalCode'] == '02134'  # leading zero kept
    assert pd.isna(stores.loc['SH00', 'PostalCode'])     # blank stays blank


def test_types_are_fixed(dfs, tmp_path):
    tables, _ = load(dfs, tmp_path)
    assert pd.api.types.is_datetime64_any_dtype(tables['Sales']['Date'])
    assert tables['Sales']['Revenue'].sum() == 600


def test_upload_replaces_original_file(dfs, tmp_path):
    (tmp_path / 'Categories.csv').write_text('Category ID,Category\nC9,Original\n')
    uploads = to_uploads(dfs)
    files, _ = data_prep.collect_files({'Categories.csv': uploads['Categories.csv']}, tmp_path)
    assert files['Categories']['source'] == 'uploaded'
    tables, _ = data_prep.load_tables(files)
    assert list(tables['Categories']['Category ID']) == ['C1']


def test_original_file_used_when_nothing_uploaded(tmp_path):
    (tmp_path / 'Categories.csv').write_text('Category ID,Category\nC9,Original\n')
    files, problems = data_prep.collect_files(None, tmp_path)
    assert files['Categories']['source'] == 'original (data/)'
    assert len(problems) == 4  # the other four files are missing, and each is named
    assert any('Sales.csv' in p for p in problems)


def test_unknown_upload_name_is_reported(dfs, tmp_path):
    uploads = to_uploads(dfs)
    uploads['sales_v2.csv'] = uploads['Sales.csv']
    _, problems = data_prep.collect_files(uploads, tmp_path)
    assert any('sales_v2.csv' in p and 'was not used' in p for p in problems)


def test_missing_column_gives_plain_message(dfs, tmp_path):
    dfs['Sales'] = dfs['Sales'].drop(columns='Revenue')
    tables, problems = load(dfs, tmp_path)
    assert 'Sales' not in tables
    assert any('missing required column(s): Revenue' in p for p in problems)


def test_unreadable_revenue_becomes_blank_and_is_reported(dfs, tmp_path):
    dfs['Sales']['Revenue'] = dfs['Sales']['Revenue'].astype(object)
    dfs['Sales'].loc[0, 'Revenue'] = 'abc'
    tables, problems = load(dfs, tmp_path)
    assert any('1 value(s) in Sales.csv column Revenue' in p for p in problems)
    assert tables['Sales']['Revenue'].sum() == 500
    assert 'left out of revenue totals' in notes_text(tables, 'Review')


# ---------------------------------------------------------------- checks
def test_duplicate_key_is_detected(dfs, tmp_path):
    dfs['Products'] = pd.DataFrame({'Product ID': ['P01', 'P01'], 'Product': ['A', 'B']})
    tables, _ = load(dfs, tmp_path)
    row = data_prep.key_checks(tables).set_index('table').loc['Products']
    assert row['duplicate keys'] == 1 and not row['key is unique']


def test_unmatched_store_is_reported(dfs, tmp_path):
    dfs['Sales'].loc[2, 'Store ID'] = 'SH99'
    tables, _ = load(dfs, tmp_path)
    row = data_prep.relationship_checks(tables).set_index('from').loc['Sales.Store ID']
    assert row['unmatched rows'] == 1 and row['examples'] == 'SH99'


def test_every_key_matches_in_clean_data(dfs, tmp_path):
    tables, _ = load(dfs, tmp_path)
    assert data_prep.relationship_checks(tables)['unmatched rows'].sum() == 0


# ---------------------------------------------------------- data quality
def test_website_blanks_are_one_expected_note_but_other_blanks_need_review(dfs, tmp_path):
    dfs['Stores'].loc[2, 'City'] = None  # SH02 is a physical store
    tables, _ = load(dfs, tmp_path)
    notes = data_prep.data_quality_notes(tables)
    expected = notes[notes['level'] == 'Expected']
    assert len(expected) == 1  # every Website blank, in both tables, in one note
    assert expected.iloc[0]['note'] == (
        'Blank values on Website rows are expected: Stores City, State, PostalCode '
        '(1 Website row(s): the website has no physical address); Survey Satisfaction, '
        'Interest (1 Website row(s): no in-store survey is taken for the website).')
    assert '1 blank City value(s).' in notes_text(tables, 'Review')  # SH02, not the website


def test_notes_are_ordered_review_info_expected_with_a_summary(dfs, tmp_path):
    dfs['Stores'].loc[1, 'Phone'] = '617) 555-0100'                        # Review
    dfs['Stores'].loc[2, ['City', 'State']] = ['Boston', 'MA']             # Info: 2 in Boston
    dfs['Stores'].loc[2, 'Location'] = 'East'
    tables, _ = load(dfs, tmp_path)
    notes = data_prep.data_quality_notes(tables)
    assert list(notes['level']) == ['Review', 'Info', 'Expected']
    assert data_prep.notes_summary(notes) == '1 to review · 1 info · 1 expected'


def test_malformed_phone_is_flagged(dfs, tmp_path):
    dfs['Stores'].loc[1, 'Phone'] = '617) 555-0100'
    tables, _ = load(dfs, tmp_path)
    assert 'SH01 phone number "617) 555-0100"' in notes_text(tables, 'Review')


def test_location_mismatch_is_a_possible_inconsistency_not_an_error(dfs, tmp_path):
    dfs['Stores'].loc[1, 'Location'] = 'Southwest'  # Boston, MA
    tables, _ = load(dfs, tmp_path)
    review = notes_text(tables, 'Review')
    assert 'Possible Location inconsistency to review: SH01 (Boston, MA)' in review
    notes = data_prep.data_quality_notes(tables)
    assert set(notes['level']) <= {'Expected', 'Info', 'Review'}
    # the "sales territories" caveat is stored once for the topic, not repeated in each note
    location = notes[notes['topic'] == 'location']
    assert len(location) == 1 and 'sales territories' not in location.iloc[0]['note']
    assert 'sales territories' in data_prep.TOPIC_CAVEATS['location']


def test_same_state_with_two_locations_is_flagged(dfs, tmp_path):
    extra = pd.DataFrame({'ID': ['SH03'], 'City': ['Dallas'], 'State': ['TX'],
                          'PostalCode': ['75201'], 'Phone': ['(214) 555-0100'],
                          'StoreType': ['Brick & Mortar'], 'Market': ['1-Small'],
                          'Location': ['South'], 'Manager': ['G, H']})
    dfs['Stores'] = pd.concat([dfs['Stores'], extra], ignore_index=True)
    tables, _ = load(dfs, tmp_path)
    review = notes_text(tables, 'Review')
    # TX accepts both South and Southwest, so only the same-state rule fires.
    assert 'stores in TX have different Location values (SH02 = Southwest, SH03 = South)' in review
    assert 'SH03 (Dallas, TX)' not in review


# ---------------------------------------------------------- the real files
def test_original_data_files_load_cleanly():
    files, problems = data_prep.collect_files()
    tables, load_problems = data_prep.load_tables(files)
    assert problems + load_problems == []
    assert data_prep.key_checks(tables)['key is unique'].all()
    assert data_prep.relationship_checks(tables)['unmatched rows'].sum() == 0
    # SH11 phone, SH07 NY, FL and NC Location pairs / Orlando's two stores / Website blanks
    notes = data_prep.data_quality_notes(tables)
    assert data_prep.notes_summary(notes) == '4 to review · 1 info · 1 expected'
    assert (notes['topic'] == 'location').sum() == 3


# ---------------------------------------------------------- sales model
def test_clean_joins_keep_rows_and_revenue(dfs, tmp_path):
    tables, _ = load(dfs, tmp_path)
    model, log, problems = data_prep.build_sales_model(tables)
    assert problems == []
    assert len(model) == 3 and model['Revenue'].sum() == 600
    assert log['unchanged'].all() and (log['unmatched rows'] == 0).all()
    by_channel = model.groupby('Channel')['Revenue'].sum().to_dict()
    assert by_channel == {'Website': 100, 'Brick & Mortar': 500}
    assert set(model['Category']) == {'Beans'} and set(model['Product']) == {'House Blend'}


def test_duplicated_store_id_stops_with_fan_out_message(dfs, tmp_path):
    dfs['Stores'] = pd.concat([dfs['Stores'], dfs['Stores'].iloc[[1]]], ignore_index=True)
    tables, _ = load(dfs, tmp_path)
    model, log, problems = data_prep.build_sales_model(tables)
    assert model is None  # inflated revenue is never handed to the dashboard
    assert 'revenue from 600.00 to 800.00' in problems[0]  # SH01's 200 counted twice
    assert not log.iloc[-1]['unchanged']


def test_unknown_store_keeps_its_revenue_with_blank_channel(dfs, tmp_path):
    dfs['Sales'].loc[2, 'Store ID'] = 'SH99'
    tables, _ = load(dfs, tmp_path)
    model, log, _ = data_prep.build_sales_model(tables)
    assert model['Revenue'].sum() == 600
    assert pd.isna(model.loc[model['Store ID'] == 'SH99', 'Channel']).all()
    assert log.set_index('merge')['unmatched rows'].iloc[0] == 1


def test_month_comes_from_date_even_when_not_month_end(dfs, tmp_path):
    dfs['Sales'].loc[0, 'Date'] = '2028-02-28'  # 2028 is a leap year
    tables, _ = load(dfs, tmp_path)
    model, _, _ = data_prep.build_sales_model(tables)
    assert (model.loc[0, 'Year'], model.loc[0, 'Month']) == (2028, 2)


def test_missing_lookup_table_is_reported_but_model_still_built(dfs, tmp_path):
    dfs['Products'] = dfs['Products'].drop(columns='Product')
    tables, _ = load(dfs, tmp_path)
    model, _, problems = data_prep.build_sales_model(tables)
    assert 'Channel' in model.columns and 'Product' not in model.columns
    assert any('Products table did not load' in p for p in problems)


def test_original_data_joins_keep_rows_and_revenue():
    files, _ = data_prep.collect_files()
    tables, _ = data_prep.load_tables(files)
    model, log, problems = data_prep.build_sales_model(tables)
    assert problems == []
    assert len(model) == len(tables['Sales'])
    assert model['Revenue'].sum() == tables['Sales']['Revenue'].sum()
    assert log['unchanged'].all() and (log['unmatched rows'] == 0).all()
