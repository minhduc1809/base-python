import uuid
from fastapi import APIRouter, File, UploadFile, status
from app.core.context import get_current_partition_code
from app.tasks.import_tasks import process_excel_import_session

router = APIRouter(prefix="/import-session", tags=["import-session"])


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_import_session(file: UploadFile = File(...)):
    session_id = f"import_{uuid.uuid4().hex[:8]}"
    partition_code = get_current_partition_code() or "default"
    file_path = f"/tmp/{session_id}_{file.filename}"

    # Dispatch task to Celery worker pool asynchronously
    task = process_excel_import_session.delay(
        session_id=session_id, file_path=file_path, partition_code=partition_code
    )

    return {
        "session_id": session_id,
        "task_id": task.id,
        "status": "processing",
        "message": "File đã được tiếp nhận và đẩy vào Celery Worker xử lý ngầm",
    }
