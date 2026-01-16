import unittest
from unittest.mock import patch, MagicMock
from crytonix.agents.manager import ManagerAgent
from crytonix.llm.client import LLMClient
import re

class TestManagerAgent(unittest.TestCase):
    def setUp(self):
        self.client = LLMClient(provider="google")
        self.client.api_key = "fake_key"
        self.agent = ManagerAgent("TestManager", self.client)

    def test_delegation_regex(self):
        response = "[CALL: Planner] Please analyze this."
        match = re.search(r"\[CALL: (\w+)\](.*)", response, re.DOTALL)
        self.assertTrue(match)
        self.assertEqual(match.group(1), "Planner")
        self.assertEqual(match.group(2).strip(), "Please analyze this.")

    def test_delegation_coder(self):
        response = "[CALL: Coder] Write the code."
        match = re.search(r"\[CALL: (\w+)\](.*)", response, re.DOTALL)
        self.assertTrue(match)
        self.assertEqual(match.group(1), "Coder")

if __name__ == "__main__":
    unittest.main()
