"""Assistant: a tool registry, a dispatcher, and a router.
The router (rules now, a language model later) only CHOOSES a tool and its arguments. The
dispatcher (run_tool) checks those arguments against the loaded data, runs the tool, and logs
the call. Nothing here executes model-written code, and no tool changes the loaded data."""
from __future__ import annotations

import calendar
import re
import time
from dataclasses import dataclass, field

import pandas as pd

import analytics
from analytics import ToolResult


@dataclass
class Context:
    """What the tools may read: the data loaded right now, passed in on every call, so an
    uploaded file is used straight away. `fingerprint` says which data that is, for the log."""
    model: pd.DataFrame | None
    tables: dict = field(default_factory=dict)
    fingerprint: str = ''


def make_context(model, tables: dict, summary: pd.DataFrame | None = None) -> Context:
    """Build a Context; `summary` is data_prep.loaded_summary() and supplies the fingerprint,
    e.g. 'Sales.csv (uploaded) · 25,200 rows · revenue sum $42,175,440.00'."""
    fingerprint = ''
    if summary is not None and 'Sales' in set(summary['table']):
        row = summary.set_index('table').loc['Sales']
        if pd.notna(row['rows']):
            fingerprint = (f'{row["file"]} ({row["source"]}) · {int(row["rows"]):,} rows · '
                           f'revenue sum ${row["revenue sum"]:,.2f}')
    return Context(model=model, tables=tables, fingerprint=fingerprint)


# ---------------------------------------------------------------- parameters
def _column_values(column):
    """Allowed values for a parameter: whatever is in the loaded data (never typed in)."""
    def values(ctx: Context) -> list:
        if ctx.model is None or column not in ctx.model.columns:
            return []
        return [analytics._plain(v) for v in sorted(ctx.model[column].dropna().unique())]
    return values


# Every parameter a tool may take: where its allowed values come from, and whether it takes
# one value or a list. The same descriptions become the language model's tool definitions.
PARAMS = {
    'year': {'values': _column_values('Year'), 'many': True, 'type': 'integer',
             'description': 'Year(s), e.g. 2028.'},
    'start_year': {'values': _column_values('Year'), 'many': False, 'type': 'integer',
                   'description': 'First year to compare (default: first year in the data).'},
    'end_year': {'values': _column_values('Year'), 'many': False, 'type': 'integer',
                 'description': 'Last year to compare (default: last year in the data).'},
    'channel': {'values': _column_values('Channel'), 'many': True, 'type': 'string',
                'description': 'Sales channel(s): Website or Brick & Mortar.'},
    'store': {'values': _column_values('Store ID'), 'many': True, 'type': 'string',
              'description': 'Store ID(s) such as SH11, or a city that has only one store.'},
    'category': {'values': _column_values('Category'), 'many': True, 'type': 'string',
                 'description': 'Product category or categories.'},
    'market': {'values': _column_values('Market'), 'many': True, 'type': 'string',
               'description': 'Market-size tier(s) of the stores, e.g. 4-Large.'},
    'by': {'values': lambda ctx: list(analytics.BREAKDOWN_DIMENSIONS), 'many': True,
           'type': 'string', 'description': 'One or two of: year, month, channel, store, '
                                            'category.'},
}

# What each tool reads from the Context.
INPUTS = {
    'model': lambda ctx: ctx.model,
    'survey': lambda ctx: ctx.tables.get('Survey'),
    'tables': lambda ctx: ctx.tables,
    'sales': lambda ctx: ctx.tables.get('Sales'),
}

# ---------------------------------------------------------------- the registry
# The ONLY things the assistant may do. (The starter's generic get_total and group_total
# took any column name, so they are kept in analytics.py but are not assistant tools.)
TOOLS = {
    'get_total_revenue': {
        'fn': analytics.get_total_revenue, 'inputs': ('model',),
        'params': ('year', 'channel', 'store', 'category'), 'required': (),
        'description': 'Total revenue, optionally for given years, channels, stores, or '
                       'categories.'},
    'get_revenue_breakdown': {
        'fn': analytics.get_revenue_breakdown, 'inputs': ('model',),
        'params': ('by', 'year', 'channel', 'store', 'category'), 'required': ('by',),
        'description': 'Revenue split by one or two of year, month, channel, store, category, '
                       'with each part\'s share of the total.'},
    'get_monthly_share': {
        'fn': analytics.get_monthly_share, 'inputs': ('model',),
        'params': ('year', 'channel', 'store', 'category'), 'required': (),
        'description': 'Each month\'s share of revenue for the selected period (seasonality).'},
    'get_store_trends': {
        'fn': analytics.get_store_trends, 'inputs': ('model',),
        'params': ('start_year', 'end_year', 'channel', 'category', 'market'), 'required': (),
        'description': 'Revenue change per store between two years, ranked from the largest '
                       'decline, with Market tier and within-tier rank. Physical stores only '
                       'unless channel is given.'},
    'get_satisfaction_vs_revenue': {
        'fn': analytics.get_satisfaction_vs_revenue, 'inputs': ('model', 'survey'),
        'params': ('year', 'market'), 'required': (),
        'description': 'Association between customer satisfaction and revenue per store-year, '
                       'overall and within each Market tier.'},
    'get_data_coverage': {
        'fn': analytics.get_data_coverage, 'inputs': ('model', 'tables'),
        'params': (), 'required': (),
        'description': 'What the loaded data contains (measures, years, channels, tiers), '
                       'e.g. to explain that profit cannot be calculated.'},
    'data_quality_report': {
        'fn': analytics.data_quality_report, 'inputs': ('sales',),
        'params': (), 'required': (),
        'description': 'Duplicates and missing values in the Sales table.'},
}

