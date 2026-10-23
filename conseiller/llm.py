"""LLM provider abstraction for DÉTOUR.

Defines a common interface for chat-completion LLM providers. Two
implementations are provided:

- OpenRouterProvider: calls the OpenRouter API (OpenAI-compatible format).
  This is the original provider, extracted from Agent._call_model.

- AnthropicProvider: calls the Anthropic Messages API. Converts between
  the OpenAI message/tool format used by the agent and the Anthropic format.

Both implementations use only the Python standard library (urllib.request).
"""

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path


class LLMError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def _ssl_context():
    ctx = ssl.create_default_context()
    for path in (
        os.environ.get("SSL_CERT_FILE"),
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
    ):
        if path and Path(path).exists():
            try:
                ctx.load_verify_locations(path)
            except (OSError, ssl.SSLError):
                pass
    return ctx


class LLMProvider:
    """Common interface for an LLM provider."""

    def chat(self, messages, tools=None):
        """Send a conversation and return the model response.

        Returns a dict {"content": str | None, "tool_calls": list}.
        Raises LLMError on failure.
        """
        raise NotImplementedError


class OpenRouterProvider(LLMProvider):
    """Calls the OpenRouter API (OpenAI-compatible format)."""

    def __init__(self, api_key="", model="", base_url="", timeout=60):
        self._api_key = api_key
        self.model = model
        self._base_url = base_url
        self.timeout = timeout

    def chat(self, messages, tools=None):
        payload = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        request = urllib.request.Request(
            self._base_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self._api_key}",
                     "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(
                    request, timeout=self.timeout,
                    context=_ssl_context()) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as err:
            detail = f"HTTP {err.code}"
            try:
                detail = json.loads(err.read()).get("error", {}).get("message", detail)
            except Exception:
                pass
            if err.code in (401, 403):
                raise LLMError(
                    "OpenRouter rejected the API key (check OPENROUTER_API_KEY).",
                    err.code) from err
            if err.code == 429:
                raise LLMError(
                    "OpenRouter rate limit reached, try again in a moment.",
                    err.code) from err
            raise LLMError(f"OpenRouter: {detail}", err.code) from err
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            raise LLMError("OpenRouter unreachable, check your connection.") from err
        except json.JSONDecodeError as err:
            raise LLMError("Unreadable response from OpenRouter.") from err
        try:
            return data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as err:
            raise LLMError(
                "OpenRouter: response without a usable message.") from err


class AnthropicProvider(LLMProvider):
    """Calls the Anthropic Messages API.

    Converts between the OpenAI format (used by the agent) and the
    Anthropic Messages API format.
    """

    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(self, api_key="", model="", base_url="", timeout=60):
        self._api_key = api_key
        self.model = model
        self._base_url = base_url or "https://api.anthropic.com/v1/messages"
        self.timeout = timeout

    def _convert_messages(self, messages):
        """Convert OpenAI messages to Anthropic format.

        Anthropic uses a separate `system` parameter and does not support
        the "system" role in the message list. "tool" messages (tool
        results) become tool_result blocks inside a user message.
        """
        system_parts = []
        converted = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "system":
                if isinstance(content, str):
                    system_parts.append(content)
                continue
            if role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                tool_content = content if isinstance(content, str) else json.dumps(content)
                converted.append({
                    "role": "user",
                    "content": [{"type": "tool_result",
                                 "tool_use_id": tool_call_id,
                                 "content": tool_content}],
                })
                continue
            if role == "assistant":
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    blocks = []
                    if content:
                        blocks.append({"type": "text", "text": content})
                    for tc in tool_calls:
                        fn = tc.get("function") or {}
                        args = fn.get("arguments", "{}")
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                args = {}
                        blocks.append({
                            "type": "tool_use",
                            "id": tc.get("id", ""),
                            "name": fn.get("name", ""),
                            "input": args,
                        })
                    converted.append({"role": "assistant", "content": blocks})
                else:
                    converted.append({
                        "role": "assistant",
                        "content": content or "",
                    })
                continue
            converted.append({"role": role, "content": content or ""})
        return "\n\n".join(system_parts), converted

    def _convert_tools(self, tools):
        """Convert OpenAI tools to Anthropic format."""
        if not tools:
            return None
        anthropic_tools = []
        for tool in tools:
            fn = tool.get("function") or {}
            params = fn.get("parameters") or {"type": "object", "properties": {}}
            anthropic_tools.append({
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "input_schema": params,
            })
        return anthropic_tools

    def _parse_response(self, data):
        """Parse the Anthropic response into OpenAI message format."""
        content_blocks = data.get("content") or []
        text_parts = []
        tool_calls = []
        for block in content_blocks:
            btype = block.get("type")
            if btype == "text":
                text_parts.append(block.get("text", ""))
            elif btype == "tool_use":
                tool_calls.append({
                    "id": block.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": block.get("name", ""),
                        "arguments": json.dumps(block.get("input") or {}),
                    },
                })
        return {
            "content": "\n".join(text_parts) if text_parts else None,
            "tool_calls": tool_calls,
        }

    def chat(self, messages, tools=None):
        system, converted_messages = self._convert_messages(messages)
        anthropic_tools = self._convert_tools(tools)
        payload = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": 4096,
        }
        if system:
            payload["system"] = system
        if anthropic_tools:
            payload["tools"] = anthropic_tools
            payload["tool_choice"] = {"type": "auto"}
        request = urllib.request.Request(
            self._base_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"x-api-key": self._api_key,
                     "anthropic-version": self.ANTHROPIC_VERSION,
                     "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(
                    request, timeout=self.timeout,
                    context=_ssl_context()) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as err:
            detail = f"HTTP {err.code}"
            try:
                err_body = json.loads(err.read())
                detail = err_body.get("error", {}).get("message", detail)
            except Exception:
                pass
            if err.code in (401, 403):
                raise LLMError(
                    "Anthropic rejected the API key (check ANTHROPIC_API_KEY).",
                    err.code) from err
            if err.code == 429:
                raise LLMError(
                    "Anthropic rate limit reached, try again in a moment.",
                    err.code) from err
            raise LLMError(f"Anthropic: {detail}", err.code) from err
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            raise LLMError("Anthropic unreachable, check your connection.") from err
        except json.JSONDecodeError as err:
            raise LLMError("Unreadable response from Anthropic.") from err
        return self._parse_response(data)