"""Business logic. Keep Streamlit code OUT of this file so every function can be
tested on its own and reused by the assistant."""
from __future__ import annotations

import io
from dataclasses import asdict, dataclass, field

import pandas as pd

EXCEL_EXT = ('.xlsx', '.xlsm', '.xls')
TEXT_EXT = ('.csv', '.txt', '.tsv')


# ---------------------------------------------------------------- loading
def excel_sheet_names(file_bytes: bytes) -> list[str]:
    return pd.ExcelFile(io.BytesIO(file_bytes)).sheet_names


def load_table(file_bytes: bytes, filename: str, sheet_name=0, **read_options) -> pd.DataFrame:
    """Read an uploaded CSV / TXT / TSV / Excel file into a DataFrame.
    `read_options` (e.g. header=2, dtype={'PostalCode': str}) are passed to pandas."""
    name = filename.lower()
    buffer = io.BytesIO(file_bytes)
    if name.endswith(EXCEL_EXT):
        return pd.read_excel(buffer, sheet_name=sheet_name, **read_options)
    if name.endswith(TEXT_EXT):
        return pd.read_csv(buffer, sep=None, engine='python', **read_options)  # sniffs the delimiter
    raise ValueError(f'Unsupported file type: {filename}')


def profile_table(df: pd.DataFrame) -> dict:
    """Basic profile: size, duplicates, missing values, data types."""
    missing = df.isna().sum()
    return {
        'rows': len(df),
        'columns': df.shape[1],
        'duplicate_rows': int(df.duplicated().sum()),
        'missing': pd.DataFrame({
            'column': missing.index,
            'missing': missing.values,
            'pct_missing': (missing.values / max(len(df), 1) * 100).round(2),
        }),
        'dtypes': pd.DataFrame({'column': df.columns, 'dtype': df.dtypes.astype(str).values}),
    }


# ---------------------------------------------------------- tool contract
@dataclass
class ToolResult:
    """Every analytical function returns this. The assistant may only narrate it.
    Keep `value` to plain Python types (numbers, strings, dicts, lists)."""
    tool: str
    value: object
    definition: str
    scope: dict
    rows_used: int
    caveats: list = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _error(tool: str, message: str, scope: dict | None = None) -> ToolResult:
    return ToolResult(tool=tool, value=None, definition='', scope=scope or {},
                      rows_used=0, caveats=[], error=message)


def _apply_filters(df: pd.DataFrame, filters: dict | None):
    """Validate filters against the LOADED data, then apply them.
    Every value is checked against the full table first, so a valid value that simply has no
    rows under the other filters (e.g. a store with no Website sales) is not called unknown."""
    wanted_by_col = {}
    for col, wanted in (filters or {}).items():
        if col not in df.columns:
            return df, f'Unknown column: {col}'
        wanted_list = list(wanted) if isinstance(wanted, (list, tuple, set)) else [wanted]
        valid = set(df[col].dropna().unique())
        bad = [w for w in wanted_list if w not in valid]
        if bad:
            examples = sorted(map(str, valid))[:20]
            return df, f'{bad} not found in column {col}. Valid values include: {examples}'
        wanted_by_col[col] = wanted_list
    for col, wanted_list in wanted_by_col.items():
        df = df[df[col].isin(wanted_list)]
    return df, None


# ------------------------------------------------------ analytical tools
def get_total(df: pd.DataFrame, value_col: str, filters: dict | None = None) -> ToolResult:
    """Sum of one numeric column, optionally filtered. EXAMPLE tool: replace the
    generic column names with your own definition of revenue."""
    name = 'get_total'
    if value_col not in df.columns:
        return _error(name, f'Unknown column: {value_col}')
    subset, err = _apply_filters(df, filters)
    if err:
        return _error(name, err, {'filters': filters})
    values = pd.to_numeric(subset[value_col], errors='coerce')
    n_bad = int(values.isna().sum())
    caveats = ['This is a sum of the chosen column. Revenue is not profit.']
    if n_bad:
        caveats.append(f'{n_bad} row(s) had a missing or non-numeric {value_col} and were excluded.')
    return ToolResult(tool=name, value=float(values.sum()), definition=f'Sum of {value_col}',
                      scope={'filters': filters or 'none (all rows)'},
                      rows_used=int(values.notna().sum()), caveats=caveats)


