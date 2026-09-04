from datetime import datetime
from fastapi import APIRouter, HTTPException
from ..models import (
    AdvanceRequest, ChapterRequest, ChapterMark
)
from ..store import save_plan, get_plan, save_closeout
from ..agents.closeout_agent import generate_closeout_pack, _format_seconds

router = APIRouter(prefix="/api/plan", tags=["Console"])


_ALLOWED = {"draft": {"live"}, "ready": {"live"}, "live": {"ended"}, "ended": set()}


def _require_transition(plan, target: str):
    if target not in _ALLOWED.get(plan.status, set()):
        raise HTTPException(status_code=409, detail=f"Cannot move a plan from '{plan.status}' to '{target}'.")


@router.post("/{plan_id}/live")
async def go_live(plan_id: str):
    """
    Go Live Guard: Blocks going live if any song has unresolved licensing issues.
    Starts the live session timer and marks the initial chapter.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    _require_transition(plan, "live")

    if plan.blocking_songs:
        blocking_titles = [s.title for s in plan.blocking_songs]
        raise HTTPException(
            status_code=400,
            detail=f"Cannot go live: {len(blocking_titles)} song(s) require human resolution: {', '.join(blocking_titles)}"
        )

    now = datetime.now()
    plan.status = "live"
    if not plan.started_at:
        plan.started_at = now.isoformat()

    if not plan.chapters:
        plan.chapters.append(
            ChapterMark(
                seconds_from_start=0,
                label="Welcome & Opening Worship",
                timestamp_str="0:00"
            )
        )

    await save_plan(plan)
    return {
        "success": True,
        "status": plan.status,
        "started_at": plan.started_at
    }



@router.post("/{plan_id}/advance")
async def advance_slide(plan_id: str, payload: AdvanceRequest):
    """
    Updates the current slide index on the backend (in sync with BroadcastChannel on the frontend).
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    plan.current_slide_index = payload.slide_index
    await save_plan(plan)
    return {"success": True, "current_slide_index": plan.current_slide_index}


@router.post("/{plan_id}/chapter")
async def add_chapter(plan_id: str, payload: ChapterRequest):
    """
    Marks a live chapter with accurate elapsed seconds from stream start.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    if plan.status != "live":
        raise HTTPException(status_code=409, detail="Chapters can only be recorded while the stream is live.")

    seconds_elapsed = 0
    if plan.started_at:
        try:
            start_time = datetime.fromisoformat(plan.started_at)
            seconds_elapsed = max(0, int((datetime.now() - start_time).total_seconds()))
        except Exception:
            seconds_elapsed = 0

    if plan.chapters:
        seconds_elapsed = max(seconds_elapsed, plan.chapters[-1].seconds_from_start)

    ts_str = _format_seconds(seconds_elapsed)
    chapter = ChapterMark(
        seconds_from_start=seconds_elapsed,
        label=payload.label,
        timestamp_str=ts_str
    )
    plan.chapters.append(chapter)
    await save_plan(plan)

    return {
        "success": True,
        "chapter": chapter,
        "total_chapters": len(plan.chapters)
    }


@router.post("/{plan_id}/end")
async def end_stream(plan_id: str):
    """
    Ends the live stream session and immediately generates the complete CloseoutPack.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    _require_transition(plan, "ended")

    plan.status = "ended"
    plan.ended_at = datetime.now().isoformat()
    await save_plan(plan)

    # Generate closeout pack with attributions, CCLI log, chapters, and disputes
    closeout = await generate_closeout_pack(plan)
    await save_closeout(closeout)


    return {
        "success": True,
        "status": plan.status,
        "closeout": closeout
    }
