"""A fake Gemini client for tests: plays back a scripted conversation, so no test ever calls
the real API or uses quota. Shared by tests/test_llm.py and tests/test_app.py."""
from llm_client import ModelTurn


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



# What the live Gemini API accepts as a content role. Defect 2 (docs/agent-tests.md): tool
# results were first sent with role 'tool', and the API answered "400 INVALID_ARGUMENT. Role
# 'tool' is not supported". The stub below rejects the same roles, so that bug fails a test.
VALID_CONTENT_ROLES = {'user', 'model'}


class StubSDK:
    """Stands in for google-genai's Client at the request level: checks each request like the
    live API (roles) and returns real google-genai response objects. No network."""

    def __init__(self, responses):
        self.responses, self.requests = list(responses), []
        self.models = self

    def generate_content(self, model, contents, config):
        from google.genai import errors  # only needed by tests that use google-genai
        roles = [c.role for c in contents]
        self.requests.append({'model': model, 'roles': roles, 'contents': list(contents),
                              'config': config})
        bad = [r for r in roles if r not in VALID_CONTENT_ROLES]
        if bad:
            raise errors.ClientError(400, {'error': {
                'code': 400, 'status': 'INVALID_ARGUMENT',
                'message': f"Role '{bad[0]}' is not supported. Please use a valid role: "
                           f"SYSTEM, USER, MODEL."}})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response
