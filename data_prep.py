"""Data preparation: load the five E-Presso tables, fix data types, and check them.
Keep Streamlit code OUT of this file so every function can be tested on its own.

Loading is two steps, so the app can cache on the file CONTENTS:
  collect_files()  picks a file for each table (an upload, or the original in data/)
  load_tables()    turns those file bytes into checked DataFrames
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

import analytics

DATA_DIR = Path(__file__).parent / 'data'

# What the app expects. The Project Guide says updated data keeps the same file names,
# sheet names, and column names, so they are safe to write down here.
# 'text' columns are read as text so IDs and ZIP codes never become numbers
# (otherwise ZIP 02134 would lose its leading zero).
TABLE_SPECS = {
    'Stores': {
        'file': 'Support_EX_B_Stores.csv',  # tab-separated despite .csv; load_table sniffs it
        'read': {},
        'columns': ['ID', 'City', 'State', 'PostalCode', 'Phone', 'StoreType', 'Market',
                    'Location', 'Manager'],
        'key': 'ID',
        'text': ['ID', 'PostalCode', 'Phone'],
    },
    'Categories': {
        'file': 'Categories.csv',
        'read': {},
        'columns': ['Category ID', 'Category'],
        'key': 'Category ID',
        'text': ['Category ID'],
    },
    'Products': {
        'file': 'Products.csv',
        'read': {},
        'columns': ['Product ID', 'Product'],
        'key': 'Product ID',
        'text': ['Product ID'],
    },
    'Sales': {
        'file': 'Sales.csv',
        'read': {},
        'columns': ['Sales ID', 'Date', 'Store ID', 'StoreYear', 'Category ID', 'Product ID',
                    'Revenue'],
        'key': 'Sales ID',
        'text': ['Sales ID', 'Store ID', 'StoreYear', 'Category ID', 'Product ID'],
        'numbers': ['Revenue'],
        'dates': ['Date'],
    },
    'Survey': {
        'file': 'Support_EX_B_Survey.xlsx',
        'read': {'sheet_name': 'Survey Results', 'header': 2},  # title + blank row above headers
        'columns': ['Survey ID', 'Store ID', 'Year', 'Satisfaction', 'Interest'],
        'key': 'Survey ID',
        'text': ['Survey ID', 'Store ID', 'Year'],
        'numbers': ['Satisfaction', 'Interest'],
    },
}

# Planned joins: (many-side table, column) -> (one-side table, key column).
# See docs/grain-statements.md. Sales -> Stores is direct, unlike our Power BI model.
RELATIONSHIPS = [
    ('Sales', 'Store ID', 'Stores', 'ID'),
    ('Sales', 'Product ID', 'Products', 'Product ID'),
    ('Sales', 'Category ID', 'Categories', 'Category ID'),
    ('Sales', 'StoreYear', 'Survey', 'Survey ID'),
    ('Survey', 'Store ID', 'Stores', 'ID'),
]


# ---------------------------------------------------------------- loading
def collect_files(uploads: dict[str, bytes] | None = None, data_dir: Path = DATA_DIR):
    """Pick one file per table. An uploaded file with the expected name replaces the
    original in data/. Returns (files, problems); files[table] = {name, bytes, source}."""
    uploads = {name.lower(): (name, data) for name, data in (uploads or {}).items()}
    expected = [spec['file'] for spec in TABLE_SPECS.values()]
    problems = [f'Uploaded file "{name}" was not used: its name does not match an expected '
                f'file ({", ".join(expected)}).'
                for lower, (name, _) in uploads.items()
                if lower not in {e.lower() for e in expected}]
    files = {}
    for table, spec in TABLE_SPECS.items():
        upload = uploads.get(spec['file'].lower())
        path = Path(data_dir) / spec['file']
        if upload:
            files[table] = {'name': spec['file'], 'bytes': upload[1], 'source': 'uploaded'}
        elif path.exists():
            files[table] = {'name': spec['file'], 'bytes': path.read_bytes(),
                            'source': 'original (data/)'}
        else:
            problems.append(f'No file for the {table} table: expected {spec["file"]}.')
    return files, problems


def load_tables(files: dict) -> tuple[dict, list]:
    """Read each file using its spec, check required columns, and fix data types.
    A table that can't be read or is missing a column is left out with a plain message."""
    tables, problems = {}, []
    for table, f in files.items():
        spec = TABLE_SPECS[table]
        try:
            df = analytics.load_table(f['bytes'], f['name'], **spec['read'],
                                      dtype={col: str for col in spec['text']})
        except Exception as exc:  # a plain message for the app instead of a traceback
            problems.append(f'Could not read {f["name"]} ({table} table): {exc}')
            continue
        missing = [col for col in spec['columns'] if col not in df.columns]
        if missing:
            problems.append(f'{f["name"]} is missing required column(s): {", ".join(missing)}. '
                            f'The {table} table was not loaded.')
            continue
        tables[table] = _fix_types(df, spec, f['name'], problems)
    return tables, problems


