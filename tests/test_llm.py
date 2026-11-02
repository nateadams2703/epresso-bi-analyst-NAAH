"""Tests for the language-model assistant (Option A). A fake Gemini client plays back a
scripted conversation, so no test calls the real API or uses quota. The last section tests
llm_client.py itself against google-genai's real types (skipped if the package is missing)."""
import ast
import json
import logging
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import agent  # noqa: E402
import data_prep  # noqa: E402
import llm_client  # noqa: E402
from llm_client import LLMError, ModelTurn  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def context(uploads=None):
    files, _ = data_prep.collect_files(uploads)
    tables, _ = data_prep.load_tables(files)
    model = data_prep.build_sales_model(tables)[0]
    return agent.make_context(model, tables, data_prep.loaded_summary(files, tables))


@pytest.fixture(scope='module')
def ctx():
    return context()


class FakeSession:
    """Plays back a script. A list = the model asks for those tools; a str = a text reply
    with no tool request; a dict = the final written answer; an LLMError = an API failure."""

    def __init__(self, script, seen):
        self.script, self.seen = script, seen

    def _next(self):
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step

    def _turn(self):
        step = self._next()
        return ModelTurn(function_calls=step) if isinstance(step, list) else ModelTurn(text=step)

    def send(self, text):
        self.seen['question'] = text
        return self._turn()

    def send_tool_results(self, results):
        self.seen.setdefault('results', []).append(results)
        return self._turn()

    def final_answer(self, instruction, schema):
        self.seen['schema'] = schema
        return self._next()


class FakeClient:
    model = 'fake-gemini'

    def __init__(self, *script):
        self.script, self.seen = list(script), {}

    def start(self, system, definitions):
        self.seen['system'], self.seen['definitions'] = system, definitions
        return FakeSession(self.script, self.seen)


def answer(text, findings=(), interpretation=('Revenue is not profit.',),
           next_steps=('Ask a follow-up question.',)):
    return {'findings': list(findings) or [text], 'interpretation': list(interpretation),
            'next_steps': list(next_steps)}


def ask(ctx, question, client, **kwargs):
    return agent.llm_answer(question, ctx, client=client, **kwargs)


# ---------------------------------------------------------------- the normal path
def test_gemini_answer_runs_tools_through_the_dispatcher(ctx):
    client = FakeClient([('get_total_revenue', {'year': [2028], 'channel': ['website']})],
                        'done', answer('Total revenue: $6,339,640.00.'))
    out = ask(ctx, 'How much revenue did the website generate in 2028?', client)
    assert out['mode'] == 'llm' and out['fallback'] is None
    assert out['answered_by'] == 'Gemini (fake-gemini), function calling'
    entry = out['tool_log'][0]
    assert entry['status'] == 'ok' and entry['arguments_used'] == {'year': [2028],
                                                                    'channel': ['Website']}
    assert client.seen['results'][0][0][1]['value'] == 6339640.0  # the result Gemini saw
    assert out['scope'] == ('Scope: get_total_revenue: 2028 (from your question); '
                            'Website (from your question).')
    assert out['model_calls'] == 3


def test_gemini_sees_only_our_tool_definitions_and_the_rules(ctx):
    client = FakeClient([('get_data_coverage', {})], 'done', answer('Measures: Revenue.'))
    ask(ctx, 'What data do you have?', client)
    assert [d['name'] for d in client.seen['definitions']] == list(agent.TOOLS)
    assert 'Never calculate new numbers yourself' in client.seen['system']
    assert 'No dashboard filters apply' in client.seen['system']
    assert client.seen['schema']['required'] == ['findings', 'interpretation', 'next_steps']


# ---------------------------------------------------------------- the number check
@pytest.mark.parametrize('text', ['Total revenue: $6,339,640.00.', 'About $6.34M in 2028.',
                                  'Roughly $6.3 million.', 'Website revenue was 6,339,640.',
                                  'It was $6.34 million, from 240 monthly rows.'])
def test_rounded_and_formatted_tool_numbers_are_accepted(ctx, text):
    client = FakeClient([('get_total_revenue', {'year': [2028], 'channel': ['Website']})],
                        'done', answer(text))
    assert ask(ctx, 'Website revenue in 2028?', client)['mode'] == 'llm'


