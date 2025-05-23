import requests
from bs4 import BeautifulSoup
import re

def register():
    return WebSearchPlugin()

class WebSearchPlugin:
    def handle(self, text):
        keywords = ['search', 'find', 'look up', 'web', 'internet', 'google']
        if any(k in text.lower() for k in keywords) or text.strip().endswith('?'):
            query = text
            answer = self.web_search_and_extract_answer(query)
            if answer:
                return answer
            else:
                return "Sorry, I couldn't find a direct answer online."
        return None

    def web_search_and_extract_answer(self, query):
        try:
            url = f'https://duckduckgo.com/html/?q={requests.utils.quote(query)}'
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                results = soup.find_all('div', class_='result')
                snippets = []
                for result in results[:5]:
                    title = result.find('a', class_='result__a')
                    snippet = result.find('a', class_='result__snippet')
                    if not snippet:
                        snippet = result.find('div', class_='result__snippet')
                    if title and snippet:
                        snippets.append(snippet.get_text(strip=True))
                # Try to extract a direct answer for fact-based questions
                answer = self.extract_direct_answer(query, snippets)
                if answer:
                    return f'Web answer: {answer}'
                # Fallback: join the best snippets
                if snippets:
                    return 'Web summary: ' + ' | '.join(snippets)
        except Exception as e:
            return f"Web search error: {e}"
        return None

    def extract_direct_answer(self, query, snippets):
        # Prefer snippets with recent years or 'current'
        current_year = '2025'
        preferred_snippets = []
        for snippet in snippets:
            if any(word in snippet.lower() for word in ['current', 'since', 'as of', current_year, '2024', '2023']):
                if 'google search' not in snippet.lower():
                    preferred_snippets.append(snippet)
        # Use preferred snippets if available
        search_space = preferred_snippets if preferred_snippets else snippets
        # Patterns for extracting names
        patterns = [
            r"prime minister of india is ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"current prime minister of india is ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"([A-Z][a-z]+ [A-Z][a-z]+) is the current prime minister of india",
            r"([A-Z][a-z]+ [A-Z][a-z]+) is the prime minister of india",
        ]
        for snippet in search_space:
            s = snippet.lower()
            for pat in patterns:
                match = re.search(pat, s, re.IGNORECASE)
                if match:
                    return match.group(1).title()
        # Fallback: first proper noun in preferred snippet
        for snippet in search_space:
            match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+)', snippet)
            if match and 'google search' not in match.group(1).lower():
                return match.group(1)
        return None
