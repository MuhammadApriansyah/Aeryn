"""Web Search tool — search the web for information."""

import urllib.request
import urllib.parse
import json


class WebSearchTool:
    """Search the web using DuckDuckGo or similar."""
    
    def execute(self, query: str, limit: int = 5) -> dict:
        """Search the web for information."""
        try:
            # Use DuckDuckGo instant answer API
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            
            req = urllib.request.Request(url, headers={"User-Agent": "Aeryn/2.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            
            results = []
            
            # Abstract
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", ""),
                    "snippet": data["Abstract"],
                    "url": data.get("AbstractURL", ""),
                })
            
            # Related topics
            for topic in data.get("RelatedTopics", [])[:limit]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else "",
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                    })
            
            return {"results": results[:limit], "count": len(results[:limit]), "query": query}
        except Exception as e:
            return {"error": str(e), "results": [], "count": 0}


web_search_tool = WebSearchTool()
