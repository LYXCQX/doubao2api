"""
Unit tests for doubao2api (fast, no browser or live network required).
"""
import os
import pytest
from doubao2api.browser_client import resolve_headless_mode
from doubao2api.unified_server import is_safe_url
from doubao2api.tool_calling import (
    convert_messages_with_tools,
    parse_tool_calls_xml,
    is_tool_call_start,
    has_complete_tool_calls,
)
from doubao2api.token_counter import count_messages_tokens


@pytest.mark.unit
def test_resolve_headless_mode():
    # Explicit true
    assert resolve_headless_mode("true") is True
    assert resolve_headless_mode("1") is True
    assert resolve_headless_mode(True) is True

    # Windows behavior
    if os.name == "nt":
        assert resolve_headless_mode("false") is False
        assert resolve_headless_mode(False) is False
        assert resolve_headless_mode("auto") is False
        assert resolve_headless_mode(None) is False


@pytest.mark.unit
def test_ssrf_is_safe_url():
    # Dangerous URLs must be blocked
    assert is_safe_url("http://127.0.0.1:9090") is False
    assert is_safe_url("http://127.0.0.1") is False
    assert is_safe_url("http://localhost:9090") is False
    assert is_safe_url("http://localhost") is False
    assert is_safe_url("http://0.0.0.0:80") is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_safe_url("http://10.0.0.1/test") is False
    assert is_safe_url("http://192.168.1.1/admin") is False
    assert is_safe_url("http://172.16.0.1") is False
    assert is_safe_url("ftp://example.com/file") is False
    assert is_safe_url("file:///etc/passwd") is False

    # Safe external URLs
    assert is_safe_url("https://www.doubao.com") is True
    assert is_safe_url("https://www.google.com") is True


@pytest.mark.unit
def test_tool_calling_xml_parser():
    xml = '<tool_call>{"name": "get_weather", "arguments": {"city": "Beijing"}}</tool_call>'
    parsed = parse_tool_calls_xml(xml)
    assert parsed is not None
    assert len(parsed) == 1
    assert parsed[0]["function"]["name"] == "get_weather"
    assert "Beijing" in parsed[0]["function"]["arguments"]

    assert is_tool_call_start('<tool_call>') is True
    assert has_complete_tool_calls(xml) is True


@pytest.mark.unit
def test_token_counter():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello world!"},
    ]
    tokens = count_messages_tokens(messages)
    assert tokens > 0
