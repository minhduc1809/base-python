import time
from app.core.logging import logger
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_excel_import_session(self, session_id: str, file_path: str, partition_code: str):
    """Celery background task xử lý đọc và import file Excel hàng loạt."""
    logger.info(
        "Celery Task: Started processing Excel import",
        session_id=session_id,
        file_path=file_path,
        partition_code=partition_code,
    )
    try:
        # Giả lập đọc file Excel bằng openpyxl / pandas
        time.sleep(2)  # Process simulation
        logger.info("Celery Task: Successfully processed Excel import", session_id=session_id)
        return {"status": "completed", "session_id": session_id, "processed_rows": 150}
    except Exception as exc:
        logger.error("Celery Task: Error processing Excel import", error=str(exc))
        raise self.retry(exc=exc)