UNSUPPORTED = ('I can only answer questions that my approved analytical functions can '
               'calculate from the loaded data: ' + ', '.join(TOOLS) + '. '
               'I cannot answer that one.')

# For when you add a language model: keep these rules in the system prompt.
SYSTEM_PROMPT = """You are an analytical assistant for E-Presso managers.
Rules:
- Only state numbers that appear in a tool result. Never estimate or recall figures.
- Always call a tool before making a numerical claim.
- State the scope (which filters/period) of every answer.
- Separate Findings (from tool results), Interpretation, and Next steps.
- Revenue is not profit. Association is not causation.
- If the data cannot support a conclusion, say so and name the missing information.
- Never ask for, run, or write code. Never modify data."""


def _store_value(raw, ctx: Context):
    """A store given as an ID (SH11), a label (SH11 – Chicago, IL), or a city with exactly one
    store (Chicago). Returns (store ID, error)."""
    text = str(raw).strip().lower()
    stores = ctx.model.drop_duplicates('Store ID') if ctx.model is not None else pd.DataFrame()
    labels = analytics.store_labels(ctx.model) if ctx.model is not None else {}
    for store_id, label in labels.items():
        if text in (store_id.lower(), label.lower()):
            return store_id, None
    if 'City' in stores:
        matches = stores[stores['City'].fillna('').str.lower() == text]['Store ID'].tolist()
        if len(matches) == 1:
            return matches[0], None
        if len(matches) > 1:
            names = ', '.join(labels.get(m, m) for m in sorted(matches))
            return None, (f'"{raw}" matches more than one store ({names}). '
                          f'Ask about one store ID.')
    return None, None  # not a store: reported with the list of valid values


def normalize(param: str, raw, ctx: Context):
    """Check one argument against the loaded data and put it in canonical form.
    Returns (value, error). None, 'All', or [] mean 'no filter'. Never guesses: a value that
    is not in the data is an error that lists the valid values."""
    spec = PARAMS[param]
    values = list(raw) if isinstance(raw, (list, tuple, set)) else [raw]
    values = [v for v in values if v is not None and str(v).strip() not in ('', 'All')]
    if not values:
        return None, None
    if not spec['many'] and len(values) > 1:
        return None, f'{param} takes one value, got {values}.'
    allowed = spec['values'](ctx)
    by_text = {str(a).lower(): a for a in allowed}
    clean = []
    for v in values:
        text = str(v).strip()
        if spec['type'] == 'integer' and text.upper().lstrip('Y').isdigit():
            text = text.upper().lstrip('Y')  # "Y2028" (as in the survey) -> "2028"
        match = by_text.get(text.lower())
        if match is None and param == 'store':
            match, err = _store_value(v, ctx)
            if err:
                return None, err
        if match is None:
            shown = ', '.join(map(str, allowed[:25])) + (' ...' if len(allowed) > 25 else '')
            return None, f'{param} "{v}" is not in the loaded data. Valid values: {shown}.'
        clean.append(match)
    if param == 'by' and len(clean) > 2:
        return None, 'by takes one or two values.'
    return (clean if spec['many'] else clean[0]), None


# ---------------------------------------------------------------- the dispatcher
def run_tool(name: str, args: dict | None, ctx: Context, log: list) -> ToolResult:
    """The dispatcher: check the request, run the tool on the loaded data, log the call."""
    started = time.perf_counter()
    args = dict(args or {})
    used = {}
    spec = TOOLS.get(name)
    if spec is None:
        result = analytics._error(name, f'Unknown tool: {name}. Available tools: '
                                        f'{", ".join(TOOLS)}.')
    else:
        unexpected = sorted(set(args) - set(spec['params']))
        # missing = not given, or given as empty / 'All' (normalize returns no value, no error)
        missing = [p for p in spec['required'] if normalize(p, args.get(p), ctx) == (None, None)]
        errors = []
        if unexpected:
            errors.append(f'Unexpected argument(s) for {name}: {unexpected}. '
                          f'Allowed: {list(spec["params"])}.')
        if missing:
            errors.append(f'Missing required argument(s) for {name}: {missing}.')
        for param in spec['params']:
            if param in args and not unexpected:
                value, err = normalize(param, args[param], ctx)
                if err:
                    errors.append(err)
                elif value is not None:
                    used[param] = value
        if errors:
            result = analytics._error(name, ' '.join(errors))
        else:
            try:
                inputs = [INPUTS[i](ctx) for i in spec['inputs']]
                result = spec['fn'](*inputs, **used)
            except Exception as exc:  # a plain error result, never a traceback in the chat
                result = analytics._error(name, f'The tool failed: {type(exc).__name__}: {exc}')
    log.append({'call': len(log) + 1, 'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'tool': name, 'arguments': args, 'arguments_used': used,
                'status': 'error' if result.error else 'ok', 'rows_used': result.rows_used,
                'duration_ms': round((time.perf_counter() - started) * 1000, 1),
                'data': ctx.fingerprint, 'result': result.to_dict()})
    return result


