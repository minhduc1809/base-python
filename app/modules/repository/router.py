from fastapi import APIRouter

router = APIRouter(prefix="/repository", tags=["repository"])


@router.get("/status")
async def get_repository_status():
    return {"orm": "SQLAlchemy 2.0 Async + Motor Raw Client", "status": "active"}
