import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from product_agent_cli.main import main, AGENT_INSTRUCTIONS_CONTENT

@patch('product_agent_cli.main.genai.GenerativeModel')
@patch('product_agent_cli.main.load_dotenv')
@patch('product_agent_cli.main.os.getenv')
@patch('product_agent_cli.main.sys.argv', ['plan', 'test feature'])
def test_main_success(mock_getenv, mock_load_dotenv, mock_generative_model):
    """Tests the main function under ideal conditions."""
    mock_console = MagicMock()
    mock_console.input.return_value = 'done'
    mock_getenv.return_value = 'fake_api_key'

    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = [
        MagicMock(text='test_feature_name'),
        MagicMock(text='# Test Plan'),
        MagicMock(text='# Test Spec')
    ]
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = MagicMock(text="Agent response")
    mock_model_instance.start_chat.return_value = mock_chat
    mock_generative_model.return_value = mock_model_instance

    m = mock_open()
    with patch('builtins.open', m):
        with patch('os.path.exists', return_value=False):
            main(console=mock_console)

    mock_load_dotenv.assert_called_once()
    mock_getenv.assert_called_with("GOOGLE_API_KEY")
    mock_generative_model.assert_called_with('gemini-1.0-pro')
    mock_console.input.assert_called_once()
    assert m.call_count == 3

@patch('product_agent_cli.main.load_dotenv')
@patch('product_agent_cli.main.os.getenv')
@patch('product_agent_cli.main.sys.argv', ['plan', 'test feature'])
def test_main_no_api_key(mock_getenv, mock_load_dotenv):
    """Tests that the script exits if the API key is not found."""
    mock_console = MagicMock()
    mock_getenv.return_value = None

    with pytest.raises(SystemExit) as e:
        main(console=mock_console)
    
    assert e.type == SystemExit
    assert e.value.code == 1
    mock_console.print.assert_any_call("[bold red]Error:[/bold red] `GOOGLE_API_KEY` not found.")

@patch('product_agent_cli.main.load_dotenv')
@patch('product_agent_cli.main.os.getenv')
@patch('product_agent_cli.main.sys.argv', ['plan'])
def test_main_no_feature_idea(mock_getenv, mock_load_dotenv):
    """Tests that the script exits if no feature idea is provided."""
    mock_console = MagicMock()
    mock_getenv.return_value = 'fake_api_key'

    with pytest.raises(SystemExit) as e:
        main(console=mock_console)

    assert e.type == SystemExit
    assert e.value.code == 1
    mock_console.print.assert_any_call("[bold red]Error:[/bold red] Please provide an initial feature idea.")
