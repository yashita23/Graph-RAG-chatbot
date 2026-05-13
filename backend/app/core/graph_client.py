from neo4j import AsyncGraphDatabase
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GraphClient:
    _instance = None

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        logger.info(f"Neo4j client created: {settings.NEO4J_URI}")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def close(self):
        await self.driver.close()

    async def verify_connection(self):
        async with self.driver.session() as session:
            result = await session.run("RETURN 1 AS ok")
            record = await result.single()
            return record["ok"] == 1

    async def get_stats(self) -> dict:
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (n:KhaiNiem)
                RETURN count(n) AS total_nodes,
                       collect(DISTINCT n.type) AS types
            """)
            record = await result.single()

            result2 = await session.run("""
                MATCH ()-[r]->()
                RETURN count(r) AS total_edges
            """)
            record2 = await result2.single()

            return {
                "total_nodes": record["total_nodes"] if record else 0,
                "total_edges": record2["total_edges"] if record2 else 0,
                "node_types": {}
            }

    async def get_all_nodes(self) -> list[dict]:
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (n:KhaiNiem)
                RETURN n.id AS id, n.label AS label, n.type AS type,
                       n.mo_ta AS mo_ta, n.dieu_khoan AS dieu_khoan,
                       n.gia_tri AS gia_tri
                ORDER BY n.label
            """)
            return [dict(r) async for r in result]

    async def get_all_edges(self) -> list[dict]:
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (a:KhaiNiem)-[r]->(b:KhaiNiem)
                RETURN a.label AS from_label, type(r) AS relation,
                       b.label AS to_label, r.mo_ta AS mo_ta
            """)
            return [dict(r) async for r in result]