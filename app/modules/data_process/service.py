"""
Data Process Service - Xử lý chuyển đổi dữ liệu và thay thế domain trong MongoDB / PostgreSQL.
"""
from typing import Any, Dict, List, Optional, Set
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger


class DataProcessService:
    """Service xử lý dữ liệu hàng loạt."""

    def __init__(self, mongo_db: Optional[AsyncIOMotorDatabase] = None, sql_db: Optional[AsyncSession] = None):
        self.mongo_db = mongo_db
        self.sql_db = sql_db

    # ─── getUpdateObjectReplaceDomain (data-process.service.ts:L17-43) ──
    def _get_update_object_replace_domain(self, obj: dict, old_domain: str, new_domain: str) -> Optional[Dict[str, dict]]:
        """Port 1-1 từ private getUpdateObjectReplaceDomain."""
        update_object = {}
        for key, value in obj.items():
            val_type = type(value)
            new_value = None
            if val_type == str:
                new_value = value
                result_type = "string"
            elif val_type == dict or val_type == list:
                import json
                new_value = json.dumps(value, ensure_ascii=False)
                result_type = "object"
            else:
                continue

            if new_value and old_domain in new_value:
                new_value = new_value.replace(old_domain, new_domain)
                update_object[key] = {"value": new_value, "type": result_type}

        return update_object if update_object else None

    # ─── replaceDomainUrlMongo (data-process.service.ts:L45-102) ────
    async def replace_domain_url_mongo(self, old_domain: str, new_domain: str, skip_tables: Optional[List[str]] = None) -> dict:
        """Port 1-1 từ replaceDomainUrlMongo(dto)."""
        if self.mongo_db is None:
            return {"error": "MongoDB connection not available"}

        skip_db_set: Set[str] = set(skip_tables or [])
        collections = await self.mongo_db.list_collection_names()
        total_updated = 0

        for coll_name in collections:
            if coll_name in skip_db_set:
                continue

            collection = self.mongo_db[coll_name]
            bulk_ops = []
            total = await collection.estimated_document_count()
            i = 0

            async for item in collection.find():
                i += 1
                _id = item["_id"]
                update = {}
                self._collect_update_fields(item, "", update, old_domain, new_domain)

                if update:
                    logger.info(f"{i}/{total} {coll_name} {_id} UPDATE")
                    bulk_ops.append({
                        "filter": {"_id": _id},
                        "update": {"$set": update},
                    })
                else:
                    logger.info(f"{i}/{total} {coll_name} {_id} SKIP")

            if bulk_ops:
                from pymongo import UpdateOne
                await collection.bulk_write([
                    UpdateOne(op["filter"], op["update"]) for op in bulk_ops
                ])
                total_updated += len(bulk_ops)

        return {"total_updated": total_updated}

    def _collect_update_fields(self, obj: Any, field_path: str, update: dict, old_domain: str, new_domain: str):
        """Port 1-1 từ collectUpdateFields (data-process.service.ts:L46-74)."""
        if isinstance(obj, str):
            if old_domain in obj:
                update[field_path] = obj.replace(old_domain, new_domain)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                if key == "_id":
                    continue
                new_path = key if not field_path else f"{field_path}.{key}"
                self._collect_update_fields(value, new_path, update, old_domain, new_domain)
        elif isinstance(obj, list):
            for idx, value in enumerate(obj):
                new_path = f"{field_path}.{idx}" if field_path else str(idx)
                self._collect_update_fields(value, new_path, update, old_domain, new_domain)

    # ─── replaceDomainUrlSql (data-process.service.ts:L104-234) ─────
    async def replace_domain_url_sql(self, old_domain: str, new_domain: str, skip_tables: Optional[List[str]] = None) -> dict:
        """Port 1-1 từ replaceDomainUrlSql(dto)."""
        if self.sql_db is None:
            return {"error": "SQL connection not available"}

        skip_db_set: Set[str] = set(skip_tables or [])

        # Get all table names
        result = await self.sql_db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """))
        table_names = [row[0] for row in result.fetchall()]

        total_updated = 0
        for table_name in table_names:
            if table_name in skip_db_set:
                continue
            updated = await self._process_sql_table(table_name, old_domain, new_domain)
            total_updated += updated

        return {"total_updated": total_updated}

    async def _process_sql_table(self, table_name: str, old_domain: str, new_domain: str, page_size: int = 50000) -> int:
        """Port 1-1 từ processBatch (data-process.service.ts:L117-228)."""
        logger.info(f"Processing SQL table: {table_name}")
        updated_count = 0

        # Get primary key
        pk_result = await self.sql_db.execute(text(f"""
            SELECT a.attname
            FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                AND a.attnum = ANY(i.indkey)
            WHERE  i.indrelid = '"{table_name}"'::regclass
            AND    i.indisprimary
        """))
        pk_row = pk_result.fetchone()
        primary_key = pk_row[0] if pk_row else None

        if primary_key != "_id":
            return 0

        current_page = 1
        has_more = True

        while has_more:
            offset = (current_page - 1) * page_size
            data_result = await self.sql_db.execute(text(
                f'SELECT * FROM "{table_name}" ORDER BY "{primary_key}" ASC LIMIT :limit OFFSET :offset'
            ), {"limit": page_size, "offset": offset})
            
            columns = data_result.keys()
            rows = data_result.fetchall()

            for index, row in enumerate(rows):
                obj = dict(zip(columns, row))
                update = self._get_update_object_replace_domain(obj, old_domain, new_domain)
                _id = obj.get("_id")

                if update:
                    set_parts = []
                    params = {"pk_id": _id}
                    for key, item in update.items():
                        param_name = f"val_{key.replace('-', '_')}"
                        set_parts.append(f'"{key}" = :{param_name}')
                        params[param_name] = item["value"]

                    update_sql = f'UPDATE "{table_name}" SET {", ".join(set_parts)} WHERE _id = :pk_id'
                    await self.sql_db.execute(text(update_sql), params)
                    updated_count += 1
                    logger.info(f"{index + 1}/{len(rows)} {table_name} {_id} UPDATED")
                else:
                    logger.info(f"{index + 1}/{len(rows)} {table_name} {_id} SKIP")

            has_more = len(rows) == page_size
            current_page += 1

        return updated_count
