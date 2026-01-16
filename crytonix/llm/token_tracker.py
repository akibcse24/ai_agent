import math

class TokenTracker:
    # Approximate pricing per 1M tokens (Input, Output) as of late 2024
    # Prices are estimates and varies by provider/model
    PRICING = {
        "gemini-1.5-flash": (0.075, 0.30),
        "gemini-1.5-pro": (3.50, 10.50),
        "llama-3.1-70b-versatile": (0.70, 0.90), # Groq pricing approx
        "anthropic/claude-3.5-sonnet": (3.00, 15.00),
        "default": (1.00, 3.00)
    }

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def estimate_tokens(self, text: str) -> int:
        """
        Approximate token count.
        Rule of thumb: 1 token ~= 4 characters for English text.
        """
        if not text:
            return 0
        return math.ceil(len(text) / 4)

    def track_request(self, input_text: str, output_text: str, model_name: str):
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        cost_in, cost_out = self.PRICING.get(model_name, self.PRICING["default"])
        
        # Calculate cost (price per 1M tokens)
        req_cost = (input_tokens / 1_000_000 * cost_in) + (output_tokens / 1_000_000 * cost_out)
        self.total_cost += req_cost

    def get_summary(self) -> str:
        return f"Tokens: {self.total_input_tokens + self.total_output_tokens} (In: {self.total_input_tokens}, Out: {self.total_output_tokens}) | Est. Cost: ${self.total_cost:.4f}"
