import pytest
from unittest.mock import AsyncMock, MagicMock
from app.common.base_framework.base_import_service import BaseImportService, ImportMode
from app.modules.import_session.service import ImportSessionService
from app.modules.data_process.service import DataProcessService
from app.modules.cron_manager.service import CronManagerService
from app.modules.increment.service import IncrementService
from app.modules.user.user_import_service import UserImportService
from app.modules.setting.setting_import_service import SettingImportService
from pydantic import BaseModel, Field


class DummyModel(BaseModel):
    username: str = Field(..., title="Tên đăng nhập", description="Username", examples=["admin"])
    email: str = Field(..., title="Email", description="User email", examples=["admin@gmail.com"])


@pytest.mark.asyncio
async def test_base_import_service_template_and_insert():
    repo_mock = MagicMock()
    repo_mock.create = AsyncMock(return_value={"_id": "1", "username": "testuser"})
    repo_mock.collection = MagicMock()

    service = BaseImportService(repo_mock)

    # 1. Test get_import_definition
    definitions = service.get_import_definition(DummyModel)
    assert len(definitions) == 2
    assert definitions[0]["field"] == "username"

    # 2. Test get_import_template_wb
    wb = service.get_import_template_wb(DummyModel)
    assert wb.active.title == "Data"

    # 3. Test insert_import
    rows = [{"username": "testuser", "email": "test@gmail.com"}]
    res = await service.insert_import(rows, mode=ImportMode.CREATE, dry_run=False)
    assert res["error"] is False
    assert res["totalProcessed"] == 1


@pytest.mark.asyncio
async def test_import_session_service():
    db_mock = MagicMock()
    coll_mock = MagicMock()
    insert_res = MagicMock()
    insert_res.inserted_id = "session_1"
    coll_mock.insert_one = AsyncMock(return_value=insert_res)
    coll_mock.find_one = AsyncMock(return_value={
        "_id": "session_1",
        "module_name": "user",
        "status": "PROCESSING",
        "error_logs": [{"index": 1, "row": {}, "rowErrors": ["Error test"]}]
    })
    coll_mock.find_one_and_update = AsyncMock(return_value={
        "_id": "session_1",
        "status": "COMPLETED"
    })

    db_mock.__getitem__.side_effect = lambda name: coll_mock

    service = ImportSessionService(db_mock)
    session = await service.create_import_session("user", total_records=10)
    assert session["_id"] == "session_1"

    updated = await service.update_import_session_status("session_1", "COMPLETED")
    assert updated["status"] == "COMPLETED"

    excel_bytes = await service.export_error_excel("session_1")
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0


@pytest.mark.asyncio
async def test_data_process_service():
    db_mock = MagicMock()
    coll_mock = MagicMock()
    insert_res = MagicMock()
    insert_res.inserted_id = "proc_1"
    coll_mock.insert_one = AsyncMock(return_value=insert_res)
    coll_mock.find_one_and_update = AsyncMock(return_value={"_id": "proc_1", "status": "RUNNING"})
    coll_mock.find_one = AsyncMock(return_value={"_id": "proc_1", "status": "COMPLETED", "progress": 100.0})

    db_mock.__getitem__.side_effect = lambda name: coll_mock

    service = DataProcessService(db_mock)
    res = await service.process_data_batch("Test Process", [{"id": 1}, {"id": 2}])
    assert res["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_cron_manager_service():
    db_mock = MagicMock()
    coll_mock = MagicMock()
    insert_res = MagicMock()
    insert_res.inserted_id = "cron_1"
    coll_mock.insert_one = AsyncMock(return_value=insert_res)
    coll_mock.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    coll_mock.find_one_and_update = AsyncMock(return_value={"_id": "cron_1", "enabled": False})

    db_mock.__getitem__.side_effect = lambda name: coll_mock

    service = CronManagerService(db_mock)
    job = await service.add_cron_job("Sync Job", "0 * * * *", "http://localhost/sync")
    assert job["_id"] == "cron_1"

    toggled = await service.toggle_cron_job("cron_1", False)
    assert toggled["enabled"] is False

    deleted = await service.delete_cron_job("cron_1")
    assert deleted is True


@pytest.mark.asyncio
async def test_increment_service():
    redis_mock = MagicMock()
    redis_mock.incr = AsyncMock(return_value=101)
    redis_mock.get = AsyncMock(return_value="101")
    redis_mock.set = AsyncMock()

    db_mock = MagicMock()
    service = IncrementService(redis=redis_mock, db=db_mock)

    val = await service.get_next_increment("USER_CODE")
    assert val == 101

    curr = await service.get_increment_value("USER_CODE")
    assert curr == 101
