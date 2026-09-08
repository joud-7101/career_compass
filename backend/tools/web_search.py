def web_search(query: str) -> list[dict]:

    return [
        {
            "title": f"Search result for: {query}",
            "url": "https://example.com",
            "snippet": "Placeholder web search result."
        }
    ]