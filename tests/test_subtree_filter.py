import pytest
from unittest.mock import AsyncMock, MagicMock
from app.common.base_framework.base_repository import BaseMongoRepository, DPQueryScope
from app.core.context import set_current_partition_code


class DummyAsyncCursor:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index < len(self.items):
            res = self.items[self.index]
            self.index += 1
            return res
        raise StopAsyncIteration


@pytest.mark.asyncio
async def test_get_data_partition_condition_subtree():
    # Setup Data Partitions hierarchy:
    # ROOT ("P_ROOT") -> CHILD1 ("P_CHILD1"), CHILD2 ("P_CHILD2")
    # CHILD1 -> GRANDCHILD1 ("P_GC1")

    db_mock = MagicMock()

    async def mock_find_one(query):
        ma = query.get("ma")
        if ma == "P_ROOT":
            return {"_id": "1", "ma": "P_ROOT", "parentCode": None}
        elif ma == "P_CHILD1":
            return {"_id": "2", "ma": "P_CHILD1", "parentCode": "P_ROOT"}
        elif ma == "P_CHILD2":
            return {"_id": "3", "ma": "P_CHILD2", "parentCode": "P_ROOT"}
        elif ma == "P_GC1":
            return {"_id": "4", "ma": "P_GC1", "parentCode": "P_CHILD1"}
        return None

    def mock_find(query):
        parent_query = query.get("parentCode", {})
        parent_in = parent_query.get("$in", []) if isinstance(parent_query, dict) else []

        matching = []
        if "P_ROOT" in parent_in:
            matching.extend([
                {"_id": "2", "ma": "P_CHILD1", "parentCode": "P_ROOT"},
                {"_id": "3", "ma": "P_CHILD2", "parentCode": "P_ROOT"}
            ])
        if "P_CHILD1" in parent_in:
            matching.append({"_id": "4", "ma": "P_GC1", "parentCode": "P_CHILD1"})

        return DummyAsyncCursor(matching)

    partitions_mock = MagicMock()
    partitions_mock.find_one = AsyncMock(side_effect=mock_find_one)
    partitions_mock.find = mock_find

    db_mock.__getitem__.side_effect = lambda name: partitions_mock if name in ("data_partitions", "data_partition_users") else MagicMock()

    set_current_partition_code("P_ROOT")

    repo = BaseMongoRepository(db_mock, "test_collection", scope=DPQueryScope.SUBTREE)
    condition = await repo.get_data_partition_condition()

    # Should contain P_ROOT and all descendant nodes: P_CHILD1, P_CHILD2, P_GC1
    assert "dataPartitionCode" in condition
    codes = condition["dataPartitionCode"]["$in"]
    assert set(codes) == {"P_ROOT", "P_CHILD1", "P_CHILD2", "P_GC1"}
