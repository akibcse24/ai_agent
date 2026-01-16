import os
import requests
import json
import base64
from typing import List, Dict, Optional, Any

class LLMClient:
    def __init__(self, provider: str = "google", model: str = None):
        self.provider = provider
        self.model = model
        self.api_key = self._get_api_key(provider)

    def _get_api_key(self, provider: str) -> str:
        key_map = {
            "google": "GOOGLE_API_KEY",
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY"
        }
        # Try finding key in config file first
        config_path = os.path.expanduser("~/.crytonix/config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    if key_map[provider] in config:
                         return config[key_map[provider]]
            except:
                pass
        
        # Fallback to env var
        env_var = key_map.get(provider)
        if not env_var:
            raise ValueError(f"Unknown provider: {provider}")
        
        return os.environ.get(env_var)

    def _encode_image(self, image_path: str) -> str:
        if image_path.startswith("http"):
            # For remote URLs, we just return the URL (logic handled in provider)
            return image_path
        
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def chat_completion(self, messages: List[Dict[str, Any]], system_instruction: str = None, stream: bool = False) -> Any:
        # If stream=True, returns a generator. Else returns string.
        
        if not self.api_key:
             raise ValueError(f"API key for {self.provider} not found. Set it in env vars or ~/.crytonix/config.json")

        if self.provider == "google":
            return self._call_google(messages, system_instruction, stream)
        elif self.provider == "groq":
            return self._call_openai_compatible(
                "https://api.groq.com/openai/v1/chat/completions", 
                messages, 
                system_instruction,
                default_model="llama-3.1-70b-versatile",
                stream=stream
            )
        elif self.provider == "openrouter":
            return self._call_openai_compatible(
                "https://openrouter.ai/api/v1/chat/completions", 
                messages, 
                system_instruction,
                default_model="anthropic/claude-3.5-sonnet",
                stream=stream
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_google(self, messages: List[Dict[str, Any]], system_instruction: str = None, stream: bool = False) -> Any:
        model = self.model or "gemini-1.5-flash"
        # Use streamGenerateContent if streaming
        method = "streamGenerateContent" if stream else "generateContent"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:{method}?key={self.api_key}"
        
        # ... (Content prep similar to before) ...
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            parts = []
            if isinstance(msg["content"], str):
                 parts.append({"text": msg["content"]})
            elif isinstance(msg["content"], list):
                for part in msg["content"]:
                    if part["type"] == "text": parts.append({"text": part["text"]})
                    # Image handling omitted for brevity in diff, assume text only for now or reuse logic
            contents.append({"role": role, "parts": parts})
            
        payload = {"contents": contents}
        if system_instruction:
            payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, headers=headers, json=payload, stream=stream)
            response.raise_for_status()
            
            if stream:
                return self._stream_google_response(response)
            else:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Error calling Google API: {e}"

    def _stream_google_response(self, response):
        # Google Streaming returns JSON objects in a list, but via requests stream it might come as valid JSON objects one by one or a big array
        # This is a naive implementation; production usually needs a better parser for SSE or JSON streams
        # But Google REST API returns a JSON array for streamGenerateContent.
        # Simple hack: accumulate text and yield difference? Or just yield raw if using SSE?
        # Actually Google REST returns '[' then objects then ']'.
        # For this CLI, let's keep it simple: If streaming is hard with requests, we fallback or just buffer. 
        # BUT let's try to yield lines.
        buffer = ""
        for chunk in response.iter_lines():
            if chunk:
                line = chunk.decode("utf-8")
                # Very basic parsing for Gemini stream format
                if '"text":' in line:
                    match = re.search(r'"text":\s*"(.*?)"', line)
                    if match:
                        text = match.group(1).encode('utf-8').decode('unicode_escape')
                        yield text
    
    def _call_openai_compatible(self, url: str, messages: List[Dict[str, Any]], system_instruction: str, default_model: str, stream: bool = False) -> Any:
        model = self.model or default_model
        final_messages = []
        if system_instruction:
            final_messages.append({"role": "system", "content": system_instruction})
        final_messages.extend(messages)
        
        payload = {
            "model": model,
            "messages": final_messages,
            "stream": stream
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://crytonix.local"

        try:
            response = requests.post(url, headers=headers, json=payload, stream=stream)
            response.raise_for_status()
            
            if stream:
                return self._stream_openai_response(response)
            else:
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {e}"

    def _stream_openai_response(self, response):
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    if decoded_line.strip() == 'data: [DONE]':
                        break
                    try:
                        data = json.loads(decoded_line[6:])
                        delta = data['choices'][0].get('delta', {})
                        if 'content' in delta:
                            yield delta['content']
                    except:
                        pass
