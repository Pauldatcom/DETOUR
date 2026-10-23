#!/usr/bin/env python3
"""Tests for the LLM provider abstraction (ticket #196).

Covers OpenRouterProvider and AnthropicProvider: request format,
response parsing, tool-call conversion, and error mapping.
"""

import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from llm import AnthropicProvider, LLMError, LLMProvider, OpenRouterProvider


def free_port():
    sock = __import__("socket").socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class FakeLLMServer:
    """Minimal HTTP server that captures requests and returns scripted responses."""

    def __init__(self, handler_fn):
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                req = {
                    "headers": dict(self.headers),
                    "body": json.loads(body) if body else {},
                }
                outer.requests.append(req)
                status, payload = handler_fn(req)
                data = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args, **kwargs):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


class TestLLMProviderInterface(unittest.TestCase):

    def test_base_raises_not_implemented(self):
        provider = LLMProvider()
        with self.assertRaises(NotImplementedError):
            provider.chat([{"role": "user", "content": "hi"}])


class TestOpenRouterProvider(unittest.TestCase):

    def setUp(self):
        def handler(req):
            return 200, {"choices": [{"message": {
                "content": "Bonjour", "tool_calls": []}}]}
        self.server = FakeLLMServer(handler)
        self.addCleanup(self.server.stop)
        self.provider = OpenRouterProvider(
            api_key="sk-test", model="m", base_url=self.server.url, timeout=5)

    def test_chat_returns_message(self):
        result = self.provider.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(result["content"], "Bonjour")
        self.assertEqual(result["tool_calls"], [])

    def test_request_has_authorization_header(self):
        self.provider.chat([{"role": "user", "content": "hi"}])
        headers = {k.lower(): v for k, v in
                   self.server.requests[0]["headers"].items()}
        self.assertEqual(headers.get("authorization"), "Bearer sk-test")

    def test_request_has_model_and_messages(self):
        self.provider.chat([{"role": "user", "content": "hi"}])
        body = self.server.requests[0]["body"]
        self.assertEqual(body["model"], "m")
        self.assertEqual(body["messages"][0]["content"], "hi")

    def test_tools_included_when_provided(self):
        tools = [{"type": "function", "function": {
            "name": "f", "description": "d",
            "parameters": {"type": "object", "properties": {}}}}]
        self.provider.chat([{"role": "user", "content": "hi"}], tools=tools)
        body = self.server.requests[0]["body"]
        self.assertEqual(body["tools"], tools)
        self.assertEqual(body["tool_choice"], "auto")

    def test_tools_omitted_when_none(self):
        self.provider.chat([{"role": "user", "content": "hi"}])
        body = self.server.requests[0]["body"]
        self.assertNotIn("tools", body)

    def test_tool_calls_parsed(self):
        def handler(req):
            return 200, {"choices": [{"message": {
                "content": None,
                "tool_calls": [{"id": "c1", "type": "function",
                                "function": {"name": "f", "arguments": '{"x": 1}'}}]}}]}
        server = FakeLLMServer(handler)
        self.addCleanup(server.stop)
        provider = OpenRouterProvider(
            api_key="k", model="m", base_url=server.url, timeout=5)
        result = provider.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(len(result["tool_calls"]), 1)
        self.assertEqual(result["tool_calls"][0]["function"]["name"], "f")

    def test_http_error_401(self):
        def handler(req):
            return 401, {"error": {"message": "invalid key"}}
        server = FakeLLMServer(handler)
        self.addCleanup(server.stop)
        provider = OpenRouterProvider(
            api_key="bad", model="m", base_url=server.url, timeout=5)
        with self.assertRaises(LLMError) as ctx:
            provider.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(ctx.exception.status, 401)

    def test_http_error_429(self):
        def handler(req):
            return 429, {"error": {"message": "rate limited"}}
        server = FakeLLMServer(handler)
        self.addCleanup(server.stop)
        provider = OpenRouterProvider(
            api_key="k", model="m", base_url=server.url, timeout=5)
        with self.assertRaises(LLMError) as ctx:
            provider.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(ctx.exception.status, 429)

    def test_connection_error(self):
        provider = OpenRouterProvider(
            api_key="k", model="m",
            base_url=f"http://127.0.0.1:{free_port()}/x", timeout=1)
        with self.assertRaises(LLMError):
            provider.chat([{"role": "user", "content": "hi"}])


