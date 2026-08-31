"""Research Assistant Plugin — Search vault entries and summarize findings."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))

from typing import Dict, Any, List, Optional

def _get_vault():
    from aeryn_core.memory.vault import AerynVault
    return AerynVault()

def _get_search_engine():
    from aeryn_core.memory.hybrid_search import get_search_engine
    return get_search_engine()

def search_vault(query: str, layer: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Search Aeryn vault entries by query."""
    vault = _get_vault()
    entries = vault.search(query, layer=layer, limit=limit)
    
    # Also search via hybrid search engine
    hse = _get_search_engine()
    hybrid_results = hse.search(query, limit=limit)
    
    # Merge and deduplicate
    all_results = []
    seen = set()
    
    for entry in entries:
        key = entry.get("title", "")
        if key not in seen:
            seen.add(key)
            all_results.append({
                "source": "vault",
                "title": entry.get("title", "Untitled"),
                "content": entry.get("body", "")[:500],
                "layer": entry.get("layer", ""),
                "tags": entry.get("tags", []),
            })
    
    for result in hybrid_results:
        key = result.get("memory_id", result.get("title", ""))
        if key not in seen:
            seen.add(key)
            all_results.append({
                "source": "hybrid_search",
                "title": result.get("title", "Untitled"),
                "content": result.get("content", "")[:500],
                "score": result.get("score", 0),
                "tags": result.get("tags", []),
            })
    
    return {
        "status": "ok",
        "query": query,
        "results": all_results[:limit],
        "count": len(all_results),
    }

async def async_summarize(text: str) -> Dict[str, Any]:
    """Summarize text using LLM."""
    from aeryn_core.utils.llm_client import get_mode_router
    
    router = get_mode_router()
    if not router.is_standalone():
        return {"status": "error", "error": "LLM not available in plugin mode"}
    
    persona = "Ringkas teks berikut secara singkat dan jelas:"
    messages = [
        {"role": "system", "content": persona},
        {"role": "user", "content": f"Text to summarize:\\n{text[:3000]}"},
    ]
    
    result = await router.llm.chat(messages)
    return {
        "status": "ok",
        "summary": result["content"],
        "provider": result.get("provider"),
        "model": result.get("model"),
    }

def summarize(text: str) -> Dict[str, Any]:
    """Summarize text (sync wrapper for async_summarize)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, return a coroutine
            return {"status": "info", "message": "Use async_summarize() for async context"}
        return asyncio.run(async_summarize(text))
    except RuntimeError:
        return {"status": "info", "message": "Use async_summarize() for async context"}

# Plugin manifest
PLUGIN_INFO = {
    "name": "research-assistant",
    "version": "1.0.0",
    "description": "Search vault entries and summarize findings",
}

TOOLS = {
    "search_vault": search_vault,
    "summarize": summarize,
}

def get_tools():
    return TOOLS

# CLI entry point for runtime
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No input provided"}))
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON input"}))
        sys.exit(1)
    
    # Determine action from params
    action = params.get("action", "search_vault")
    
    if action == "search_vault":
        query = params.get("query", "")
        try:
            result = asyncio.run(search_vault(query))
        except RuntimeError:
            # Fallback: run sync version
            result = {"status": "error", "message": "Async runtime unavailable"}
    elif action == "summarize":
        text = params.get("text", "")
        try:
            result = asyncio.run(summarize(text))
        except RuntimeError:
            result = {"status": "error", "message": "Async runtime unavailable"}
    else:
        result = {"error": f"Unknown action: {action}"}
    
    print(json.dumps(result, indent=2))
