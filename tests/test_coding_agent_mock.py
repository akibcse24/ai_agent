import unittest
from unittest.mock import patch, MagicMock
import os
from crytonix.agents.coding import CodingAgent
from crytonix.llm.client import LLMClient

class TestCodingAgent(unittest.TestCase):
    def setUp(self):
        self.client = LLMClient(provider="google")
        self.client.api_key = "fake_key"
        self.agent = CodingAgent("TestCoder", self.client)

    def test_xml_parsing(self):
        response = """
Here is the code:
<file path="test_output.py">
print("Hello")
</file>

And another:
<file path="subdir/config.json">
{"key": "value"}
</file>
"""
        
        # We need to mock Toolbox.write_file to avoid actual FS writes
        with patch("crytonix.tools.Toolbox.write_file") as mock_write:
            mock_write.return_value = "Success"
            
            tool_output = self.agent.execute_tools(response)
            
            self.assertEqual(mock_write.call_count, 2)
            
            # Verify calls
            calls = mock_write.call_args_list
            self.assertEqual(calls[0][0][0], "test_output.py")
            self.assertEqual(calls[1][0][0], "subdir/config.json")
            
            self.assertIn("System: Success", tool_output)

if __name__ == "__main__":
    unittest.main()