def _fix_types(df: pd.DataFrame, spec: dict, filename: str, problems: list) -> pd.DataFrame:
    """Convert number and date columns. Values that can't be converted become blank,
    and we say how many, so nothing disappears silently."""
    df = df.copy()
    converters = [(col, 'a number', lambda s: pd.to_numeric(s, errors='coerce'))
                  for col in spec.get('numbers', [])]
    converters += [(col, 'a date', lambda s: pd.to_datetime(s, errors='coerce'))
                   for col in spec.get('dates', [])]
    for col, kind, convert in converters:
        converted = convert(df[col])
        n_bad = int((converted.isna() & df[col].notna()).sum())
        if n_bad:
            problems.append(f'{n_bad} value(s) in {filename} column {col} could not be read as '
                            f'{kind} and are treated as blank.')
        df[col] = converted
    return df


# ---------------------------------------------------------------- checks
def key_checks(tables: dict) -> pd.DataFrame:
    """One row per table: is the key column unique and never blank?
    The grain statements depend on this."""
    rows = []
    for table, df in tables.items():
        key = TABLE_SPECS[table]['key']
        n_blank = int(df[key].isna().sum())
        n_dup = int(df[key].dropna().duplicated().sum())
        rows.append({'table': table, 'key': key, 'rows': len(df), 'blank keys': n_blank,
                     'duplicate keys': n_dup, 'key is unique': n_blank == 0 and n_dup == 0})
    return pd.DataFrame(rows)


