import requests
from bs4 import BeautifulSoup
import urllib.parse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": (
                "Fetch and read the text content of any public webpage or URL. "
                "Use this to read documentation, articles, GitHub READMEs, etc. "
                "Returns clean extracted text, not raw HTML."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL to fetch."},
                    "max_chars": {
                        "type": "integer",
                        "description": "Max characters to return. Default 4000.",
                        "default": 4000,
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for information. Returns titles, URLs, and snippets "
                "for the top results. Use when you need to find documentation, "
                "answers, or current information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query string."},
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return. Default 5.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def web_fetch(url: str, max_chars: int = 4000) -> str:
    """Fetch a URL and return clean readable text."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Collapse excessive blank lines
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        clean = "\n".join(lines)
        return clean[:max_chars] + ("..." if len(clean) > max_chars else "")

    except requests.exceptions.Timeout:
        return "[ AURA ] web_fetch: request timed out."
    except requests.exceptions.HTTPError as e:
        return f"[ AURA ] web_fetch: HTTP error {e.response.status_code}"
    except Exception as e:
        return f"[ AURA ] web_fetch error: {e}"


def web_search(query: str, max_results: int = 5) -> str:
    """
    Search DuckDuckGo by scraping its HTML — no API key required.
    Falls back to Google scraping if DDG fails.
    """
    try:
        return _search_ddg(query, max_results)
    except Exception:
        try:
            return _search_google(query, max_results)
        except Exception as e:
            return f"[ AURA ] web_search failed: {e}"


def _search_ddg(query: str, max_results: int) -> str:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for result in soup.select(".result")[:max_results]:
        title_tag = result.select_one(".result__title")
        snippet_tag = result.select_one(".result__snippet")
        link_tag = result.select_one(".result__url")

        title = title_tag.get_text(strip=True) if title_tag else "No title"
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else "No snippet"
        link = link_tag.get_text(strip=True) if link_tag else ""

        results.append(f"• {title}\n  {link}\n  {snippet}")

    if not results:
        raise ValueError("No results found from DDG")
    return "\n\n".join(results)


def _search_google(query: str, max_results: int) -> str:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}&num={max_results}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for g in soup.select("div.g")[:max_results]:
        title = g.select_one("h3")
        snippet = g.select_one("div.BNeawe, div[data-sncf]")
        link = g.select_one("a")

        t = title.get_text(strip=True) if title else "No title"
        s = snippet.get_text(strip=True) if snippet else "No snippet"
        l = link["href"] if link and link.get("href", "").startswith("http") else ""

        results.append(f"• {t}\n  {l}\n  {s}")

    return "\n\n".join(results) if results else "[ AURA ] No search results found."
