"""The only file that talks to the Gemini API (the google-genai package).

It is a thin adapter: agent.py decides what to do, and the tests replace this client with a
fake one, so they never use API quota. The model can only *ask* for one of our named tools;
nothing in this file runs anything the model writes. The API key is passed in by the app
(from st.secrets) and is never logged or shown: it is removed from every error message.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

DEFAULT_MODEL = 'gemini-3.5-flash-lite'  # stable, supports function calling, free tier
TIMEOUT_SECONDS = 30


# Free-tier limits for DEFAULT_MODEL, as shown on AI Studio's rate-limit page for the team's
# key (checked by Audrey, Nov 2 2026). Google can change them; they are used only in messages.
FREE_TIER_LIMITS = 'about 15 requests per minute and 500 per day for gemini-3.5-flash-lite'


class LLMError(Exception):
    """A failure talking to the model. `kind` is one of: missing_key, key_rejected, quota,
    quota_minute, quota_day, timeout, unavailable, bad_response. The message never contains
    the API key."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind


def scrub(text, secret: str | None) -> str:
    """Remove the API key from a message, in case an error ever echoes it."""
    text = str(text)
    return text.replace(secret, '[hidden key]') if secret else text


def _as_llm_error(exc: Exception, key: str | None) -> LLMError:
    """Translate an exception from google-genai into an LLMError with a plain kind."""
    message = scrub(exc, key)
    code = getattr(exc, 'code', None)
    upper = message.upper()
    if code == 429 or 'RESOURCE_EXHAUSTED' in upper:
        # Gemini names the limit in the error details, e.g. quotaId
        # "GenerateRequestsPerDayPerProjectPerModel-FreeTier".
        compact = upper.replace(' ', '').replace('_', '')
        if 'PERDAY' in compact:
            return LLMError('quota_day', 'Gemini daily request limit reached (429).')
        if 'PERMINUTE' in compact:
            return LLMError('quota_minute', 'Gemini per-minute limit reached (429).')
        return LLMError('quota', 'Gemini free-tier limit reached (429).')
    if code in (401, 403) or 'API_KEY_INVALID' in upper or 'API KEY NOT VALID' in upper:
        return LLMError('key_rejected', 'Gemini rejected the API key.')
    if 'TIMEOUT' in type(exc).__name__.upper() or 'TIMED OUT' in upper:
        return LLMError('timeout', f'Gemini did not answer within {TIMEOUT_SECONDS} seconds.')
    if code == 404:
        return LLMError('unavailable', f'Gemini model not found: {message}')
    return LLMError('unavailable', f'Gemini request failed: {message}')


@dataclass
class ModelTurn:
    """What the model returned: the tools it asked for (name, arguments), or plain text."""
    function_calls: list = field(default_factory=list)
    text: str = ''


class GeminiSession:
    """One question's conversation with the model: the question, its tool requests, our tool
    results, and finally the written answer."""

    def __init__(self, client, model: str, system: str, definitions: list, types, key: str):
        self._client, self._model, self._types, self._key = client, model, types, key
        self._system = system
        self._contents = []
        declarations = [types.FunctionDeclaration(name=d['name'], description=d['description'],
                                                  parameters_json_schema=d['parameters'])
                        for d in definitions]
        self._tools_config = types.GenerateContentConfig(
            system_instruction=system, temperature=0,
            tools=[types.Tool(function_declarations=declarations)],
            # The model only proposes calls; our code decides whether and how to run them.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))

    def _generate(self, config):
        try:
            return self._client.models.generate_content(model=self._model,
                                                        contents=self._contents, config=config)
        except LLMError:
            raise
        except Exception as exc:
            raise _as_llm_error(exc, self._key) from None

    def _turn(self, response) -> ModelTurn:
        content = response.candidates[0].content if response.candidates else None
        if content is None:
            raise LLMError('bad_response', 'Gemini returned an empty response.')
        self._contents.append(content)  # keep the model's own turn in the conversation
        calls = [(c.name, dict(c.args or {})) for c in (response.function_calls or [])]
        text = '' if calls else (response.text or '')
        return ModelTurn(function_calls=calls, text=text)

    def send(self, text: str) -> ModelTurn:
        types = self._types
        self._contents.append(types.Content(role='user', parts=[types.Part(text=text)]))
        return self._turn(self._generate(self._tools_config))

    def send_tool_results(self, results: list) -> ModelTurn:
        """Return our tool results (name, result dict) to the model, as the docs show."""
        types = self._types
        parts = [types.Part.from_function_response(name=name, response={'result': result})
                 for name, result in results]
        self._contents.append(types.Content(role='tool', parts=parts))
        return self._turn(self._generate(self._tools_config))

    def final_answer(self, instruction: str, schema: dict) -> dict:
        """Ask for the written answer as JSON in a fixed shape (no tools in this call)."""
        types = self._types
        self._contents.append(types.Content(role='user', parts=[types.Part(text=instruction)]))
        config = types.GenerateContentConfig(system_instruction=self._system, temperature=0,
                                             response_mime_type='application/json',
                                             response_json_schema=schema)
        response = self._generate(config)
        try:
            return json.loads(response.text)
        except (TypeError, ValueError):
            raise LLMError('bad_response', 'Gemini did not return valid JSON.') from None


class GeminiClient:
    """Creates one GeminiSession per question. `sdk_client` lets tests pass a stand-in for
    google-genai's Client, so no network call is ever made in tests."""

    def __init__(self, api_key: str | None, model: str | None = None, sdk_client=None):
        if not api_key:
            raise LLMError('missing_key', 'No Gemini API key is configured.')
        from google.genai import types  # imported here so the app runs without the package
        self.model = model or DEFAULT_MODEL
        self._key, self._types = api_key, types
        if sdk_client is None:
            from google import genai
            sdk_client = genai.Client(
                api_key=api_key, http_options=types.HttpOptions(timeout=TIMEOUT_SECONDS * 1000))
        self._client = sdk_client

    def start(self, system: str, definitions: list) -> GeminiSession:
        return GeminiSession(self._client, self.model, system, definitions, self._types,
                             self._key)
