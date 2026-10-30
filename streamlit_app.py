"""Main app: data profile, dashboard, and assistant for E-Presso.
Keep loading/checks in data_prep.py, calculations in analytics.py, and the assistant in agent.py.
This file only lays things out: every number on screen comes from an analytics.py function."""
import calendar

import pandas as pd
import plotly.express as px
import streamlit as st

import agent
import analytics
import data_prep

MAX_QUESTIONS = 15  # per-session limit for the assistant

# Chart colors: the first slots of a palette validated for color-blind readers. Colors are
# assigned to channel NAMES, so filtering out one channel never repaints the other.
SERIES_COLORS = ['#2a78d6', '#eb6834', '#1baf7a']  # blue, orange, aqua
SINGLE_COLOR = SERIES_COLORS[0]
MONTH_NAMES = dict(enumerate(calendar.month_abbr))  # 1 -> 'Jan'
FILTER_NAMES = {'year': 'years', 'channel': 'channels', 'store': 'stores',
                'category': 'categories'}


def md(text: str) -> str:
    """Escape dollar signs for any text Streamlit renders as Markdown (captions, markdown,
    warnings, errors, help). Otherwise two $ signs turn the text between them into math,
    e.g. "$7,181,750 → $9,181,550" shows up as a formula."""
    return str(text).replace('$', r'\$')


def compact_money(value: float) -> str:
    """Short dollar amounts for KPI tiles, e.g. $42.17M, so they fit without being cut off.
    The exact amount is shown in the caption under the tile."""
    for size, suffix in ((1e9, 'B'), (1e6, 'M'), (1e3, 'K')):
        if abs(value) >= size:
            return f'${value / size:,.2f}{suffix}'
    return f'${value:,.2f}'


def scope_text(scope: dict, labels: dict) -> str:
    """Turn a tool result's scope into a sentence, e.g. 'Scope: all years; Website; ...'."""
    parts = []
    for param, plural in FILTER_NAMES.items():
        value = scope.get(param, 'All')
        if value == 'All':
            parts.append(f'all {plural}')
        else:
            values = value if isinstance(value, list) else [value]
            parts.append(', '.join(str(labels.get(v, v)) if param == 'store' else str(v)
                                   for v in values))
    return 'Scope: ' + '; '.join(parts) + '.'


def show_data(df: pd.DataFrame, money=(), pct=()):
    """The table view under each chart, so exact values can be read and checked."""
    with st.expander('Show data'):
        formats = {**{c: '${:,.2f}' for c in money}, **{c: '{:.2f}%' for c in pct}}
        st.dataframe(df.style.format(formats), hide_index=True)


def records(result) -> pd.DataFrame | None:
    """A tool result as a table for a chart, or a plain message if there is nothing to plot."""
    if result.error:
        st.warning(md(result.error))
        return None
    if not result.value:
        st.info('No data for this chart under the current filters.')
        return None
    return pd.DataFrame(result.value)


def money_axis(fig, axis='y'):
    """Dollar ticks like $2.5M on a value axis that starts at zero."""
    update = fig.update_yaxes if axis == 'y' else fig.update_xaxes
    update(tickprefix='$', tickformat='~s', rangemode='tozero')


