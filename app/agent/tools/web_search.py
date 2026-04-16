import httpx
from urllib.parse import quote


async def web_search(query: str) -> str:
    """
    Search the web using DuckDuckGo
    """
    try:
        url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()

        parts = []

        # Abstract (Wikipedia-style summary)
        if data.get("AbstractText"):
            parts.append(f"Summary: {data['AbstractText']}")
            if data.get("AbstractURL"):
                parts.append(f"Source: {data['AbstractURL']}")

        # Answer (instant answer like calculations, facts)
        if data.get("Answer"):
            parts.append(f"Direct answer: {data['Answer']}")

        # Related topics
        related = data.get("RelatedTopics", [])[:3]
        if related:
            topics = []
            for t in related:
                if isinstance(t, dict) and t.get("Text"):
                    topics.append(f"- {t['Text'][:200]}")
            if topics:
                parts.append("Related info:\n" + "\n".join(topics))

        if not parts:
            return (
                f"No direct results found for '{query}'. "
                "Try rephrasing or being more specific."
            )

        return "\n\n".join(parts)

    except Exception as e:
        return f"Search failed: {str(e)}"