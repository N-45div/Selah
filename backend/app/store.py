import json
import asyncio
from pathlib import Path
from typing import Optional, List
from .config import DATA_DIR
from .models import ServicePlan, CloseoutPack

_lock = asyncio.Lock()


async def save_plan(plan: ServicePlan) -> None:
    async with _lock:
        file_path = DATA_DIR / f"plan_{plan.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(plan.model_dump(), f, indent=2, ensure_ascii=False)


async def get_plan(plan_id: str) -> Optional[ServicePlan]:
    file_path = DATA_DIR / f"plan_{plan_id}.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ServicePlan(**data)
    except Exception as e:
        print(f"Error loading plan {plan_id}: {e}")
        return None


async def list_plans() -> List[ServicePlan]:
    plans = []
    for file_path in DATA_DIR.glob("plan_*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                plans.append(ServicePlan(**data))
        except Exception:
            continue
    return plans


async def save_closeout(closeout: CloseoutPack) -> None:
    async with _lock:
        file_path = DATA_DIR / f"closeout_{closeout.plan_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(closeout.model_dump(), f, indent=2, ensure_ascii=False)


async def get_closeout(plan_id: str) -> Optional[CloseoutPack]:
    file_path = DATA_DIR / f"closeout_{plan_id}.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return CloseoutPack(**data)
    except Exception as e:
        print(f"Error loading closeout for {plan_id}: {e}")
        return None