def tool_definitions(ctx: Context) -> list:
    """The registry as function definitions for a language model (Option A, Checkpoint 4),
    with the allowed values taken from the loaded data."""
    definitions = []
    for name, spec in TOOLS.items():
        properties = {}
        for param in spec['params']:
            p = PARAMS[param]
            item = {'type': p['type'], 'enum': p['values'](ctx)}
            properties[param] = ({'type': 'array', 'items': item, 'description': p['description']}
                                 if p['many'] else {**item, 'description': p['description']})
        definitions.append({'name': name, 'description': spec['description'],
                            'parameters': {'type': 'object', 'properties': properties,
                                           'required': list(spec['required'])}})
    return definitions


# ---------------------------------------------------------------- rules router (Option B)
# The router only decides WHICH tools to call and with WHICH filters. Every number in an
# answer comes from a tool result returned by run_tool(); the composers below only format.

FILTER_PARAMS = ('year', 'channel', 'store', 'category', 'market')
PLURALS = {'year': 'years', 'channel': 'channels', 'store': 'stores', 'category': 'categories',
           'market': 'Market tiers'}
FROM_QUESTION, FROM_SIDEBAR = 'from your question', 'from the sidebar filter'
NO_RECOMMENDATION = 'No recommendation is supported by this data.'
MONTH_NAMES = dict(enumerate(calendar.month_name))

CHANNEL_WORDS = {'website': r'\b(website|web ?site|online|e-?commerce|internet)\b',
                 'physical': r'\b(brick|bricks|physical|in-?store)\b'}
# A tier word only counts when it describes stores ("large stores", "Large tier"), so that
# "the largest decline" or "a small change" is not read as a Market tier.
TIER_FOLLOWS = r'(?=\s+(?:stores?|tiers?|markets?|shops?|locations?)\b)'
STORE_WORDS = r'\b(stores?|shops?|locations?|branch\w*)\b'

# Intent rules, checked in this order; the first match wins. Order matters because nearly
# every question mentions revenue: "Which store's revenue declined most?" is a store trend.
INTENT_RULES = [
    ('decision', r'\b(close|closing|closed|closure|shut\w*|expand\w*|invest\w*|relocat\w*)\b'),
    ('profit', r'\b(profit\w*|margins?|costs?|expenses?|loss|losses)\b'),
    ('satisfaction', r'\b(satisf\w*|surveys?|happy|happiness)\b'),
    ('store_trends', r'\b(declin\w*|drop\w*|fall\w*|fell|shrink\w*|grow\w*|growth|increas\w*|'
                     r'decreas\w*|trends?)\b'),
    ('seasonality', r'\b(months?|monthly|season\w*|holiday\w*|busiest|quietest|january|february|'
                    r'march|april|june|july|august|september|october|november|december)\b'),
    ('quality', r'\b(missing values?|duplicat\w*|blanks?|data quality)\b'),
    ('coverage', r'\b(what can you|what data|what do you know|help|capabilit\w*)\b'),
    ('breakdown', r'\b(by|per|each|which|compare\w*|comparison|breakdown|split|top|highest|'
                  r'lowest|best|worst|biggest|smallest|rank\w*)\b'),
    ('total', r'\b(revenue|sales|sold|sell|earn\w*|made|generat\w*|how much|total|income)\b'),
]
DIMENSION_WORDS = {'year': r'\b(years?|yearly|annual\w*)\b', 'month': r'\b(months?|monthly)\b',
                   'channel': r'\bchannels?\b', 'store': STORE_WORDS,
                   'category': r'\b(categor\w*|product lines?)\b'}

# What the assistant can answer, shown for unsupported questions and for "help".
CAPABILITIES = [
    ('Total revenue for any years, channel, store, or category',
     'How much revenue did the website generate in 2028?'),
    ('Revenue broken down by year, month, channel, store, or category',
     'What was revenue by category in 2027?'),
    ('Seasonality: each month\'s share of revenue', 'Which months bring in the most revenue?'),
    ('Store trends, with each store\'s Market tier', 'Which store had the greatest revenue decline?'),
    ('Customer satisfaction vs. revenue (association, not cause)',
     'Is customer satisfaction related to revenue?'),
    ('What the data contains, and why profit cannot be calculated',
     'Which store is the most profitable?'),
    ('Store decisions: the evidence and what is missing (no recommendation)',
     'Should E-Presso close the Chicago store?'),
    ('Data quality', 'Are there missing values in the sales data?'),
]


