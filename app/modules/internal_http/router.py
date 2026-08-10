from fastapi import APIRouter

router = APIRouter(prefix="/internal-http", tags=["internal-http"])


@router.get("/status")
async def get_internal_status():
    return {"status": "active", "service": "internal-http-client"}
