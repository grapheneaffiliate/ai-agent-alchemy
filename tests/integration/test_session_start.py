import pytest
from unittest.mock import patch, MagicMock
from agent.core import start_session  # Assuming function

@pytest.fixture
def mock_env():
    with patch('os.getenv') as mock_get:
        mock_get.side_effect = lambda k: {'OPENAI_API_KEY': 'test', 'OPENAI_BASE_URL': 'http://test', 'MODEL': 'grok'}[k]
        return mock_get

def test_session_start_loads_env(mock_env):
    """Integration test: Session start loads .env and initializes API client."""
    with patch('agent.api.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        session = start_session()  # Fails until impl
        assert session.api.base_url == 'http://test'
        mock_openai.assert_called_once_with(base_url='http://test', api_key='test')