def show_dashboard(model: pd.DataFrame, selection: dict, total) -> None:
    """KPI tiles and four charts. Each one calls an analytics.py function with the same
    `selection`, so every result on this tab follows the sidebar filters."""
    # ---- KPI tiles
    channels = analytics.get_revenue_breakdown(model, 'channel', **selection)
    change = analytics.get_revenue_change(model, **selection)
    # Short labels and compact values, so nothing is cut off; exact figures go in the captions.
    k1, k2, k3 = st.columns(3)
    k1.metric('Total revenue', compact_money(total.value), help=md(total.definition))
    k1.caption(md(f'Exactly ${total.value:,.2f}'))
    web = next((r for r in channels.value or [] if r['channel'] == data_prep.WEBSITE_TYPE), None)
    # No Website row under the current filters (e.g. only physical stores selected) means
    # the Website share really is 0%. 'n/a' is kept for when the share can't be calculated.
    share = 'n/a' if channels.error else f'{web["share_pct"]:.1f}%' if web else '0.0%'
    k2.metric('Website share', share,
              help='Website revenue ÷ total revenue for the current filters.')
    k2.caption(md(f'Website revenue: ${web["revenue"]:,.2f}') if web
               else 'No Website sales under the current filters.')
    if change.value and change.value['change_pct'] is not None:
        v = change.value
        k3.metric('Revenue change', f'{v["change_pct"]:+.1f}%', help=md(change.definition))
        k3.caption(md(f'{v["first_year"]}: ${v["first_revenue"]:,.0f} → '
                      f'{v["last_year"]}: ${v["last_revenue"]:,.0f}'))
    else:
        k3.metric('Revenue change', 'n/a', help=md(change.definition))
        k3.caption(md(change.error or change.caveats[-1]))
    st.caption(md(' '.join(total.caveats)))

    channel_names = sorted(model['Channel'].dropna().unique()) if 'Channel' in model else []
    color_map = dict(zip(channel_names, SERIES_COLORS))

    # ---- Chart 1: revenue by year, one line per channel
    left, right = st.columns(2)
    with left:
        st.subheader('Revenue by year and channel')
        df = records(analytics.get_revenue_breakdown(model, ['year', 'channel'], **selection))
        if df is not None:
            fig = px.line(df, x='year', y='revenue', color='channel', markers=True,
                          color_discrete_map=color_map,
                          labels={'year': 'Year', 'revenue': 'Revenue', 'channel': 'Channel'})
            fig.update_traces(hovertemplate='%{fullData.name}, %{x}: $%{y:,.0f}<extra></extra>')
            fig.update_xaxes(dtick=1, tickformat='d')
            money_axis(fig)
            st.plotly_chart(fig)
            st.caption('Total revenue for each year, one line per sales channel.')
            show_data(df, money=['revenue'], pct=['share_pct'])

    # ---- Chart 2: each month's share of revenue for the selected period
    with right:
        st.subheader('Share of revenue by month')
        df = records(analytics.get_monthly_share(model, **selection))
        if df is not None:
            df['month_name'] = df['month'].map(MONTH_NAMES)
            fig = px.bar(df, x='month_name', y='share_pct', custom_data=['revenue'],
                         color_discrete_sequence=[SINGLE_COLOR],
                         labels={'month_name': 'Month',
                                 'share_pct': '% of revenue for the selected period'})
            fig.update_traces(hovertemplate='%{x}: %{y:.2f}% ($%{customdata[0]:,.0f})'
                                            '<extra></extra>')
            fig.update_yaxes(ticksuffix='%', rangemode='tozero')
            fig.update_layout(barcornerradius=4)
            st.plotly_chart(fig)
            st.caption("Each month's revenue as a percent of total revenue for the current "
                       'filters, with the selected years added together, so the bars add up '
                       "to 100%. This is not a percent of each year's revenue; select one year "
                       "to see that year's pattern.")
            show_data(df[['month', 'month_name', 'revenue', 'share_pct']], money=['revenue'],
                      pct=['share_pct'])

    # ---- Chart 3: category trends as small multiples (one panel per category)
    st.subheader('Revenue by category and year')
    df = records(analytics.get_revenue_breakdown(model, ['category', 'year'], **selection))
    if df is not None:
        categories = sorted(df['category'].unique())
        fig = px.line(df, x='year', y='revenue', facet_col='category',
                      facet_col_wrap=3, facet_col_spacing=0.08, facet_row_spacing=0.18,
                      height=260 * ((len(categories) + 2) // 3) + 60,
                      category_orders={'category': categories}, markers=True,
                      color_discrete_sequence=[SINGLE_COLOR],
                      labels={'year': 'Year', 'revenue': 'Revenue'})
        fig.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))
        fig.update_traces(hovertemplate='%{x}: $%{y:,.0f}<extra></extra>')
        # every other year, starting from the first one, so narrow panels fit
        fig.update_xaxes(dtick=2, tick0=int(df['year'].min()), tickformat='d',
                         showticklabels=True)  # label every panel, not just the bottom row
        fig.update_yaxes(matches=None, showticklabels=True)
        money_axis(fig)
        st.plotly_chart(fig)
        st.caption('One panel per product category. Each panel has its own vertical scale, so '
                   'read the axis values before comparing panels: a small category is not '
                   'mistaken for a big one.')
        show_data(df, money=['revenue'], pct=['share_pct'])

    # ---- Chart 4: revenue by store, sorted. The website earns far more than any one physical
    # store, so by default it is left out (with a checkbox and a caption saying so); otherwise
    # the physical stores shrink to slivers. Website store IDs come from the data.
    st.subheader('Revenue by store')
    web_ids = sorted(model.loc[model['Channel'] == data_prep.WEBSITE_TYPE, 'Store ID'].unique()) \
        if 'Channel' in model else []
    store_selection = dict(selection)
    if web_ids:
        include_web = st.checkbox(f'Include the website ({", ".join(web_ids)})', value=False,
                                  key='store_chart_include_website')
        if not include_web:
            # An empty Channel filter means "all channels", so start from every channel.
            chosen = selection.get('channel') or channel_names
            remaining = [c for c in chosen if c != data_prep.WEBSITE_TYPE]
            if not remaining:
                st.info('Only the website is selected in the Channel filter. Tick "Include the '
                        'website" to show it.')
                return
            store_selection['channel'] = remaining
            amount = md(f' (${web["revenue"]:,.2f} under the current filters)') if web else ''
            st.caption(f'The website ({", ".join(web_ids)}) is excluded from this chart{amount} '
                       f'so the physical stores can be compared. Tick the box to include it.')
    df = records(analytics.get_revenue_breakdown(model, 'store', **store_selection))
    if df is not None:
        df = df.merge(model[['Store ID', 'Channel']].drop_duplicates(), how='left',
                      left_on='store', right_on='Store ID').sort_values('revenue')
        fig = px.bar(df, x='revenue', y='store_label', color='Channel', orientation='h',
                     color_discrete_map=color_map, height=max(250, 26 * len(df) + 100),
                     labels={'revenue': 'Revenue', 'store_label': 'Store'})
        fig.update_traces(hovertemplate='%{y}: $%{x:,.0f}<extra></extra>')
        fig.update_yaxes(categoryorder='array', categoryarray=list(df['store_label']))
        fig.update_layout(barcornerradius=4, showlegend=df['Channel'].nunique() > 1)
        money_axis(fig, axis='x')
        st.plotly_chart(fig)
        st.caption('Stores are identified by ID, because a city can have more than one store. '
                   'Shares in the table are of the revenue shown in this chart.')
        show_data(df[['store', 'store_label', 'Channel', 'revenue', 'share_pct']],
                  money=['revenue'], pct=['share_pct'])

