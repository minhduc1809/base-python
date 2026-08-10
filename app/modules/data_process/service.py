from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.data_process.models import DataProcessModel


class DataProcessService:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.model = DataProcessModel(db)

    async def process_data_batch(self, name: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Port từ processDataBatch (data-process.service.ts:L30-80)."""
        process = await self.model.create_process(name, {"totalItems": len(items)})
        process_id = process["_id"]

        # Process batch items
        processed = 0
        total = len(items)
        for item in items:
            processed += 1
            progress = (processed / total) * 100.0 if total > 0 else 100.0
            await self.model.update_progress(process_id, "RUNNING", progress)

        await self.model.update_progress(process_id, "COMPLETED", 100.0)
        return await self.model.get_by_id(process_id)

    async def aggregate_data_process_status(self) -> List[Dict[str, Any]]:
        """Port từ aggregateDataProcessStatus (data-process.service.ts:L85-110)."""
        return await self.model.aggregate_status()
