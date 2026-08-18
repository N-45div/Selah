from typing import List, Dict, Any, Optional
from parallel import Parallel
from ..config import PARALLEL_API_KEY


_parallel_client: Optional[Parallel] = None


def get_parallel_client() -> Optional[Parallel]:
    global _parallel_client
    if _parallel_client is None and PARALLEL_API_KEY:
        try:
            _parallel_client = Parallel(api_key=PARALLEL_API_KEY)
        except Exception as e:
            print(f"Warning: Failed to initialize Parallel client: {e}")
    return _parallel_client


def search_licensing_web(objective: str, search_queries: List[str], mode: str = "fast") -> Dict[str, Any]:
    """
    Search the web using the official Parallel SDK (parallel-web).
    Trims excerpts to ~900 chars (max 3 per result).
    """
    client = get_parallel_client()
    if not client:
        # If API key is missing, return a message indicating Parallel key is needed
        return {
            "error": "PARALLEL_API_KEY is not set or client initialization failed.",
            "results": []
        }

    try:
        # Search queries should be 3-6 words
        cleaned_queries = [q.strip() for q in search_queries if q.strip()][:4]
        if not cleaned_queries:
            cleaned_queries = [objective[:100]]

        search_response = client.search(
            objective=objective,
            search_queries=cleaned_queries,
            mode=mode
        )

        formatted_results = []
        raw_results = getattr(search_response, "results", []) or []

        for item in raw_results:
            title = getattr(item, "title", "Untitled") or "Untitled"
            url = getattr(item, "url", "") or ""
            raw_excerpts = getattr(item, "excerpts", []) or []

            # Excerpts can be long — trim to ~900 chars, max 3 per result
            trimmed_excerpts = []
            for exc in raw_excerpts[:3]:
                if exc:
                    trimmed = exc[:900] + ("..." if len(exc) > 900 else "")
                    trimmed_excerpts.append(trimmed)

            publish_date = getattr(item, "publish_date", None)

            formatted_results.append({
                "title": title,
                "url": url,
                "excerpts": trimmed_excerpts,
                "publish_date": publish_date
            })

        return {
            "objective": objective,
            "queries": cleaned_queries,
            "results": formatted_results
        }
    except Exception as e:
        print(f"Parallel search error: {e}")
        return {
            "error": str(e),
            "results": []
        }
