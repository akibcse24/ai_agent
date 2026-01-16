import unittest
from unittest.mock import patch, MagicMock
import os
import json
from crytonix.llm.client import LLMClient

class TestLLMClient(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            "GOOGLE_API_KEY": "fake_google_key",
            "GROQ_API_KEY": "fake_groq_key",
            "OPENROUTER_API_KEY": "fake_router_key"
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch("requests.post")
    def test_google_client(self, mock_post):
        # Mock Google Response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Hello from Google"}]}}]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = LLMClient(provider="google")
        response = client.chat_completion([{"role": "user", "content": "Hi"}])
        
        self.assertEqual(response, "Hello from Google")
        self.assertTrue(mock_post.called)
        # Check URL contains key
        self.assertIn("key=fake_google_key", mock_post.call_args[0][0])

    @patch("requests.post")
    def test_groq_client(self, mock_post):
        # Mock Groq Response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello from Groq"}}]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = LLMClient(provider="groq")
        response = client.chat_completion([{"role": "user", "content": "Hi"}])
        
        self.assertEqual(response, "Hello from Groq")
        self.assertTrue(mock_post.called)
        # Check Headers contain Auth
        headers = mock_post.call_args[1]["headers"]
        self.assertEqual(headers["Authorization"], "Bearer fake_groq_key")

    @patch("requests.post")
    def test_openrouter_client(self, mock_post):
        # Mock OpenRouter Response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello from OpenRouter"}}]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = LLMClient(provider="openrouter")
        response = client.chat_completion([{"role": "user", "content": "Hi"}])
        
        self.assertEqual(response, "Hello from OpenRouter")
        self.assertTrue(mock_post.called)
        # Check specific headers
        headers = mock_post.call_args[1]["headers"]
        self.assertEqual(headers["Authorization"], "Bearer fake_router_key")
        self.assertIn("HTTP-Referer", headers)

if __name__ == "__main__":
    unittest.main()
