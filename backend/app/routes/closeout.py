from fastapi import APIRouter, HTTPException, Response
from ..store import get_plan, get_closeout, save_closeout
from ..agents.closeout_agent import generate_closeout_pack, generate_closeout_markdown_document

router = APIRouter(prefix="/api/plan", tags=["Closeout"])


@router.get("/{plan_id}/closeout")
async def get_closeout_pack_data(plan_id: str):
    """
    Retrieves the generated CloseoutPack for a finished service plan.
    Requires plan.status == 'ended'.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Service plan not found.")

    if plan.status != "ended":
        raise HTTPException(
            status_code=409,
            detail=f"Close-out compliance documentation is available after the live telecast ends. Current plan status is '{plan.status}'."
        )

    closeout = await get_closeout(plan_id)
    if not closeout:
        closeout = await generate_closeout_pack(plan)
        await save_closeout(closeout)

    return closeout


@router.get("/{plan_id}/closeout/download")
async def download_closeout_markdown(plan_id: str):
    """
    Downloads the entire closeout pack as a clean markdown file.
    Requires plan.status == 'ended'.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Service plan not found.")

    if plan.status != "ended":
        raise HTTPException(
            status_code=409,
            detail=f"Close-out compliance documentation is available after the live telecast ends. Current plan status is '{plan.status}'."
        )

    closeout = await get_closeout(plan_id)
    if not closeout:
        closeout = await generate_closeout_pack(plan)
        await save_closeout(closeout)

    markdown_text = generate_closeout_markdown_document(closeout, plan)

    return Response(
        content=markdown_text,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="selah_closeout_{plan_id}.md"'
        }
    )