st.set_page_config(page_title='E-Presso BI Analyst', layout='wide')
st.title('E-Presso BI Analyst')
st.caption('Revenue, store, product, and customer-survey analysis for E-Presso managers.')


@st.cache_data(show_spinner='Loading data...')
def cached_load(files: dict):
    # The cache is keyed on the file CONTENTS (the bytes inside `files`), so a modified
    # file is never confused with the original one.
    return data_prep.load_tables(files)


# Reserve the top of the sidebar for the dashboard filters. They are filled in further down,
# after the data has loaded, because the filter lists are built from the data.
filter_area = st.sidebar.container()

with st.sidebar:
    st.divider()
    st.header('Data')
    st.caption('The app uses the original E-Presso files. To use updated data, upload a file '
               'with the same name; it replaces that table only.')
    uploaded = st.file_uploader('Upload updated E-Presso files',
                                type=['csv', 'txt', 'tsv', 'xlsx', 'xls'],
                                accept_multiple_files=True)
    files, problems = data_prep.collect_files({f.name: f.getvalue() for f in uploaded})
    st.subheader('Loaded from')
    st.caption('Row counts and the revenue sum show which file is really loaded. Two files can '
               'share a name (e.g. an original and a modified Sales.csv), so check these after '
               'every upload.')
    loaded_area = st.container()  # filled in below, once the files have been read

tables, load_problems = cached_load(files)
summary = data_prep.loaded_summary(files, tables)
with loaded_area:
    for _, row in summary.iterrows():
        if pd.isna(row['rows']):
            detail = 'not loaded'
        else:
            detail = f'{int(row["rows"]):,} rows'
            if pd.notna(row['revenue sum']):
                detail += f' · revenue sum ${row["revenue sum"]:,.2f}'
        st.markdown(md(f'**{row["table"]}:** `{row["file"]}` ({row["source"]}) · {detail}'))
model, merge_log, model_problems = data_prep.build_sales_model(tables)
problems = problems + load_problems + model_problems
for problem in problems:
    st.error(md(problem))
if not tables:
    st.stop()

# Dashboard filters. Every option list is built from the loaded data (never typed in), and the
# same `selection` is passed to every KPI and chart, so they always agree.
selection, labels = {}, {}
if model is not None:
    labels = analytics.store_labels(model)
    with filter_area:
        st.header('Dashboard filters')
        st.caption('Leave a filter empty to include everything.')
        cleared = []
        for param, col in analytics.REVENUE_FILTERS.items():
            if col not in model.columns:
                continue
            options = sorted(model[col].dropna().unique().tolist())
            key = f'filter_{param}'
            # After a new upload, drop selections that no longer exist in the data.
            if key in st.session_state:
                kept = [v for v in st.session_state[key] if v in options]
                if len(kept) < len(st.session_state[key]):
                    st.session_state[key] = kept
                    cleared.append(FILTER_NAMES[param])
            selection[param] = st.multiselect(
                param.capitalize(), options, key=key, placeholder=f'All {FILTER_NAMES[param]}',
                format_func=(lambda v: labels.get(v, v)) if param == 'store' else str)
        if cleared:
            st.info(md(f'Some selected {", ".join(cleared)} are not in the newly loaded data '
                       f'and were cleared.'))

tab_data, tab_dash, tab_assistant = st.tabs(['Data and profile', 'Dashboard', 'Assistant'])

