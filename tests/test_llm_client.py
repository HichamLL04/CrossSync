import pytest
from unittest.mock import patch, MagicMock
from src.llm_client import LLMClient

@patch('src.llm_client.requests.post')
def test_split_line_ollama(mock_post):
    # Mock Ollama JSON response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": '["Parte uno de prueba", "Parte dos de prueba"]'
        }
    }
    mock_post.return_value = mock_response

    client = LLMClient(provider="ollama", model="qwen2.5:7b", url="http://localhost:11434")
    result = client.split_line(
        text="Parte uno de prueba Parte dos de prueba",
        num_parts=2,
        references=["Parte 1 ref", "Parte 2 ref"]
    )
    assert result == ["Parte uno de prueba", "Parte dos de prueba"]

@patch('src.llm_client.requests.post')
def test_filter_join_ollama(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": '{"indices_validos": [0]}'
        }
    }
    mock_post.return_value = mock_response

    client = LLMClient(provider="ollama", model="qwen2.5:7b", url="http://localhost:11434")
    result = client.filter_join(
        texts_a=["Y así nos conocimos.", "Entrada gratuita"],
        reference_b="And so we met."
    )
    assert result == ["Y así nos conocimos."]
