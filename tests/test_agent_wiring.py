import unittest
from crytonix.agents.base import BaseAgent
from crytonix.llm.client import LLMClient
import json

class MockAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return "mock"

class TestAgentWiring(unittest.TestCase):
    def setUp(self):
        # We don't need a real LLM client for this, we just test execute_tools
        self.client = type('MockClient', (), {'model': 'test'})()
        self.agent = MockAgent("TestAgent", self.client)

    def test_wiring(self):
        # Simulate an LLM response asking for the new tools
        response = """
        I will now check the system info and zip some files.
        ```json
        [
            {"tool": "get_system_info", "args": {}},
            {"tool": "open_app", "args": {"app_name": "calculator"}}
        ]
        ```
        """
        output = self.agent.execute_tools(response)

        self.assertIn("System Tool 'get_system_info' output", output)
        self.assertIn("Desktop Tool 'open_app' output", output)

        # Verify FileToolbox
        response_file = """
        ```json
        [{"tool": "read_csv", "args": {"path": "nonexistent.csv"}}]
        ```
        """
        output_file = self.agent.execute_tools(response_file)
        self.assertIn("File Tool 'read_csv' output", output_file)
        # It should return an error from the tool itself, but routed correctly
        self.assertIn("Error reading CSV", output_file)

if __name__ == "__main__":
    unittest.main()