def group_total(df: pd.DataFrame, value_col: str, group_col: str,
                filters: dict | None = None) -> ToolResult:
    """Sum of one numeric column by group (store, channel, year, ...)."""
    name = 'group_total'
    for col in (value_col, group_col):
        if col not in df.columns:
            return _error(name, f'Unknown column: {col}')
    subset, err = _apply_filters(df, filters)
    if err:
        return _error(name, err, {'filters': filters})
    work = subset.assign(**{value_col: pd.to_numeric(subset[value_col], errors='coerce')})
    n_bad = int(work[value_col].isna().sum())
    n_nogroup = int(work[group_col].isna().sum())
    grouped = work.dropna(subset=[value_col, group_col]).groupby(group_col)[value_col].sum()
    caveats = ['Sums of the chosen column. Revenue is not profit.']
    if n_bad:
        caveats.append(f'{n_bad} row(s) with missing or non-numeric {value_col} were excluded.')
    if n_nogroup:
        caveats.append(f'{n_nogroup} row(s) with a missing {group_col} were excluded.')
    return ToolResult(tool=name, value={str(k): float(v) for k, v in grouped.items()},
                      definition=f'Sum of {value_col} by {group_col}',
                      scope={'filters': filters or 'none (all rows)'},
                      rows_used=int(len(work) - n_bad - n_nogroup), caveats=caveats)


# ------------------------------------------------------ E-Presso revenue
# The explicit parameters a revenue tool accepts, and the sales-model column each one filters.
REVENUE_FILTERS = {'year': 'Year', 'channel': 'Channel', 'store': 'Store ID',
                   'category': 'Category'}
REVENUE_DEFINITION = 'Sum of Revenue on the monthly sales rows (one row per store x product x month)'


def _revenue_filters(**params) -> tuple[dict, dict]:
    """Turn explicit parameters into ({column: [values]}, scope). None, 'All', or an empty
    list means no filter. Years may arrive as text ('2028'), so they become numbers."""
    filters, scope = {}, {}
    for param, value in params.items():
        values = list(value) if isinstance(value, (list, tuple, set)) else [value]
        values = [v for v in values if v is not None and v != 'All']
        if param == 'year':
            values = [int(v) if str(v).isdigit() else v for v in values]
        scope[param] = 'All' if not values else values[0] if len(values) == 1 else values
        if values:
            filters[REVENUE_FILTERS[param]] = values
    return filters, scope


def _plain(value):
    """numpy/pandas numbers -> plain Python, so results can be shown as JSON."""
    return value.item() if hasattr(value, 'item') else value


def _select(name: str, model: pd.DataFrame | None, year, channel, store, category):
    """Shared first step of every revenue tool: check the filters against the loaded data,
    apply them, and collect caveats. Returns (rows, scope, caveats, error_result or None)."""
    filters, scope = _revenue_filters(year=year, channel=channel, store=store,
                                      category=category)
    if model is None:
        return None, scope, [], _error(name, 'Revenue cannot be calculated: the sales data did '
                                             'not load or failed a merge check (see the Data '
                                             'and profile tab).', scope)
    subset, err = _apply_filters(model, filters)
    if err:
        return None, scope, [], _error(name, err, scope)
    subset = subset.assign(Revenue=pd.to_numeric(subset['Revenue'], errors='coerce'))
    caveats = ['Revenue is not profit: costs are not in the data.']
    n_missing = int(subset['Revenue'].isna().sum())
    if n_missing:
        caveats.append(f'{n_missing} row(s) with missing revenue were excluded.')
    if 'Channel' in filters:
        n_no_channel = int(model['Channel'].isna().sum())
        if n_no_channel:
            caveats.append(f'{n_no_channel} row(s) with no channel (store not found in Stores) '
                           f'are excluded by the channel filter.')
    if subset['Revenue'].notna().sum() == 0:
        caveats.append('No sales match these filters.')
    return subset, scope, caveats, None