class TestAnthropicProvider(unittest.TestCase):

    def setUp(self):
        def handler(req):
            return 200, {"content": [{"type": "text", "text": "Bonjour"}]}
        self.server = FakeLLMServer(handler)
        self.addCleanup(self.server.stop)
        self.provider = AnthropicProvider(
            api_key="sk-ant", model="claude", base_url=self.server.url, timeout=5)

    def test_chat_returns_content(self):
        result = self.provider.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(result["content"], "Bonjour")
        self.assertEqual(result["tool_calls"], [])

    def test_request_has_anthropic_headers(self):
        self.provider.chat([{"role": "user", "content": "hi"}])
        headers = {k.lower(): v for k, v in
                   self.server.requests[0]["headers"].items()}
        self.assertEqual(headers.get("x-api-key"), "sk-ant")
        self.assertIn("anthropic-version", headers)

    def test_system_extracted_from_messages(self):
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "hi"},
        ]
        self.provider.chat(messages)
        body = self.server.requests[0]["body"]
        self.assertEqual(body["system"], "You are helpful")
        roles = [m["role"] for m in body["messages"]]
        self.assertNotIn("system", roles)
        self.assertEqual(roles, ["user"])

    def test_multiple_system_messages_merged(self):
        messages = [
            {"role": "system", "content": "Rule 1"},
            {"role": "system", "content": "Rule 2"},
            {"role": "user", "content": "hi"},
        ]
        self.provider.chat(messages)
        body = self.server.requests[0]["body"]
        self.assertEqual(body["system"], "Rule 1\n\nRule 2")

    def test_tools_converted_to_anthropic_format(self):
        tools = [{"type": "function", "function": {
            "name": "search", "description": "Search trips",
            "parameters": {"type": "object",
                           "properties": {"dest": {"type": "string"}}}}}]
        self.provider.chat([{"role": "user", "content": "hi"}], tools=tools)
        body = self.server.requests[0]["body"]
        self.assertEqual(len(body["tools"]), 1)
        self.assertEqual(body["tools"][0]["name"], "search")
        self.assertEqual(body["tools"][0]["input_schema"]["properties"]["dest"]["type"], "string")

    def test_tool_use_response_parsed(self):
        def handler(req):
            return 200, {"content": [
                {"type": "tool_use", "id": "tu_1", "name": "search",
                 "input": {"dest": "Lyon"}},
                {"type": "text", "text": "Voici les résultats"},
            ]}
        server = FakeLLMServer(handler)
        self.addCleanup(server.stop)
        provider = AnthropicProvider(
            api_key="k", model="m", base_url=server.url, timeout=5)
        result = provider.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(len(result["tool_calls"]), 1)
        self.assertEqual(result["tool_calls"][0]["id"], "tu_1")
        self.assertEqual(result["tool_calls"][0]["function"]["name"], "search")
        self.assertEqual(json.loads(result["tool_calls"][0]["function"]["arguments"]),
                         {"dest": "Lyon"})
        self.assertEqual(result["content"], "Voici les résultats")

    def test_tool_result_message_converted(self):
        messages = [
            {"role": "user", "content": "search Lyon"},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "tu_1", "type": "function",
                 "function": {"name": "search", "arguments": '{"dest": "Lyon"}'}}]},
            {"role": "tool", "tool_call_id": "tu_1", "content": '{"results": []}'},
            {"role": "user", "content": "thanks"},
        ]
        self.provider.chat(messages)
        body = self.server.requests[0]["body"]
        anthropic_msgs = body["messages"]
        self.assertEqual(anthropic_msgs[1]["role"], "assistant")
        self.assertEqual(anthropic_msgs[1]["content"][0]["type"], "tool_use")
        self.assertEqual(anthropic_msgs[1]["content"][0]["id"], "tu_1")
        self.assertEqual(anthropic_msgs[2]["role"], "user")
        self.assertEqual(anthropic_msgs[2]["content"][0]["type"], "tool_result")
        self.assertEqual(anthropic_msgs[2]["content"][0]["tool_use_id"], "tu_1")

    def test_max_tokens_in_payload(self):
        self.provider.chat([{"role": "user", "content": "hi"}])
        body = self.server.requests[0]["body"]
        self.assertIn("max_tokens", body)

    def test_http_error_401(self):
        def handler(req):
            return 401, {"error": {"message": "invalid key"}}
        server = FakeLLMServer(handler)
        self.addCleanup(server.stop)
        provider = AnthropicProvider(
            api_key="bad", model="m", base_url=server.url, timeout=5)
        with self.assertRaises(LLMError) as ctx:
            provider.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(ctx.exception.status, 401)

    def test_connection_error(self):
        provider = AnthropicProvider(
            api_key="k", model="m",
            base_url=f"http://127.0.0.1:{free_port()}/x", timeout=1)
        with self.assertRaises(LLMError):
            provider.chat([{"role": "user", "content": "hi"}])


class TestAgentWithProvider(unittest.TestCase):
    """Agent integrates with any LLMProvider via the provider parameter."""

    def setUp(self):
        from agent import Agent
        from propositions import PropositionStore
        from store import DemandStore
        from tests.test_conseiller import FakeSupplier
        self.store = DemandStore(None)
        self.supplier = FakeSupplier()
        self.Agent = Agent

    def test_agent_uses_provider(self):
        class StubProvider:
            model = "stub-model"
            def chat(self, messages, tools=None):
                return {"content": "Hello from stub", "tool_calls": []}
        agent = self.Agent(self.supplier, self.store, provider=StubProvider())
        result = agent.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(result["reply"], "Hello from stub")

    def test_agent_backward_compat_without_provider(self):
        agent = self.Agent(self.supplier, self.store, api_key="", model="m")
        self.assertIsInstance(agent._provider, OpenRouterProvider)


if __name__ == "__main__":
    unittest.main()