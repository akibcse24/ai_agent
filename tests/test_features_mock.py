import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import base64
from crytonix.llm.client import LLMClient
from crytonix.agents.base import BaseAgent

class MockAgent(BaseAgent):
    @property
    def system_prompt(self):
        return "mock prompt"

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.client = LLMClient(provider="google")
        # Patch api key to avoid init error
        self.client.api_key = "fake_key"

    def test_image_encoding_local(self):
        # Create a dummy image file
        with open("test_img.txt", "wb") as f:
            f.write(b"fake_image_data")
        
        try:
            encoded = self.client._encode_image("test_img.txt")
            expected = base64.b64encode(b"fake_image_data").decode('utf-8')
            self.assertEqual(encoded, expected)
        finally:
            if os.path.exists("test_img.txt"):
                os.remove("test_img.txt")

    def test_image_encoding_url(self):
        url = "http://example.com/image.png"
        encoded = self.client._encode_image(url)
        self.assertEqual(encoded, url)

    def test_agent_context_loading(self):
        agent = MockAgent("TestAgent", self.client)
        
        # Create dummy context file
        with open("context.txt", "w") as f:
            f.write("Important Context")
            
        try:
            agent.add_context_files(["context.txt"])
            last_msg = agent.history[-1]
            self.assertEqual(last_msg["role"], "user")
            self.assertIn("Important Context", last_msg["content"])
            self.assertIn("context.txt", last_msg["content"])
        finally:
            if os.path.exists("context.txt"):
                os.remove("context.txt")

    @patch("builtins.open", new_callable=mock_open, read_data='{"GOOGLE_API_KEY": "stored_key"}')
    @patch("os.path.exists", return_value=True)
    def test_config_loading(self, mock_exists, mock_file):
        # We need to re-instantiate client to trigger config load
        # But we mocked path.exists to True for config file
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient(provider="google")
            self.assertEqual(client.api_key, "stored_key")

if __name__ == "__main__":
    unittest.main()