def extract_filters(question: str, ctx: Context) -> dict:
    """Filters named in the question, matched against values in the loaded data. They are not
    validated here: the dispatcher checks them (e.g. an ambiguous city or a missing year)."""
    q = question.lower()
    model = ctx.model if ctx.model is not None else pd.DataFrame()
    found = {}
    years = sorted({int(y) for y in re.findall(r'(?<!\d)(?:fy|y)?(20\d\d)(?!\d)', q)})
    if years:
        found['year'] = years
    stores = [s.upper() for s in re.findall(r'\bsh\d{2}\b', q)]
    for city in sorted(model['City'].dropna().unique()) if 'City' in model else []:
        if re.search(r'\b' + re.escape(city.lower()) + r'\b', q):
            stores.append(city)
    if stores:
        found['store'] = list(dict.fromkeys(stores))
    if 'Channel' in model:
        channels = sorted(model['Channel'].dropna().unique())
        chosen = []
        if re.search(CHANNEL_WORDS['website'], q):
            chosen += [c for c in channels if c == analytics.WEBSITE_TYPE]
        if re.search(CHANNEL_WORDS['physical'], q):
            chosen += [c for c in channels if c != analytics.WEBSITE_TYPE]
        if chosen:
            found['channel'] = chosen
    if 'Category' in model:
        # match the start of the name, so "bean" finds Beans and "accessory" Accessories
        cats = [c for c in sorted(model['Category'].dropna().unique())
                if re.search(r'\b' + re.escape(c.lower()[:max(4, len(c) - 3)]), q)]
        if cats:
            found['category'] = cats
    if 'Market' in model:
        tiers = [t for t in sorted(model['Market'].dropna().unique())
                 if re.search(r'\b' + re.escape(t.lower()) + r'\b', q)
                 or re.search(r'\b' + re.escape(t.split('-', 1)[-1].lower()) + r'\b'
                              + TIER_FOLLOWS, q)]
        if tiers:
            found['market'] = tiers
    return found


def route(question: str, ctx: Context):
    """(intent, filters from the question). intent is None for an unsupported question."""
    q = question.lower()
    filters = extract_filters(question, ctx)
    for intent, pattern in INTENT_RULES:
        if not re.search(pattern, q):
            continue
        if intent == 'store_trends' and not (re.search(STORE_WORDS, q) or filters.get('store')
                                             or filters.get('market')):
            continue  # "revenue growth" with no store is a total or breakdown question
        if intent == 'decision' and not (filters.get('store') or re.search(STORE_WORDS, q)):
            continue
        if intent == 'breakdown' and not _dimensions(q, filters):
            continue
        return intent, filters
    return None, filters


def _dimensions(q: str, filters: dict) -> list:
    """Which dimension(s) a breakdown question asks about, in the order they are named."""
    hits = sorted((m.start(), dim) for dim, pattern in DIMENSION_WORDS.items()
                  for m in [re.search(pattern, q)] if m)
    dims = list(dict.fromkeys(dim for _, dim in hits))[:2]
    if not dims and len(filters.get('channel', [])) > 1:
        dims = ['channel']  # "compare website and physical stores"
    return dims


def build_args(filters: dict, sidebar: dict | None, use_sidebar: bool, accepted: tuple,
               reasons: dict | None = None):
    """Combine filters from the question with the sidebar filters. The question wins; any
    filter it does not mention comes from the sidebar (if switched on). Returns
    (args, sources, notes): notes explain filters this analysis cannot use."""
    args, sources, notes = {}, {}, []
    for param in FILTER_PARAMS:
        if filters.get(param):
            value, source = filters[param], FROM_QUESTION
        elif use_sidebar and (sidebar or {}).get(param):
            value, source = sidebar[param], FROM_SIDEBAR
        else:
            continue
        if param in accepted:
            args[param], sources[param] = value, source
        else:
            why = (reasons or {}).get(param, 'this analysis does not use it')
            who = 'Sidebar' if source == FROM_SIDEBAR else 'Your question\'s'
            notes.append(f'{who} {param} filter not applied: {why}.')
    return args, sources, notes


def _describe(param: str, value, labels: dict) -> str:
    values = value if isinstance(value, list) else [value]
    if param == 'store':
        values = [labels.get(v, v) for v in values]
    return ', '.join(map(str, values))


def _scope(parts: list, notes: list) -> str:
    return 'Scope: ' + '; '.join(parts) + '.' + ''.join(f' {n}' for n in notes)


def _filter_parts(used: dict, sources: dict, labels: dict, params: tuple) -> list:
    """'SH11 – Chicago, IL (from your question)' for each filter used, else 'all stores'."""
    return [f'{_describe(p, used[p], labels)} ({sources.get(p, FROM_QUESTION)})' if p in used
            else f'all {PLURALS[p]}' for p in params]