def get_total_revenue(model: pd.DataFrame | None, year=None, channel=None, store=None,
                      category=None) -> ToolResult:
    """Total revenue for the chosen year(s), channel(s), store ID(s), and category(ies).
    Values are checked against the loaded data; an unknown value returns an error result."""
    name = 'get_total_revenue'
    rows, scope, caveats, err = _select(name, model, year, channel, store, category)
    if err:
        return err
    return ToolResult(tool=name, value=round(float(rows['Revenue'].sum()), 2),
                      definition=REVENUE_DEFINITION, scope=scope,
                      rows_used=int(rows['Revenue'].notna().sum()), caveats=caveats)


# The fixed list of ways revenue can be broken down, and the sales-model column for each.
BREAKDOWN_DIMENSIONS = {'year': 'Year', 'month': 'Month', 'channel': 'Channel',
                        'store': 'Store ID', 'category': 'Category'}


def store_labels(model: pd.DataFrame) -> dict:
    """Readable store names by ID, e.g. {'SH11': 'SH11 – Chicago, IL', 'SH00': 'SH00 – Website'}.
    Stores are always identified by ID, because a city can have more than one store."""
    labels = {}
    for _, row in model.drop_duplicates('Store ID').iterrows():
        if pd.notna(row.get('City')) and pd.notna(row.get('State')):
            place = f'{row["City"]}, {row["State"]}'
        else:
            place = row.get('Channel')
        labels[row['Store ID']] = f'{row["Store ID"]} – {place}' if pd.notna(place) else row['Store ID']
    return dict(sorted(labels.items()))


def get_revenue_breakdown(model: pd.DataFrame | None, by, year=None, channel=None, store=None,
                          category=None) -> ToolResult:
    """Revenue grouped by one or two of: year, month, channel, store, category.
    Each row also gives its share of total revenue for the current filters."""
    name = 'get_revenue_breakdown'
    dims = [by] if isinstance(by, str) else list(by)
    if not 1 <= len(dims) <= 2 or len(set(dims)) != len(dims) or any(
            d not in BREAKDOWN_DIMENSIONS for d in dims):
        return _error(name, f'"by" must be one or two different values from: '
                            f'{", ".join(BREAKDOWN_DIMENSIONS)}. Got: {by}')
    rows, scope, caveats, err = _select(name, model, year, channel, store, category)
    if err:
        return err
    cols = [BREAKDOWN_DIMENSIONS[d] for d in dims]
    missing = [c for c in cols if c not in rows.columns]
    if missing:
        return _error(name, f'Column(s) {missing} are not in the sales model (a lookup table '
                            f'did not load).', scope)
    valid = rows.dropna(subset=['Revenue'])
    n_blank = int(valid[cols].isna().any(axis=1).sum())
    if n_blank:
        caveats.append(f'{n_blank} row(s) with a blank {" or ".join(dims)} were excluded.')
    valid = valid.dropna(subset=cols)
    grouped = valid.groupby(cols)['Revenue'].sum()
    total = float(grouped.sum())
    labels = store_labels(model) if 'store' in dims else {}
    records = []
    for keys, revenue in grouped.items():
        keys = keys if isinstance(keys, tuple) else (keys,)
        record = {dim: _plain(key) for dim, key in zip(dims, keys)}
        if 'store' in dims:
            record['store_label'] = labels.get(record['store'], record['store'])
        record['revenue'] = round(float(revenue), 2)
        record['share_pct'] = round(float(revenue) / total * 100, 4) if total else None
        records.append(record)
    return ToolResult(tool=name, value=records,
                      definition=(f'Revenue by {" and ".join(dims)} ({REVENUE_DEFINITION}). '
                                  f'share_pct = percent of total revenue for the current filters.'),
                      scope=scope, rows_used=len(valid), caveats=caveats)


