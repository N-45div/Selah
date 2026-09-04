import asyncio
import contextvars
from typing import List, Dict, Any, Optional, Set
from parallel import Parallel, AsyncParallel
from ..config import PARALLEL_API_KEY

_parallel_client: Optional[Parallel] = None
_async_parallel_client: Optional[AsyncParallel] = None

# Context variable to collect URLs returned by Parallel during a research task
PARALLEL_URLS: contextvars.ContextVar[Optional[Set[str]]] = contextvars.ContextVar("parallel_urls", default=None)


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


def _demojibake(s: str) -> str:
    """Repair UTF-8 double-encoding artifacts (e.g. © → Â©)."""
    if not s:
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def _clean_text(s: str) -> str:
    """Apply demojibake repair and strip whitespace."""
    return _demojibake(s).strip() if s else s


async def search_licensing_web(objective: str, search_queries: List[str], mode: str = "fast") -> Dict[str, Any]:
    """Search the live web for song copyright owner, publisher, CCLI SongSelect ID, and YouTube Content ID evidence. Call this before issuing a verdict; do not answer from memory. objective: the full research goal in one sentence. search_queries: 2-4 keyword queries of 3-6 words each."""
    client = get_async_parallel_client()
    if not client:
        return {
            "error": "PARALLEL_API_KEY is not set or client initialization failed.",
            "results": []
        }

    try:
        cleaned_queries = [q.strip() for q in search_queries if q.strip()][:4]
        if not cleaned_queries:
            cleaned_queries = [objective[:100]]

        search_response = await client.with_options(timeout=25.0, max_retries=1).search(
            objective=objective,
            search_queries=cleaned_queries,
            mode=mode
        )

        formatted_results = []
        raw_results = getattr(search_response, "results", []) or []

        for item in raw_results:
            title = _clean_text(getattr(item, "title", "Untitled") or "Untitled")
            url = getattr(item, "url", "") or ""
            raw_excerpts = getattr(item, "excerpts", []) or []

            trimmed_excerpts = []
            for exc in raw_excerpts[:3]:
                if exc:
                    cleaned = _clean_text(exc)
                    trimmed = cleaned[:900] + ("..." if len(cleaned) > 900 else "")
                    trimmed_excerpts.append(trimmed)

            publish_date = getattr(item, "publish_date", None)

            formatted_results.append({
                "title": title,
                "url": url,
                "excerpts": trimmed_excerpts,
                "publish_date": publish_date
            })

        # Save to context bucket for citation validation
        bucket = PARALLEL_URLS.get()
        if bucket is not None:
            bucket.update(r["url"] for r in formatted_results if r["url"])

        print(f"[PARALLEL] search ok queries={cleaned_queries} results={len(raw_results)}")

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
        return {"results": [], "extractions": [], "evidence": ""}

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
        search_res = await async_client.with_options(timeout=60.0, max_retries=1).search(
            objective=objective,
            search_queries=search_queries,
            mode=mode
        )

        results = getattr(search_res, "results", []) or []
        extractions = []

        # Grounding extraction on primary musicology domains
        top_url = next(
            (r.url for r in results[:4] if getattr(r, "url", None) and any(dom in r.url for dom in ("ccli.com", "hymnary.org", "musicnotes.com", "praisecharts.com"))),
            None
        )
        if top_url:
            try:
                extract_res = await async_client.with_options(timeout=30.0).extract(
                    urls=[top_url],
                    objective=f"Extract exact copyright notice line, author names, year, and CCLI ID for '{title}'",
                    max_chars_total=2000
                )
                extractions = getattr(extract_res, "results", []) or []
            except Exception as extract_err:
                print(f"Parallel extract non-fatal notice: {extract_err}")

        # Record URLs to contextvar bucket
        bucket = PARALLEL_URLS.get()
        if bucket is not None:
            bucket.update(getattr(r, "url", "") for r in results if getattr(r, "url", None))

        print(f"[PARALLEL] deep search ok queries={search_queries} results={len(results)}")

        evidence_parts = []
        for r in results[:4]:
            url = getattr(r, "url", "") or ""
            t = _clean_text(getattr(r, "title", "") or "")
            excs = "\n".join(_clean_text(e) for e in (getattr(r, "excerpts", []) or [])[:2] if e)[:1500]
            evidence_parts.append(f"SOURCE: {t} <{url}>\n{excs}")
        for x in extractions[:2]:
            url = getattr(x, "url", "") or ""
            t = _clean_text(getattr(x, "title", "") or "")
            excs = "\n".join(_clean_text(e) for e in (getattr(x, "excerpts", []) or [])[:2] if e)[:1500]
            evidence_parts.append(f"EXTRACTED PAGE: {t} <{url}>\n{excs}")
        evidence_str = "\n\n".join(evidence_parts)[:6000]

        return {
            "objective": objective,
            "queries": search_queries,
            "results": results,
            "extractions": extractions,
            "evidence": evidence_str
        }
    except Exception as e:
        print(f"AsyncParallel deep research error: {e}")
        return {"results": [], "extractions": [], "evidence": ""}