def _physical_channels(ctx: Context) -> list:
    if ctx.model is None or 'Channel' not in ctx.model:
        return []
    return sorted(c for c in ctx.model['Channel'].dropna().unique() if c != analytics.WEBSITE_TYPE)


def _website_ids(ctx: Context) -> list:
    if ctx.model is None or 'Channel' not in ctx.model:
        return []
    return sorted(ctx.model.loc[ctx.model['Channel'] == analytics.WEBSITE_TYPE, 'Store ID'].unique())


def money(x) -> str:
    return f'${x:,.2f}'


def _answer(intent, scope, findings, interpretation, next_steps, log) -> dict:
    return {'intent': intent, 'scope': scope, 'findings': findings,
            'interpretation': interpretation, 'next_steps': next_steps, 'tool_log': log}


def _error_answer(intent, result, log, scope='Scope: not available because the request '
                                             'could not be completed.') -> dict:
    return _answer(intent, scope, [f'The request could not be completed: {result.error}'], [],
                   ['Check the store, year, or other names in your question and ask again.'],
                   log)


def _tier_note(records: list) -> str | None:
    """Whether a store revenue ranking mostly reflects store size (Market tier)."""
    top = records[:3]
    tiers = [r.get('market') for r in top]
    if len(top) < 3 or None in tiers:
        return None
    if len(set(tiers)) == 1:
        tier = tiers[0]
        in_tier = sum(r.get('market') == tier for r in records)
        largest = max(r['market'] for r in records if r.get('market'))
        which = f'the three {tier} stores' if in_tier == 3 else f'all {tier} stores'
        size = ', the largest Market tier' if tier == largest else ''
        return (f'The top three are {which}{size}, so this revenue ranking mostly reflects '
                f'store size.')
    return (f'The top three come from different Market tiers ({", ".join(tiers)}); compare '
            f'stores within the same tier.')


def _trend_sentence(row: dict, tiers: dict, start: int, end: int) -> str:
    tier = tiers.get(row['market'], {})
    text = (f"{row['store_label']} ({row['market']}): {money(row[f'revenue_{start}'])} in "
            f"{start} → {money(row[f'revenue_{end}'])} in {end}")
    if row['change_pct'] is None:
        return text + f' (no sales in {start}, so no percentage change).'
    text += f" ({row['change_pct']:+.2f}%)."
    if tier.get('median_change_pct') is not None:
        side = 'below' if row['vs_tier_median_pts'] < 0 else 'above'
        text += (f" Within {row['market']} it ranks {row['rank_in_tier']} of {tier['stores']} "
                 f"(1 = largest decline); the {row['market']} median change was "
                 f"{tier['median_change_pct']:+.2f}%, so it is "
                 f"{abs(row['vs_tier_median_pts']):.2f} points {side} its tier's median.")
    return text


# ---------------------------------------------------------------- composers (one per intent)
def _total(filters, sidebar, use_sidebar, ctx, log, labels):
    params = ('year', 'channel', 'store', 'category')
    args, sources, notes = build_args(filters, sidebar, use_sidebar, params)
    r = run_tool('get_total_revenue', args, ctx, log)
    if r.error:
        return _error_answer('total', r, log)
    scope = _scope(_filter_parts(log[-1]['arguments_used'], sources, labels, params), notes)
    if r.rows_used == 0:
        findings = ['No sales match this scope.']
    else:
        findings = [f'Total revenue: {money(r.value)}.',
                    f'Based on {r.rows_used:,} monthly sales rows (one per store, product, '
                    f'and month).']
    return _answer('total', scope, findings, r.caveats,
                   ['For a split of this total, ask e.g. "What was revenue by year?" or '
                    '"Which category earned the most?"'], log)


def _breakdown(filters, sidebar, use_sidebar, ctx, log, labels, q):
    params = ('year', 'channel', 'store', 'category')
    dims = _dimensions(q, filters)
    args, sources, notes = build_args(filters, sidebar, use_sidebar, params)
    if 'store' in dims and 'channel' not in args and _website_ids(ctx):
        args['channel'] = _physical_channels(ctx)  # the website is a separate channel
        sources['channel'] = 'physical stores only; the website is excluded unless asked'
    r = run_tool('get_revenue_breakdown', {'by': dims, **args}, ctx, log)
    if r.error:
        return _error_answer('breakdown', r, log)
    scope = _scope(_filter_parts(log[-1]['arguments_used'], sources, labels, params), notes)
    rows = sorted(r.value, key=lambda x: -x['revenue'])
    findings = [f'Revenue by {" and ".join(dims)}, highest first:']
    for rec in rows[:10]:
        if 'store' in dims:
            name = f"{rec['store_label']} ({rec.get('market', 'tier unknown')})"
            name += ''.join(f" · {rec[d]}" for d in dims if d != 'store')
        else:
            name = ' · '.join(MONTH_NAMES[rec[d]] if d == 'month' else str(rec[d]) for d in dims)
        findings.append(f"{name}: {money(rec['revenue'])} ({rec['share_pct']:.2f}% of this scope)")
    if len(rows) > 10:
        findings.append('The remaining rows are in the tool-call log.')
    interpretation = list(r.caveats)
    if dims == ['store']:
        note = _tier_note(rows)
        if note:
            interpretation.insert(0, note)
    return _answer('breakdown', scope, findings, interpretation,
                   ['To see change over time, ask e.g. "Which store had the greatest revenue '
                    'decline?"'], log)


