"""Assistant: a tool registry, a dispatcher, and a router.
The router (rules now, a language model later) only CHOOSES a tool and its arguments. The
dispatcher (run_tool) checks those arguments against the loaded data, runs the tool, and logs
the call. Nothing here executes model-written code, and no tool changes the loaded data."""
from __future__ import annotations

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


# ---------------------------------------------------------------- routers
def rules_router(question: str, ctx: Context):
    """Option B router (Checkpoint 4 adds the real rules).
    Returns (tool_name, arguments) or None if the question is unsupported."""
    q = question.lower()
    if any(w in q for w in ('missing', 'duplicate', 'quality', 'blank')):
        return 'data_quality_report', {}
    return None


def llm_router(question: str, ctx: Context):
    """Option A router. TODO: after the rules-based version works, ask a model that
    supports function calling to choose from TOOLS. Return (name, args) or None."""
    raise NotImplementedError('Add the language-model router after your tools are tested.')


def format_findings(result: ToolResult) -> str:
    if result.error:
        return f'The request could not be completed: {result.error}'
    return f'{result.definition}: {result.value}  (rows used: {result.rows_used})'


def answer_question(question: str, ctx: Context, mode: str = 'rules') -> dict:
    log: list = []
    routed = rules_router(question, ctx) if mode == 'rules' else llm_router(question, ctx)
    if routed is None:
        return {'scope': 'n/a', 'findings': UNSUPPORTED, 'interpretation': '',
                'next_steps': '', 'tool_log': log}
    name, args = routed
    result = run_tool(name, args, ctx, log)
    return {
        'scope': str(result.scope),
        'findings': format_findings(result),
        'interpretation': ' '.join(result.caveats),
        'next_steps': '',
        'tool_log': log,
    }