def test_an_invented_number_falls_back_and_says_why(ctx, caplog):
    client = FakeClient([('get_total_revenue', {'year': [2028], 'channel': ['Website']})],
                        'done', answer('Website revenue was $6.5M, up 12% on 2027.'))
    with caplog.at_level(logging.WARNING, logger='epresso.assistant'):
        out = ask(ctx, 'How much revenue did the website generate in 2028?', client)
    assert out['mode'] == 'rules' and out['fallback']['kind'] == 'unsupported_number'
    # 2027 is flagged too: no tool fetched 2027 data, so "up on 2027" is unsupported
    assert out['fallback']['detail'] == '$6.5M, 12%, 2027'
    assert out['findings'][0] == 'Total revenue: $6,339,640.00.'  # the rules answer
    assert len(out['llm_attempt_log']) == 1                      # what Gemini tried is kept
    assert 'Assistant fallback (unsupported_number)' in caplog.text


def test_numbers_from_the_question_are_accepted(ctx):
    client = FakeClient([('get_revenue_breakdown', {'by': ['store'], 'year': [2027]})],
                        'done', answer('These are the top 5 stores by revenue in 2027.'))
    assert ask(ctx, 'Which were the top 5 stores by revenue in 2027?', client)['mode'] == 'llm'


def test_numbers_must_come_from_the_current_data(ctx):
    """$270,100 is right after the $1,000 upload, but not for the original data."""
    script = [[('get_total_revenue', {'store': ['Chicago'], 'year': [2028]})], 'done',
              answer("Chicago's 2028 revenue was $270,100.")]
    assert ask(ctx, "What was Chicago's revenue in 2028?", FakeClient(*script))['mode'] == 'rules'
    updated = context({'Sales.csv': (data_prep.DATA_DIR / 'modified' / 'Sales.csv').read_bytes()})
    out = ask(updated, "What was Chicago's revenue in 2028?", FakeClient(*script))
    assert out['mode'] == 'llm' and '(uploaded)' in out['tool_log'][0]['data']


# ---------------------------------------------------------------- the five agent tests
FIVE_TESTS = [
    ('How much revenue did the website generate in 2028?',
     [('get_total_revenue', {'year': [2028], 'channel': ['Website']})],
     ['The website generated $6.34 million in 2028, based on 240 monthly sales rows.']),
    ('Which store experienced the greatest percentage revenue decline?',
     [('get_store_trends', {})],
     ['All 20 of 20 physical stores declined between 2025 and 2029.',
      'Chicago (SH11, 4-Large) declined most: -66.8%, from $539,740 to $179,130.',
      'That is 19.5 points below the 4-Large median of -47.3%.']),
    ('Which E-Presso store is the most profitable?',
     [('get_data_coverage', {}),
      ('get_revenue_breakdown', {'by': ['store'], 'channel': ['Brick & Mortar']})],
     ['Profit cannot be calculated: the data has no cost or profit columns.',
      'Highest revenue, not profit: Phoenix $2.53M, Baltimore $1.94M, Chicago $1.75M.']),
    ('Does higher customer satisfaction cause higher revenue?',
     [('get_satisfaction_vs_revenue', {})],
     ['Across 100 store-years the correlation is weak (r = 0.24).',
      'Within tiers it is near zero (1-Small -0.01, 2-Minor -0.09, 3-Medium -0.01) except '
      '4-Large at +0.18 with only n = 15.']),
    ("What was Chicago's revenue in 2028?",
     [('get_total_revenue', {'store': ['Chicago'], 'year': [2028]})],
     ["Chicago's revenue in 2028 was $269,100."]),
]


@pytest.mark.parametrize('question, calls, findings', FIVE_TESTS)
def test_realistic_answers_to_the_five_agent_tests_are_not_rejected(ctx, question, calls,
                                                                    findings):
    out = ask(ctx, question, FakeClient(calls, 'done', answer('', findings=findings)))
    assert out['mode'] == 'llm', out.get('fallback')
    assert all(e['status'] == 'ok' for e in out['tool_log'])


# ---------------------------------------------------------------- what the model asks for
def test_unknown_tool_is_refused_by_the_dispatcher_and_logged(ctx):
    client = FakeClient([('run_python', {'code': 'import os'})], 'I could not do that.')
    out = ask(ctx, 'How much revenue did the website generate in 2028?', client)
    assert out['mode'] == 'rules' and out['fallback']['kind'] == 'no_successful_tool'
    attempt = out['llm_attempt_log'][0]
    assert attempt['tool'] == 'run_python' and attempt['status'] == 'error'
    assert 'Unknown tool' in client.seen['results'][0][0][1]['error']  # Gemini was told