def _seasonality(filters, sidebar, use_sidebar, ctx, log, labels):
    params = ('year', 'channel', 'store', 'category')
    args, sources, notes = build_args(filters, sidebar, use_sidebar, params)
    r = run_tool('get_monthly_share', args, ctx, log)
    if r.error:
        return _error_answer('seasonality', r, log)
    scope = _scope(_filter_parts(log[-1]['arguments_used'], sources, labels, params), notes)
    rows = sorted(r.value, key=lambda x: -x['share_pct'])
    if not rows:
        return _answer('seasonality', scope, ['No sales match this scope.'], r.caveats, [], log)
    describe = lambda x: f"{MONTH_NAMES[x['month']]} {x['share_pct']:.2f}% ({money(x['revenue'])})"
    findings = ['Highest months: ' + '; '.join(describe(x) for x in rows[:3]) + '.',
                f'Lowest month: {describe(rows[-1])}.']
    return _answer('seasonality', scope, findings, r.caveats,
                   ['To see one year\'s pattern, ask again with a year, e.g. "Monthly revenue '
                    'share in 2028".'], log)


def _store_trends(filters, sidebar, use_sidebar, ctx, log, labels):
    reasons = {'store': 'this question compares stores'}
    args, sources, notes = build_args(filters, sidebar, use_sidebar,
                                      ('year', 'channel', 'category', 'market'), reasons)
    years = args.pop('year', [])
    year_source = sources.pop('year', None)
    if len(years) >= 2:
        args['start_year'], args['end_year'] = min(years), max(years)
    elif years:
        notes.append(f'A trend needs two years, so the first and last years in the data are '
                     f'used ({year_source.replace("from ", "")} gave one).')
    r = run_tool('get_store_trends', args, ctx, log)
    if r.error:
        return _error_answer('store_trends', r, log)
    v = r.value
    start, end = v['start_year'], v['end_year']
    used = log[-1]['arguments_used']
    year_text = (f'{start} → {end} ({year_source})' if 'start_year' in used
                 else f'{start} → {end} (first and last years in the data)')
    channel_text = (f"{_describe('channel', used['channel'], labels)} ({sources['channel']})"
                    if 'channel' in used else
                    'physical stores only (the website is a separate channel; excluded unless asked)')
    parts = [year_text, channel_text] + _filter_parts(used, sources, labels, ('category', 'market'))
    scope = _scope(parts, notes)
    tiers = {t['market']: t for t in v['tiers']}
    findings = [f"{v['stores_declined']} of {v['stores_compared']} stores compared declined "
                f'between {start} and {end}.']
    named = []
    for s in filters.get('store', []):
        store_id, _ = normalize('store', s, ctx)
        named += store_id or []
    focus = [row for row in v['stores'] if row['store'] in named]
    if focus:
        findings += [_trend_sentence(row, tiers, start, end) for row in focus]
    elif v['largest_decline']:
        findings.append('Largest decline: ' + _trend_sentence(v['largest_decline'], tiers,
                                                              start, end))
        others = [row for row in v['stores'][1:3] if row['store'] in v['declined']]
        if others:
            findings.append('Next largest declines: ' + '; '.join(
                f"{row['store_label']} ({row['market']}) {row['change_pct']:+.2f}%"
                for row in others) + '.')
    else:
        smallest = v['stores'][0]
        findings.append(f"No store declined between {start} and {end}. Smallest growth: "
                        f"{smallest['store_label']} ({smallest['market']}) "
                        f"{smallest['change_pct']:+.2f}%.")
    findings.append('Median change by Market tier: ' + '; '.join(
        f"{t['market']} {t['median_change_pct']:+.2f}% ({t['stores']} stores)"
        for t in v['tiers'] if t['median_change_pct'] is not None) + '.')
    interpretation = list(r.caveats)
    if v['stores_compared'] and v['stores_declined'] == v['stores_compared']:
        interpretation.insert(0, 'Every store compared declined, so the question is how much, '
                                 'not whether.')
    target = focus[0] if focus else v['largest_decline']
    if target:
        next_steps = [f'For what the data can and cannot say about closing a store, ask e.g. '
                      f'"Should E-Presso close {target["store"]}?"']
    else:
        next_steps = ['Ask about one store, e.g. "How did Chicago\'s revenue change?"']
    return _answer('store_trends', scope, findings, interpretation, next_steps, log)