def get_monthly_share(model: pd.DataFrame | None, year=None, channel=None, store=None,
                      category=None) -> ToolResult:
    """Each calendar month's share of revenue. The denominator is total revenue for the
    current filters (all selected years together), so the shares add up to 100%.
    With no filters this matches Power BI's "Percent of Annual Revenue per Month", which
    really divides by the five-year grand total (see docs/validation-table.md)."""
    result = get_revenue_breakdown(model, 'month', year, channel, store, category)
    result.tool = 'get_monthly_share'
    if result.error:
        return result
    result.definition = ('Each calendar month\'s revenue as a percent of total revenue for the '
                         'current filters, with the selected years added together. The shares '
                         'add up to 100%.')
    result.caveats.append('This is not a percent of each year\'s revenue: each month is added '
                          'up across the selected years first. Select one year to see that '
                          'year\'s pattern.')
    return result


def get_revenue_change(model: pd.DataFrame | None, year=None, channel=None, store=None,
                       category=None) -> ToolResult:
    """Revenue in the first and last selected years, and the change between them."""
    name = 'get_revenue_change'
    rows, scope, caveats, err = _select(name, model, year, channel, store, category)
    if err:
        return err
    by_year = rows.dropna(subset=['Revenue', 'Year']).groupby('Year')['Revenue'].sum()
    value = None
    if len(by_year) < 2:
        caveats.append('At least two years with sales are needed to calculate a change.')
    else:
        first, last = by_year.index.min(), by_year.index.max()
        before, after = float(by_year[first]), float(by_year[last])
        value = {'first_year': _plain(first), 'last_year': _plain(last),
                 'first_revenue': round(before, 2), 'last_revenue': round(after, 2),
                 'change': round(after - before, 2),
                 'change_pct': round((after - before) / before * 100, 2) if before else None}
        caveats.append('Compares the first and last years only; it does not show the years '
                       'in between, and it does not explain why revenue changed.')
    return ToolResult(tool=name, value=value,
                      definition=('Revenue in the last selected year minus revenue in the first '
                                  'selected year, in dollars and as a percent of the first year.'),
                      scope=scope, rows_used=int(rows['Revenue'].notna().sum()), caveats=caveats)


def data_quality_report(df: pd.DataFrame) -> ToolResult:
    """Row count, duplicate rows, and missing values per column."""
    missing = {c: int(n) for c, n in df.isna().sum().items() if n > 0}
    caveats = []
    if missing:
        caveats.append('Missing values may limit conclusions drawn from those columns.')
    return ToolResult(tool='data_quality_report',
                      value={'rows': len(df), 'duplicate_rows': int(df.duplicated().sum()),
                             'columns_with_missing': missing},
                      definition='Counts of duplicate rows and missing values in the loaded table',
                      scope={'filters': 'none (full table)'}, rows_used=len(df), caveats=caveats)


# ------------------------------------------------------------ merge check
def check_merge(left: pd.DataFrame, right: pd.DataFrame, on, value_col: str, how: str = 'left'):
    """Merge, and report whether the join changed the row count or the revenue sum.
    `value_col` must be a numeric column in `left`. Returns (merged, report)."""
    before_rows = len(left)
    before_sum = float(pd.to_numeric(left[value_col], errors='coerce').sum())
    merged = left.merge(right, on=on, how=how)
    after_rows = len(merged)
    after_sum = float(pd.to_numeric(merged[value_col], errors='coerce').sum())
    fan_out = after_rows > before_rows or abs(after_sum - before_sum) > 1e-9
    report = {
        'rows_before': before_rows, 'rows_after': after_rows,
        'sum_before': before_sum, 'sum_after': after_sum,
        'changed': fan_out,
        'warning': ('The join changed the row count or the total. Check the grain and keys '
                    'of both tables before using this result.') if fan_out else '',
    }
    return merged, report
