import asyncio
from typing import List, Dict, Any, Optional
from parallel import Parallel, AsyncParallel
from ..config import PARALLEL_API_KEY

_parallel_client: Optional[Parallel] = None
_async_parallel_client: Optional[AsyncParallel] = None


def get_parallel_client() -> Optional[Parallel]:
    global _parallel_client
    if _parallel_client is None and PARALLEL_API_KEY:
        try:
            _parallel_client = Parallel(api_key=PARALLEL_API_KEY)
        except Exception as e:
            print(f"Warning: Failed to initialize Parallel client: {e}")
    return _parallel_client


def get_async_parallel_client() -> Optional[AsyncParallel]:
    global _async_parallel_client
    if _async_parallel_client is None and PARALLEL_API_KEY:
        try:
            _async_parallel_client = AsyncParallel(api_key=PARALLEL_API_KEY)
        except Exception as e:
            print(f"Warning: Failed to initialize AsyncParallel client: {e}")
    return _async_parallel_client


def search_licensing_web(objective: str, search_queries: List[str], mode: str = "fast") -> Dict[str, Any]:
    """
    Synchronous search tool for Google ADK Agent integration.
    """
    client = get_parallel_client()
    if not client:
        return {
            "error": "PARALLEL_API_KEY is not set or client initialization failed.",
            "results": []
        }

    try:
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


async def async_research_licensing_deep(
    title: str,
    artist: str,
    licenses_held: List[str],
    mode: str = "advanced"
) -> Dict[str, Any]:
    """
    High-performance non-blocking async research with Parallel search and primary domain extraction.
    """
    async_client = get_async_parallel_client()
    if not async_client:
        return {"results": [], "extractions": []}

    objective = (
        f"Find copyright owner, original publishing year, CCLI SongSelect ID, "
        f"and YouTube Content ID risk profile for '{title}' by '{artist}'. "
        f"Verify streaming coverage against held licenses: {licenses_held}."
    )

    search_queries = [
        f"{title} {artist} CCLI SongSelect ID",
        f"{title} copyright owner publishing administrator",
        f"{title} public domain hymnary publication year"
    ]

    try:
        search_res = await async_client.search(
            objective=objective,
            search_queries=search_queries,
            mode=mode
        )

        results = getattr(search_res, "results", []) or []
        extractions = []

        # Grounding extraction on primary musicology domains
        top_url = results[0].url if results and hasattr(results[0], "url") else None
        if top_url and any(dom in top_url for dom in ("ccli.com", "hymnary.org", "musicnotes.com", "praisecharts.com")):
            try:
                extract_res = await async_client.extract(
                    urls=[top_url],
                    objective=f"Extract exact copyright notice line, author names, year, and CCLI ID for '{title}'",
                    excerpts=True
                )
                extractions = getattr(extract_res, "results", []) or []
            except Exception as extract_err:
                print(f"Parallel extract non-fatal notice: {extract_err}")

        return {
            "objective": objective,
            "queries": search_queries,
            "results": results,
            "extractions": extractions
        }
    except Exception as e:
        print(f"AsyncParallel deep research error: {e}")
        return {"results": [], "extractions": []}