def _satisfaction(filters, sidebar, use_sidebar, ctx, log, labels):
    reasons = {'channel': 'only physical stores have a customer survey',
               'store': 'a correlation needs many store-years',
               'category': 'the survey is per store and year, not per category'}
    args, sources, notes = build_args(filters, sidebar, use_sidebar, ('year', 'market'), reasons)
    r = run_tool('get_satisfaction_vs_revenue', args, ctx, log)
    if r.error:
        return _error_answer('satisfaction', r, log)
    used = log[-1]['arguments_used']
    scope = _scope(_filter_parts(used, sources, labels, ('year', 'market'))
                   + ['physical stores with a survey score'], notes)
    v = r.value
    if v['correlation'] is None:
        findings = [f"Too few store-years ({v['store_years_used']}) to calculate a correlation."]
    else:
        findings = [f"Correlation between satisfaction and revenue across "
                    f"{v['store_years_used']} store-years: {v['correlation']:+.3f} "
                    f"({analytics.correlation_strength(v['correlation'])})."]
    for t in v['by_tier']:
        corr = 'not calculable' if t['correlation'] is None else f"{t['correlation']:+.2f}"
        findings.append(f"{t['market']}: correlation {corr} (n = {t['store_years']}); mean "
                        f"satisfaction {t['mean_satisfaction']:.2f}, mean store-year revenue "
                        f"{money(t['mean_store_year_revenue'])}.")
    return _answer('satisfaction', scope, findings, r.caveats,
                   [NO_RECOMMENDATION,
                    'Showing that satisfaction drives revenue would need more than this data, '
                    'e.g. a planned service change at some stores compared with others.'], log)


def _profit(filters, sidebar, use_sidebar, ctx, log, labels):
    cov = run_tool('get_data_coverage', {}, ctx, log)
    if cov.error:
        return _error_answer('profit', cov, log)
    params = ('year', 'channel', 'store', 'category')
    args, sources, notes = build_args(filters, sidebar, use_sidebar, params)
    website_excluded = 'channel' not in args and bool(_website_ids(ctx))
    if website_excluded:
        args['channel'] = _physical_channels(ctx)
        sources['channel'] = 'physical stores only; the website is excluded unless asked'
    bd = run_tool('get_revenue_breakdown', {'by': 'store', **args}, ctx, log)
    if bd.error:
        return _error_answer('profit', bd, log)
    scope = _scope(_filter_parts(log[-1]['arguments_used'], sources, labels, params), notes)
    measures = '; '.join(f"{', '.join(cols)} ({table})"
                         for table, cols in cov.value['measures'].items())
    findings = []
    if not cov.value['cost_or_profit_columns']:
        findings.append('Profit cannot be calculated: the loaded data has no cost, expense, '
                        'price, or profit columns.')
    findings.append(f'Measures in the loaded data: {measures}.')
    rows = sorted(bd.value, key=lambda x: -x['revenue'])
    if rows:
        findings.append('Highest revenue, not profit:')
        findings += [f"{x['store_label']} ({x.get('market', 'tier unknown')}): "
                     f"{money(x['revenue'])}" for x in rows[:3]]
    interpretation = []
    note = _tier_note(rows)
    if note:
        interpretation.append(note)
    if website_excluded:
        interpretation.append(f'The website ({", ".join(_website_ids(ctx))}) is a separate '
                              f'sales channel and is excluded unless you ask about it.')
    # coverage already says revenue is not profit; skip the breakdown's version of it
    interpretation += cov.caveats + [c for c in bd.caveats
                                     if not c.startswith('Revenue is not profit')]
    return _answer('profit', scope, findings, interpretation,
                   [NO_RECOMMENDATION,
                    'To compare profitability, management would need each store\'s costs: '
                    'cost of goods, staff, rent or lease, and other operating expenses.'], log)


