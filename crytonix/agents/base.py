from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
import json
import os
import re
from crytonix.llm.client import LLMClient
from crytonix.tools import (Toolbox, GitHubToolbox, WebToolbox, ProductToolbox, DesignToolbox,
                             CodeAnalysisToolbox, TestingToolbox, DatabaseToolbox, DevOpsToolbox,
                             DocumentationToolbox, SecurityToolbox, MemoryToolbox, AssetToolbox, ScaffoldToolbox,
                             HealthToolbox, NetworkToolbox, ArchiveToolbox, CryptoToolbox)
from crytonix.llm.token_tracker import TokenTracker

class BaseAgent(ABC):
    def __init__(self, name: str, client: LLMClient):
        self.name = name
        self.client = client
        self.history: List[Dict[str, Any]] = []
        self.tracker = TokenTracker()
        self.MAX_HISTORY_TOKENS = 30000 # Conservative limit for most models

    def load_history(self, filepath: str):
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                self.history = json.load(f)

    def save_history(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.history, f, indent=2)

    def add_context_files(self, file_paths: List[str]):
        context_str = "Project Context Files:\n"
        for path in file_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        context_str += f"\n--- {path} ---\n{f.read()}\n"
                except Exception as e:
                    context_str += f"\n--- {path} (Error reading file: {e}) ---\n"
        
        self.history.append({"role": "user", "content": f"Context for upcoming task:\n{context_str}"})

    def execute_tools(self, response: str) -> str:
        """
        Parses tool calls from the response.
        Supports:
        1. JSON blocks: ```json [{"tool": "name", "args": {...}}] ```
        2. XML blocks (Legacy): <file path="...">...</file>
        """
        tool_output = []
        executed_any = False

        # 1. JSON Parsing
        # Find all json blocks
        json_matches = re.finditer(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        for match in json_matches:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict):
                    data = [data] # Normalize to list
                
                if isinstance(data, list):
                    for tool_call in data:
                        # Handle CoT "thought" field
                        if "thought" in tool_call:
                             tool_output.append(f"Thought: {tool_call['thought']}")

                        tool_name = tool_call.get("tool")
                        args = tool_call.get("args", {})
                        
                        if tool_name:
                            # Map tool names to Toolbox methods
                            toolboxes = [
                                Toolbox, GitHubToolbox, WebToolbox, ProductToolbox, DesignToolbox,
                                CodeAnalysisToolbox, TestingToolbox, DatabaseToolbox, DevOpsToolbox,
                                DocumentationToolbox, SecurityToolbox, MemoryToolbox, AssetToolbox, ScaffoldToolbox,
                                HealthToolbox, NetworkToolbox, ArchiveToolbox, CryptoToolbox
                            ]
                            
                            found = False
                            for tb in toolboxes:
                                if hasattr(tb, tool_name):
                                    method = getattr(tb, tool_name)
                                    try:
                                        # Call the method with unpacked arguments
                                        result = method(**args) if isinstance(args, dict) else method(args)

                                        # Nice display name
                                        tb_name = tb.__name__.replace("Toolbox", "")
                                        if tb_name == "Toolbox": tb_name = "Tool"
                                        else: tb_name += " Tool"

                                        tool_output.append(f"{tb_name} '{tool_name}' output:\n{result}")
                                        executed_any = True
                                        found = True
                                        break
                                    except Exception as e:
                                        tool_output.append(f"Error executing '{tool_name}': {e}")
                                        found = True
                                        break
                            
                            if not found:
                                tool_output.append(f"Error: Tool '{tool_name}' not found.")
            except json.JSONDecodeError:
                pass # Not valid JSON, maybe just code snippet

        # 2. Legacy XML Parsing (Backwards Compatibility)
        if not executed_any:
            matches_xml = re.finditer(r'<file path="(.*?)">(.*?)</file>', response, re.DOTALL)
            for match in matches_xml:
                path = match.group(1).strip()
                content = match.group(2).strip()
                res = Toolbox.write_file(path, content)
                tool_output.append(f"System: {res}")

        return "\n\n".join(tool_output)

    def _manage_context(self):
        """Prunes history if it exceeds the token limit (Sliding Window)."""
        # Estimate total tokens
        total_text = json.dumps(self.history)
        current_tokens = self.tracker.estimate_tokens(total_text)
        
        if current_tokens > self.MAX_HISTORY_TOKENS:
            # Prune loop: Remove oldest messages (skipping System if present, but here System is separate)
            # We assume self.history contains [User, Assistant, User, Assistant...]
            # We keep the last 10 messages + any context manually added?
            # Simple strategy: Slice to keep last N messages.
            
            # Keep the first message if it's context? No, Context is usually added as User msg.
            # Let's just keep the last 20 messages for safety.
            overhead = len(self.history) - 20
            if overhead > 0:
                self.history = self.history[overhead:]
                # Verify we didn't break a User/Assistant pair? Not strictly critical for API but good practice.
            
    def _track_message(self, role: str, content: str):
        # We track incrementally, but cost calculation usually needs request/response pairs.
        # Here we just accumulate stats.
        pass # The tracker works on request/response basis usually. We'll track in chat_stream.

    def _add_user_message(self, content: Union[str, List[Dict[str, Any]]]):
        self.history.append({"role": "user", "content": content})

    def _add_assistant_message(self, content: str):
        self.history.append({"role": "assistant", "content": content})

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    def chat(self, user_input: Union[str, List[Dict[str, Any]]]) -> str:
        self._add_user_message(user_input)
        response = self.client.chat_completion(self.history, self.system_prompt)
        self._add_assistant_message(response)
        return response

    def chat_stream(self, user_input: Union[str, List[Dict[str, Any]]]):
        """Yields chunks of the response."""
        self._add_user_message(user_input)
        
        full_response = ""
        
        self._manage_context()
        stream = self.client.chat_completion(self.history, self.system_prompt, stream=True)
        
        try:
            for chunk in stream:
                if chunk:
                    full_response += chunk
                    yield chunk
            
            self.tracker.track_request(
                input_text=json.dumps(self.history), 
                output_text=full_response, 
                model_name=self.client.model or "default"
            )
            self._add_assistant_message(full_response)
        except Exception as e:
            # If stream fails, try to capture what we have
             if full_response:
                 self._add_assistant_message(full_response)
             raise e