def test_bad_argument_from_the_model_is_an_error_result(ctx):
    client = FakeClient([('get_total_revenue', {'year': [2031]})], 'Sorry.')
    out = ask(ctx, 'Revenue in 2031?', client)
    assert out['fallback']['kind'] == 'no_successful_tool'
    assert 'not in the loaded data' in out['fallback']['detail']


def test_a_model_that_keeps_calling_tools_is_stopped(ctx):
    call = [('get_total_revenue', {})]
    out = ask(ctx, 'Total revenue?', FakeClient(*[call] * 10))
    assert out['fallback']['kind'] == 'call_limit'
    assert len(out['llm_attempt_log']) <= agent.MAX_TOOL_CALLS


def test_too_many_tool_calls_in_one_turn_are_refused(ctx):
    out = ask(ctx, 'Total revenue?', FakeClient([('get_total_revenue', {})] * 7))
    assert out['fallback']['kind'] == 'call_limit' and out['llm_attempt_log'] == []


def test_answer_without_any_tool_falls_back_to_the_capability_list(ctx):
    out = ask(ctx, 'What is the weather in Chicago?', FakeClient('It is sunny in Chicago.'))
    assert out['fallback']['kind'] == 'no_tool_called'
    assert out['intent'] is None and "can't answer" in out['findings'][0]


# ---------------------------------------------------------------- API failures
@pytest.mark.parametrize('kind', ['quota', 'timeout', 'unavailable', 'key_rejected'])
def test_api_failures_fall_back_with_a_clear_message(ctx, kind):
    out = ask(ctx, 'Total revenue?', FakeClient(LLMError(kind, 'details')))
    assert out['mode'] == 'rules' and out['fallback']['kind'] == kind
    assert out['fallback']['message'].startswith('The language model did not answer (')
    assert out['findings'][0].startswith('Total revenue: $')


def test_missing_key_falls_back(ctx):
    out = agent.answer_question('Total revenue?', ctx, mode='llm', client=None)
    assert out['fallback']['kind'] == 'missing_key'
    assert out['fallback']['reason'] == 'no Gemini API key is configured'


@pytest.mark.parametrize('written', [{'findings': 'not a list', 'interpretation': [],
                                      'next_steps': []},
                                     {'findings': [], 'interpretation': [], 'next_steps': []},
                                     ['not', 'a', 'dict'],
                                     LLMError('bad_response', 'Gemini did not return valid JSON.')])
def test_a_badly_shaped_answer_falls_back(ctx, written):
    out = ask(ctx, 'Total revenue?', FakeClient([('get_total_revenue', {})], 'done', written))
    assert out['fallback']['kind'] == 'bad_response'


# ---------------------------------------------------------------- scope and wording
def test_scope_labels_question_sidebar_and_model_choices(ctx):
    client = FakeClient([('get_total_revenue', {'year': [2028], 'store': ['SH11'],
                                                'category': ['Beans']})],
                        'done', answer('Total revenue: $269,100.00 is the store total.',
                                       findings=['Beans revenue was found.']))
    out = ask(ctx, 'What was revenue in 2028?', client,
              sidebar={'store': ['SH11'], 'channel': ['Brick & Mortar']})
    assert '2028 (from your question)' in out['scope']
    assert 'SH11 – Chicago, IL (from the sidebar filter)' in out['scope']
    assert 'Beans (chosen by the model)' in out['scope']
    assert out['scope'].endswith('Sidebar filter(s) not used by the model: channel.')
    assert "store = ['SH11']" in client.seen['system']


def test_decision_answer_always_starts_next_steps_with_no_recommendation(ctx):
    client = FakeClient([('get_store_trends', {'store': ['Chicago']}), ('get_data_coverage', {})],
                        'done', answer('', findings=['Chicago declined -66.81% from 2025 to 2029.'],
                                       next_steps=['Gather cost and lease data for SH11.']))
    out = ask(ctx, 'Should E-Presso close the Chicago store?', client)
    assert out['mode'] == 'llm'
    assert out['next_steps'] == [agent.NO_RECOMMENDATION, 'Gather cost and lease data for SH11.']


