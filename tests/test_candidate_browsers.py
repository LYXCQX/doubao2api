import os
import pytest
from doubao2api.browser_client import BrowserClient

def test_get_candidate_browsers_returns_non_empty_list():
    candidates = BrowserClient.get_candidate_browsers()
    assert isinstance(candidates, list)
    assert len(candidates) > 0
    for c in candidates:
        assert 'desc' in c

def test_get_candidate_browsers_includes_edge_and_chrome_on_windows():
    if os.name == 'nt':
        candidates = BrowserClient.get_candidate_browsers()
        channels_or_paths = [c.get('channel') for c in candidates if 'channel' in c]
        assert 'msedge' in channels_or_paths

def test_custom_env_override(monkeypatch):
    monkeypatch.setenv('DOUBAO_BROWSER_CHANNEL', 'custom-chrome')
    candidates = BrowserClient.get_candidate_browsers()
    assert candidates[0]['channel'] == 'custom-chrome'
    assert '自定义通道' in candidates[0]['desc']
