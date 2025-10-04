import pytest
import json
from unittest.mock import patch, MagicMock
from agent.memory import MemoryStore, save_session, load_session  # Assuming functions
from agent.models import Session

def test_memory_persistence_saves_and_loads():
    """Integration test: Memory saves session to JSON and loads it back."""
    session = Session(history=["test input"], current_task="test task", loaded_tools=[])
    with patch('json.dump') as mock_dump, patch('pathlib.Path.open') as mock_open_save:
        mock_file_save = MagicMock()
        mock_open_save.return_value.__enter__.return_value = mock_file_save
        save_session(session, "test_session_id")  # Fails until impl
        mock_dump.assert_called_once()
        expected_data = {"history": ["test input"], "current_task": "test task", "loaded_tools": []}
        mock_dump.assert_called_with(expected_data, mock_file_save)
    
    with patch('json.load') as mock_load, patch('pathlib.Path.open') as mock_open_load:
        mock_file_load = MagicMock()
        mock_open_load.return_value.__enter__.return_value = mock_file_load
        mock_load.return_value = expected_data
        loaded = load_session("test_session_id")  # Fails until impl
        assert loaded.history == ["test input"]
        assert loaded.current_task == "test task"
        mock_load.assert_called()
