class WebToolbox:
    @staticmethod
    def search_web(query: str, max_results: int = 5) -> str:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "Error: duckduckgo-search not installed."

        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}\n")
            return "\n---\n".join(results) if results else "No results found."
        except Exception as e:
            return f"Error searching web: {e}"

    @staticmethod
    def read_url(url: str) -> str:
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return "Error: requests/bs4 not installed."

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text[:5000] + "..." if len(text) > 5000 else text
        except Exception as e:
            return f"Error reading URL: {e}"