def _decision(filters, sidebar, use_sidebar, ctx, log, labels):
    stores = filters.get('store', [])
    if not stores:
        return _store_trends(filters, sidebar, use_sidebar, ctx, log, labels) | {
            'intent': 'decision', 'next_steps': [NO_RECOMMENDATION,
                                                 'Name one store to see its evidence, e.g. '
                                                 '"Should E-Presso close the Chicago store?"']}
    yearly = run_tool('get_revenue_breakdown', {'by': 'year', 'store': stores[0]}, ctx, log)
    if yearly.error:
        return _error_answer('decision', yearly, log)
    store_id = log[-1]['arguments_used']['store'][0]
    channel = {} if store_id not in _website_ids(ctx) else {'channel': [analytics.WEBSITE_TYPE]}
    trends = run_tool('get_store_trends', channel, ctx, log)
    cov = run_tool('get_data_coverage', {}, ctx, log)
    if trends.error or cov.error:
        return _error_answer('decision', trends if trends.error else cov, log)
    v = trends.value
    start, end = v['start_year'], v['end_year']
    label = labels.get(store_id, store_id)
    scope = _scope([f'{label} ({FROM_QUESTION})',
                    f'{start} → {end} (first and last years in the data)',
                    'compared with the other physical stores and its Market tier',
                    'sidebar filters not applied (a store decision needs the full picture)'], [])
    row = next((x for x in v['stores'] if x['store'] == store_id), None)
    findings = [f'{label} revenue by year: ' + ' · '.join(
        f"{x['year']} {money(x['revenue'])}" for x in sorted(yearly.value, key=lambda x: x['year']))
        + '.']
    interpretation = []
    if row:
        tiers = {t['market']: t for t in v['tiers']}
        findings.append(_trend_sentence(row, tiers, start, end))
        findings.append(f"{v['stores_declined']} of {v['stores_compared']} stores compared "
                        f'declined over the same period.')
        if row['vs_tier_median_pts'] is not None and row['vs_tier_median_pts'] < 0:
            interpretation.append('Its decline is worse than its Market tier\'s median, so store '
                                  'size alone does not explain it.')
        elif row['vs_tier_median_pts'] is not None:
            interpretation.append('Its change is in line with or better than its Market tier\'s '
                                  'median.')
    if not cov.value['cost_or_profit_columns']:
        interpretation.append('Revenue alone cannot justify closing a store: the loaded data has '
                              'no cost or profit columns, so the store\'s profitability is unknown.')
    interpretation += [
        'Missing information: operating costs and profit, lease obligations, staffing, and '
        'customer behavior (for example, whether this store\'s customers would move to the '
        'website or to another store).',
        'A revenue trend does not explain why revenue fell; the reasons are not in the data.']
    return _answer('decision', scope, findings, interpretation,
                   [NO_RECOMMENDATION,
                    'Before deciding, management would need the store\'s costs and profit, its '
                    'lease terms, staffing, and evidence of where its customers would go.'], log)


def _quality(filters, sidebar, use_sidebar, ctx, log, labels):
    r = run_tool('data_quality_report', {}, ctx, log)
    if r.error:
        return _error_answer('quality', r, log)
    v = r.value
    missing = v['columns_with_missing']
    findings = [f"The Sales table has {v['rows']:,} rows and {v['duplicate_rows']} fully "
                f'duplicated rows.',
                'Missing values: ' + ('; '.join(f'{c} {n}' for c, n in missing.items())
                                      if missing else 'none') + '.']
    return _answer('quality', 'Scope: the whole loaded Sales table (filters do not apply).',
                   findings, r.caveats,
                   ['See the Data and profile tab for every data-quality note on all five '
                    'tables.'], log)


def _coverage(filters, sidebar, use_sidebar, ctx, log, labels):
    r = run_tool('get_data_coverage', {}, ctx, log)
    if r.error:
        return _error_answer('coverage', r, log)
    v = r.value
    findings = [
        'Measures: ' + '; '.join(f"{', '.join(c)} ({t})" for t, c in v['measures'].items()) + '.',
        f"Years: {', '.join(map(str, v['years']))}. Channels: {', '.join(v['channels'])}. "
        f"Market tiers: {', '.join(v['market_tiers'])}.",
        f"Stores: {v['stores']} ({v['physical_stores']} physical). Categories: "
        f"{', '.join(v['categories'])}."]
    return _answer('coverage', 'Scope: all loaded tables.', findings, r.caveats,
                   [f'{what}: e.g. "{example}"' for what, example in CAPABILITIES], log)


COMPOSERS = {'total': _total, 'seasonality': _seasonality, 'store_trends': _store_trends,
             'satisfaction': _satisfaction, 'profit': _profit, 'decision': _decision,
             'quality': _quality, 'coverage': _coverage}


def answer_question(question: str, ctx: Context, sidebar: dict | None = None,
                    use_sidebar: bool = True, mode: str = 'rules') -> dict:
    """Route the question, call the tools through the dispatcher, and compose the answer:
    scope, findings (numbers only from tool results), interpretation, next steps, and the
    tool-call log. `sidebar` holds the dashboard filters; the question's own filters win."""
    log: list = []
    if mode != 'rules':
        return llm_router(question, ctx)
    intent, filters = route(question, ctx)
    labels = analytics.store_labels(ctx.model) if ctx.model is not None else {}
    if intent is None:
        return _answer(None, 'Scope: no tool was run.',
                       ['I can\'t answer that with my tools and the loaded data.'], [],
                       ['I can answer questions like these:']
                       + [f'{what}: e.g. "{example}"' for what, example in CAPABILITIES], log)
    if intent == 'breakdown':
        return _breakdown(filters, sidebar, use_sidebar, ctx, log, labels, question.lower())
    return COMPOSERS[intent](filters, sidebar, use_sidebar, ctx, log, labels)


def llm_router(question: str, ctx: Context):
    """Option A router. TODO: after the rules-based version works, ask a model that
    supports function calling to choose from TOOLS (see tool_definitions)."""
    raise NotImplementedError('Add the language-model router after the rules router works.')
