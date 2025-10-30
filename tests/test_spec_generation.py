import pytest
from unittest.mock import patch, mock_open, MagicMock, call
import os
# FIX: Adjusted import path to match your project structure
from product_agent_cli.main import main, AGENT_INSTRUCTIONS_CONTENT

@patch('product_agent_cli.main.genai.GenerativeModel')
@patch('product_agent_cli.main.load_dotenv')
@patch('product_agent_cli.main.os.getenv')
@patch('product_agent_cli.main.sys.argv', ['plan', 'test feature'])
# FIX: The incorrect patch for 'builtins.input' has been REMOVED from here.
def test_spec_md_generation(mock_getenv, mock_load_dotenv, mock_generative_model):
    """Tests that the .spec.md file is generated correctly."""
    # --- Setup Mocks ---

    # Create a mock console object
    mock_console_instance = MagicMock()
    # FIX: Configure the 'input' method ON THE MOCK CONSOLE to simulate the user typing 'done'
    mock_console_instance.input.return_value = 'done'

    # Mock API key to be returned by os.getenv
    mock_getenv.return_value = 'fake_api_key'

    # Mock the sequence of responses from the generative model
    mock_generative_model.return_value.generate_content.side_effect = [
        # 1. Response for generate_feature_name
        MagicMock(text='test_feature_name'),
        # 2. Response for the plan synthesis
        MagicMock(text='# Test Plan'),
        # 3. Response for the spec synthesis
        MagicMock(text='# Test Spec\n## Requirements\n* REQ-001: Test requirement')
    ]

    # We also need to mock the chat object and its send_message method
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = MagicMock(text="Mocked agent response.")
    mock_generative_model.return_value.start_chat.return_value = mock_chat

    # --- Run the Test ---
    m = mock_open()
    with patch('builtins.open', m):
        # Mock os.path.exists to simulate AGENT_INSTRUCTIONS.md not existing
        with patch('os.path.exists', return_value=False):
            # Pass our fully configured mock console to the main function
            main(console=mock_console_instance)

    # --- Assert Results ---

    # Assert that the correct files were opened for writing
    expected_open_calls = [
        call('test_feature_name.plan.md', 'w'),
        call('test_feature_name.spec.md', 'w'),
        call('AGENT_INSTRUCTIONS.md', 'w')
    ]
    m.assert_has_calls(expected_open_calls, any_order=True)

    # Assert that the correct content was written to the files
    expected_write_calls = [
        call('# Test Plan'),
        call('# Test Spec\n## Requirements\n* REQ-001: Test requirement'),
        call(AGENT_INSTRUCTIONS_CONTENT)
    ]
    m.return_value.write.assert_has_calls(expected_write_calls, any_order=True)

    # Assert that our mock console was used to print and get input
    mock_console_instance.print.assert_called()
    mock_console_instance.input.assert_called_once()