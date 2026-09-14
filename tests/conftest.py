import os
import pytest

@pytest.fixture
def base_url():
    return os.environ.get("DOUBAO_BASE_URL", "http://127.0.0.1:9090")
