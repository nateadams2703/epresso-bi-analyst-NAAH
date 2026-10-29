"""Main app. Checkpoint 1: loads the five E-Presso tables and shows a data profile.
Keep loading/checks in data_prep.py, calculations in analytics.py, and the assistant in agent.py."""
import pandas as pd
import streamlit as st

import agent
import analytics
import data_prep

MAX_QUESTIONS = 15  # per-session limit for the assistant

st.set_page_config(page_title='E-Presso BI Analyst', layout='wide')
st.title('E-Presso BI Analyst')
st.caption('Revenue, store, product, and customer-survey analysis for E-Presso managers.')


@st.cache_data(show_spinner='Loading data...')
def cached_load(files: dict):
    # The cache is keyed on the file CONTENTS (the bytes inside `files`), so a modified
    # file is never confused with the original one.
    return data_prep.load_tables(files)


with st.sidebar:
    st.header('Data')
    st.caption('The app uses the original E-Presso files. To use updated data, upload a file '
               'with the same name; it replaces that table only.')
    uploaded = st.file_uploader('Upload updated E-Presso files',
                                type=['csv', 'txt', 'tsv', 'xlsx', 'xls'],
                                accept_multiple_files=True)
    files, problems = data_prep.collect_files({f.name: f.getvalue() for f in uploaded})
    st.subheader('Loaded from')
    for table, f in files.items():
        st.markdown(f'**{table}:** `{f["name"]}` ({f["source"]})')

tables, load_problems = cached_load(files)
model, merge_log, model_problems = data_prep.build_sales_model(tables)
problems = problems + load_problems + model_problems
for problem in problems:
    st.error(problem)
if not tables:
    st.stop()

tab_data, tab_dash, tab_assistant = st.tabs(['Data and profile', 'Dashboard', 'Assistant'])

with tab_data:
    st.subheader('Loaded tables')
    st.dataframe(pd.DataFrame([{'table': table, 'file': files[table]['name'],
                                'source': files[table]['source'], 'rows': len(df),
                                'columns': df.shape[1]} for table, df in tables.items()]),
                 hide_index=True)

    st.subheader('Data-quality notes')
    st.caption('Expected = explained, not an error. Info = worth knowing. '
               'Review = a person should check it.')
    st.dataframe(data_prep.data_quality_notes(tables), hide_index=True)

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
    st.info('TODO: KPIs, filters, and at least three charts go here. '
            'Calculate everything from the loaded data. Never hardcode results.')

with tab_assistant:
    st.caption('Mode: rules-based starter. Describe what you actually built here.')
    df = tables.get('Sales')  # temporary: the starter tools work on one table (Checkpoint 3)
    if df is None:
        st.warning('The assistant needs the Sales table, which did not load.')
        st.stop()
    st.session_state.setdefault('n_questions', 0)
    st.session_state.setdefault('history', [])
    for item in st.session_state['history']:
        with st.chat_message('user'):
            st.write(item['question'])
        with st.chat_message('assistant'):
            st.markdown(f"**Scope:** {item['answer']['scope']}")
            st.markdown(f"**Findings:** {item['answer']['findings']}")
            if item['answer']['interpretation']:
                st.markdown(f"**Interpretation:** {item['answer']['interpretation']}")
            with st.expander('Tool-call log'):
                st.json(item['answer']['tool_log'])
    question = st.chat_input('Ask a question about the loaded data')
    if question:
        if st.session_state['n_questions'] >= MAX_QUESTIONS:
            st.warning('Question limit reached for this session. Reload the page to start over.')
        else:
            st.session_state['n_questions'] += 1
            answer = agent.answer_question(question, df, mode='rules')
            st.session_state['history'].append({'question': question, 'answer': answer})
            st.rerun()