with tab_data:
    st.subheader('Loaded tables')
    st.dataframe(summary.style.format({'rows': '{:,.0f}', 'columns': '{:,.0f}',
                                       'revenue sum': '${:,.2f}'}, na_rep=''),
                 hide_index=True)

    st.subheader('Data-quality notes')
    st.caption('Expected = explained, not an error. Info = worth knowing. '
               'Review = a person should check it.')
    # A wrapped list rather than a table, so long notes are never cut off. The notes arrive
    # sorted Review -> Info -> Expected; a caveat for a group of notes (e.g. Location) is
    # shown once, right after the last note in that group.
    notes = data_prep.data_quality_notes(tables)
    if notes.empty:
        st.success('No data-quality issues found.')
    else:
        st.markdown(f'**{data_prep.notes_summary(notes)}**')
        lines = []
        for i, note in enumerate(notes.itertuples(index=False)):
            lines.append(f'- **{note.level}** · {note.table}: {note.note}')
            next_topic = notes['topic'].iloc[i + 1] if i + 1 < len(notes) else None
            caveat = data_prep.TOPIC_CAVEATS.get(note.topic)
            if caveat and next_topic != note.topic:
                st.markdown(md('\n'.join(lines)))
                st.caption(md(f'Note on the Location items above: {caveat}'
                              if note.topic == 'location' else caveat))
                lines = []
        if lines:
            st.markdown(md('\n'.join(lines)))

    left, right = st.columns(2)
    left.subheader('Key checks')
    left.caption('Each table\'s key should be unique and never blank (see the grain statements).')
    left.dataframe(data_prep.key_checks(tables), hide_index=True)
    right.subheader('Relationship checks')
    right.caption('Rows whose key has no match in the lookup table would drop out of joins.')
    right.dataframe(data_prep.relationship_checks(tables), hide_index=True)

    st.subheader('Merge checks')
    st.caption('Sales is joined to each lookup table. Rows and revenue must be the same before '
               'and after every join; otherwise the join duplicated or dropped revenue.')
    if merge_log.empty:
        st.info('No joins were run because the Sales table did not load.')
    else:
        st.dataframe(merge_log.style.format({'revenue before': '${:,.2f}',
                                             'revenue after': '${:,.2f}'}), hide_index=True)

    st.subheader('Table profiles')
    for table, df in tables.items():
        with st.expander(f'{table} ({len(df):,} rows)'):
            profile = analytics.profile_table(df)
            c1, c2, c3 = st.columns(3)
            c1.metric('Rows', f"{profile['rows']:,}")
            c2.metric('Columns', profile['columns'])
            c3.metric('Duplicate rows', profile['duplicate_rows'])
            st.dataframe(df.head(50))
            left, right = st.columns(2)
            left.markdown('**Missing values**')
            left.dataframe(profile['missing'], hide_index=True)
            right.markdown('**Data types**')
            right.dataframe(profile['dtypes'], hide_index=True)

with tab_dash:
    total = analytics.get_total_revenue(model, **selection)
    if total.error:
        st.warning(md(total.error))
    else:
        st.markdown(md(f'**{scope_text(total.scope, labels)}** Change the filters in the '
                       f'sidebar.'))
        if total.rows_used == 0:
            st.warning('No sales match these filters. Remove a filter in the sidebar to see '
                       'results.')
        else:
            show_dashboard(model, selection, total)

with tab_assistant:
    st.caption('Mode: rules-based starter. Describe what you actually built here.')
    # The tools read the data loaded right now (an upload is used at once); the fingerprint
    # records in each tool-call log entry which data that was.
    ctx = agent.make_context(model, tables, summary)
    if model is None:
        st.warning('Revenue questions need the Sales table, which did not load.')
    st.session_state.setdefault('n_questions', 0)
    st.session_state.setdefault('history', [])
    for item in st.session_state['history']:
        with st.chat_message('user'):
            st.write(item['question'])
        with st.chat_message('assistant'):
            st.markdown(md(f"**Scope:** {item['answer']['scope']}"))
            st.markdown(md(f"**Findings:** {item['answer']['findings']}"))
            if item['answer']['interpretation']:
                st.markdown(md(f"**Interpretation:** {item['answer']['interpretation']}"))
            with st.expander('Tool-call log'):
                st.json(item['answer']['tool_log'])
    question = st.chat_input('Ask a question about the loaded data')
    if question:
        if st.session_state['n_questions'] >= MAX_QUESTIONS:
            st.warning('Question limit reached for this session. Reload the page to start over.')
        else:
            st.session_state['n_questions'] += 1
            answer = agent.answer_question(question, ctx, mode='rules')
            st.session_state['history'].append({'question': question, 'answer': answer})
            st.rerun()