def relationship_checks(tables: dict) -> pd.DataFrame:
    """For each planned join, count rows whose key has no match in the lookup table.
    Unmatched rows would drop out of (or go blank in) joined results."""
    rows = []
    for many, col, one, key in RELATIONSHIPS:
        if many not in tables or one not in tables:
            continue
        values = tables[many][col]
        unmatched = values[~values.isin(set(tables[one][key].dropna()))]
        examples = sorted(map(str, unmatched.dropna().unique()))[:5]
        if unmatched.isna().any():
            examples.append('(blank)')
        rows.append({'from': f'{many}.{col}', 'to': f'{one}.{key}', 'rows checked': len(values),
                     'unmatched rows': len(unmatched), 'examples': ', '.join(examples)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------- joins
# What each lookup table adds to Sales: {source column: name in the model}.
# Stores' ID is renamed to 'Store ID' so check_merge() can join on one shared column name,
# and StoreType is renamed 'Channel' because that is what it means for revenue.
# The survey is NOT joined here: its grain is store x year, so joining it to Sales would
# repeat each satisfaction score on ~240 rows (see docs/grain-statements.md).
LOOKUPS = [
    ('Stores', 'Store ID', {'ID': 'Store ID', 'StoreType': 'Channel', 'City': 'City',
                            'State': 'State', 'Location': 'Location', 'Market': 'Market'}),
    ('Products', 'Product ID', {'Product ID': 'Product ID', 'Product': 'Product'}),
    ('Categories', 'Category ID', {'Category ID': 'Category ID', 'Category': 'Category'}),
]


def build_sales_model(tables: dict):
    """Join Sales to Stores, Products, and Categories, and add Year and Month.
    The model keeps the Sales grain (one row per store x product x month).
    Every join goes through check_merge(); if one changes the row count or the revenue
    total, we stop and return no model, because its revenue could not be trusted.
    Returns (model or None, merge_log, problems)."""
    if 'Sales' not in tables:
        return None, pd.DataFrame(), ['The Sales table did not load, so revenue cannot be '
                                      'calculated.']
    model = tables['Sales']
    log, problems = [], []
    for table, key, columns in LOOKUPS:
        if table not in tables:
            problems.append(f'The {table} table did not load, so its columns '
                            f'({", ".join(c for c in columns.values() if c != key)}) are '
                            f'missing from the sales model.')
            continue
        lookup = tables[table][list(columns)].rename(columns=columns)
        unmatched = int((~model[key].isin(lookup[key].dropna())).sum())
        model, report = analytics.check_merge(model, lookup, on=key, value_col='Revenue')
        log.append({'merge': f'Sales → {table} (on {key})',
                    'rows before': report['rows_before'], 'rows after': report['rows_after'],
                    'revenue before': report['sum_before'], 'revenue after': report['sum_after'],
                    'unmatched rows': unmatched, 'unchanged': not report['changed']})
        if report['changed']:
            problems.append(f'Joining {table} changed the Sales rows from '
                            f'{report["rows_before"]:,} to {report["rows_after"]:,} and revenue '
                            f'from {report["sum_before"]:,.2f} to {report["sum_after"]:,.2f}. '
                            f'Usually this means a duplicated {key} in {table}. Revenue results '
                            f'are not shown until this is fixed.')
            return None, pd.DataFrame(log), problems
    # Year and Month come from the date itself, so grouping by month works whatever day
    # of the month is stored (e.g. 2028-02-28 in a leap year).
    model = model.assign(Year=model['Date'].dt.year.astype('Int64'),
                         Month=model['Date'].dt.month.astype('Int64'))
    return model, pd.DataFrame(log), problems


# ---------------------------------------------------------- data quality
WEBSITE_TYPE = 'Website'  # StoreType of the online store (SH00 in the original data)

# Blanks we expect on Website rows: no physical address, and no in-store survey.
EXPECTED_WEBSITE_BLANKS = {
    'Stores': ['City', 'State', 'PostalCode'],
    'Survey': ['Satisfaction', 'Interest'],
}

PHONE_PATTERNS = [re.compile(r'^\(\d{3}\) \d{3}-\d{4}$'),  # (407) 555-9773
                  re.compile(r'^1-8\d{2}-\d{3}-\d{4}$')]   # toll-free: 1-800-555-7810

# Survey scales from the 'Terms and Definitions' sheet of the survey workbook.
SURVEY_SCALES = {'Satisfaction': (0, 5), 'Interest': (0, 100)}

# Reference list: which E-Presso Location values are plausible for each US state.
# This is general geography, not E-Presso results. States near a regional border appear
# under more than one region, so either value is accepted.
# ASSUMPTION: E-Presso's Location values may be company sales territories rather than
# standard geography. A mismatch is therefore only a POSSIBLE inconsistency for a person
# to review, never an error, and the app does not change or exclude the store.
LOCATION_STATES = {
    'East': {'CT', 'DC', 'DE', 'FL', 'GA', 'MA', 'MD', 'ME', 'NC', 'NH', 'NJ', 'NY', 'PA',
             'RI', 'SC', 'VA', 'VT', 'WV'},
    'South': {'AL', 'AR', 'DC', 'DE', 'FL', 'GA', 'KY', 'LA', 'MD', 'MS', 'NC', 'OK', 'SC',
              'TN', 'TX', 'VA', 'WV'},
    'Midwest': {'IA', 'IL', 'IN', 'KS', 'MI', 'MN', 'MO', 'ND', 'NE', 'OH', 'SD', 'WI'},
    'Southwest': {'AZ', 'NM', 'NV', 'OK', 'TX'},
    'West': {'AK', 'CA', 'CO', 'HI', 'ID', 'MT', 'NV', 'OR', 'UT', 'WA', 'WY'},
}
TERRITORY_CAVEAT = ("E-Presso's Location values may be company sales territories rather than "
                    'standard geography, so this may be intentional.')


def data_quality_notes(tables: dict) -> pd.DataFrame:
    """Plain-English data-quality notes, found by rules (no store is named in the code),
    so they also work on updated data. Levels: Expected, Info, Review."""
    notes = []

    def add(table, level, note):
        notes.append({'table': table, 'level': level, 'note': note})

    stores = tables.get('Stores')
    website_ids = set()
    if stores is not None:
        website_ids = set(stores.loc[stores['StoreType'] == WEBSITE_TYPE, 'ID'].dropna())

    # Blank values, separating the ones we expect on Website rows.
    for table, df in tables.items():
        store_col = {'Stores': 'ID', 'Survey': 'Store ID'}.get(table)
        on_website = (df[store_col].isin(website_ids) if store_col
                      else pd.Series(False, index=df.index))
        for col in df.columns:
            blank = df[col].isna()
            n_expected = 0
            if col in EXPECTED_WEBSITE_BLANKS.get(table, []):
                n_expected = int((blank & on_website).sum())
            n_other = int(blank.sum()) - n_expected
            if n_expected:
                reason = ('the website has no physical address' if table == 'Stores'
                          else 'no in-store survey is taken for the website')
                add(table, 'Expected', f'{n_expected} blank {col} value(s) on Website rows: '
                                       f'{reason}.')
            if n_other:
                extra = ' These rows are left out of revenue totals.' if col == 'Revenue' else ''
                add(table, 'Review', f'{n_other} blank {col} value(s).{extra}')
        n_dup = int(df.duplicated().sum())
        if n_dup:
            add(table, 'Review', f'{n_dup} fully duplicated row(s).')

    if stores is not None:
        _store_notes(stores, add)

    sales = tables.get('Sales')
    if sales is not None:
        n_nonpos = int((sales['Revenue'] <= 0).sum())
        if n_nonpos:
            add('Sales', 'Review', f'{n_nonpos} row(s) with zero or negative Revenue.')

    survey = tables.get('Survey')
    if survey is not None:
        for col, (low, high) in SURVEY_SCALES.items():
            n_out = int(((survey[col] < low) | (survey[col] > high)).sum())
            if n_out:
                add('Survey', 'Review', f'{n_out} {col} value(s) outside the {low}-{high} scale.')

    return pd.DataFrame(notes, columns=['table', 'level', 'note'])


def _store_notes(stores: pd.DataFrame, add) -> None:
    """Stores-only rules: phone format, shared cities, and Location vs. state."""
    physical = stores[stores['StoreType'] != WEBSITE_TYPE]

    for _, row in stores.dropna(subset=['Phone']).iterrows():
        if not any(p.match(row['Phone'].strip()) for p in PHONE_PATTERNS):
            add('Stores', 'Review', f'{row["ID"]} phone number "{row["Phone"]}" is not in the '
                                    f'usual (###) ###-#### format.')

    located = physical.dropna(subset=['City', 'State'])
    for (city, state), group in located.groupby(['City', 'State']):
        if len(group) > 1:
            add('Stores', 'Info', f'{city}, {state} has {len(group)} stores '
                                  f'({", ".join(group["ID"])}). City is not unique, so stores '
                                  f'are always identified by ID.')

    # Location vs. state: possible inconsistencies only (see the assumption above).
    for _, row in physical.dropna(subset=['State', 'Location']).iterrows():
        allowed = LOCATION_STATES.get(row['Location'])
        if allowed is None:
            add('Stores', 'Review', f'{row["ID"]} has Location "{row["Location"]}", which is not '
                                    f'in the reference list, so it could not be checked.')
        elif row['State'] not in allowed:
            add('Stores', 'Review', f'Possible Location inconsistency to review: {row["ID"]} '
                                    f'({row["City"]}, {row["State"]}) has Location '
                                    f'"{row["Location"]}", which is not a usual region for '
                                    f'{row["State"]}. {TERRITORY_CAVEAT}')
    for state, group in physical.dropna(subset=['State', 'Location']).groupby('State'):
        if group['Location'].nunique() > 1:
            detail = ', '.join(f'{r["ID"]} = {r["Location"]}' for _, r in group.iterrows())
            add('Stores', 'Review', f'Possible Location inconsistency to review: stores in '
                                    f'{state} have different Location values ({detail}). '
                                    f'{TERRITORY_CAVEAT}')