def test_rules_answers_are_labelled_too(ctx):
    out = agent.answer_question('Total revenue?', ctx)
    assert out['mode'] == 'rules' and out['answered_by'] == 'rules-based assistant'
    assert out['fallback'] is None


def test_llm_answer_does_not_change_the_loaded_data(ctx):
    model = ctx.model.copy()
    ask(ctx, 'Which store declined most?',
        FakeClient([('get_store_trends', {})], 'done', answer('All 20 of 20 declined.')))
    pd.testing.assert_frame_equal(ctx.model, model)


# ---------------------------------------------------------------- no code execution, anywhere
@pytest.mark.parametrize('filename', ['agent.py', 'llm_client.py', 'analytics.py',
                                      'data_prep.py', 'streamlit_app.py'])
def test_no_eval_exec_or_compile_in_the_app(filename):
    tree = ast.parse(open(os.path.join(ROOT, filename)).read())
    called = {node.func.id for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    assert not called & {'eval', 'exec', 'compile', '__import__'}


# ---------------------------------------------------------------- llm_client.py itself
def test_key_is_scrubbed_from_error_messages():
    error = llm_client._as_llm_error(Exception('bad request for key AIza-secret-123'),
                                     'AIza-secret-123')
    assert 'AIza-secret-123' not in str(error) and '[hidden key]' in str(error)


@pytest.mark.parametrize('exc, kind', [
    (type('ClientError', (Exception,), {'code': 429})('429 RESOURCE_EXHAUSTED'), 'quota'),
    (type('ClientError', (Exception,), {'code': 400})('API_KEY_INVALID'), 'key_rejected'),
    (type('ReadTimeout', (Exception,), {})('slow'), 'timeout'),
    (type('ServerError', (Exception,), {'code': 503})('overloaded'), 'unavailable'),
])
def test_api_errors_map_to_plain_kinds(exc, kind):
    assert llm_client._as_llm_error(exc, 'k').kind == kind


def test_client_without_a_key_raises_missing_key():
    with pytest.raises(LLMError) as err:
        llm_client.GeminiClient(api_key='')
    assert err.value.kind == 'missing_key'


class StubSDK:
    """Stands in for google-genai's Client: returns real google-genai response objects."""

    def __init__(self, responses):
        self.responses, self.requests = list(responses), []
        self.models = self

    def generate_content(self, model, contents, config):
        self.requests.append({'model': model, 'roles': [c.role for c in contents],
                              'config': config})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_gemini_client_round_trip_with_real_types(ctx):
    types = pytest.importorskip('google.genai.types')

    def reply(**part):
        return types.GenerateContentResponse(candidates=[types.Candidate(
            content=types.Content(role='model', parts=[types.Part(**part)]))])

    stub = StubSDK([
        reply(function_call=types.FunctionCall(name='get_total_revenue', args={'year': [2028]})),
        reply(text='I have what I need.'),
        reply(text=json.dumps(answer('Total revenue: $8,969,470.00.'))),
    ])
    client = llm_client.GeminiClient(api_key='test-key', sdk_client=stub)
    out = agent.llm_answer('What was revenue in 2028?', ctx, client=client)
    assert out['mode'] == 'llm' and out['findings'] == ['Total revenue: $8,969,470.00.']
    first = stub.requests[0]['config']
    assert first.automatic_function_calling.disable is True       # the SDK never runs tools
    names = [d.name for d in first.tools[0].function_declarations]
    assert names == list(agent.TOOLS)
    assert stub.requests[1]['roles'] == ['user', 'model', 'tool']  # results sent as role 'tool'
    assert stub.requests[2]['config'].response_mime_type == 'application/json'
    assert stub.requests[0]['model'] == llm_client.DEFAULT_MODEL == 'gemini-3.5-flash-lite'


def test_gemini_client_quota_error_becomes_a_fallback(ctx):
    pytest.importorskip('google.genai')
    stub = StubSDK([type('ClientError', (Exception,), {'code': 429})('RESOURCE_EXHAUSTED')])
    client = llm_client.GeminiClient(api_key='test-key', sdk_client=stub)
    out = agent.llm_answer('Total revenue?', ctx, client=client)
    assert out['fallback']['kind'] == 'quota'
