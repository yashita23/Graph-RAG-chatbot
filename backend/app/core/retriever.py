from .embedder import Embedder
from .graph_client import GraphClient
from ..utils.logger import get_logger

logger = get_logger(__name__)

class HybridRetriever:
    def __init__(self, graph_client: GraphClient, embedder: Embedder):
        self.client = graph_client
        self.embedder = embedder

    async def retrieve(self, query: str, top_k: int = 10) -> dict:
        embedding = await self.embedder.encode(query)

        seed_nodes = await self._vector_search(embedding, top_k)
        seed_ids = [n["id"] for n in seed_nodes]
        logger.info(f"Vector search found {len(seed_nodes)} seed nodes")

        neighbor_nodes = await self._graph_traversal(seed_ids, depth=2)
        logger.info(f"Graph traversal found {len(neighbor_nodes)} neighbor nodes")

        all_nodes = {n["id"]: n for n in seed_nodes}
        for n in neighbor_nodes:
            all_nodes.setdefault(n["id"], n)

        relationships = await self._get_relationships(list(all_nodes.keys()))

        return {
            "nodes": list(all_nodes.values()),
            "relationships": relationships,
            "seed_node_ids": seed_ids,
        }

    async def _vector_search(self, embedding: list[float], top_k: int):
        async with self.client.driver.session() as session:
            result = await session.run("""
                CALL db.index.vector.queryNodes('quyche_embedding', $top_k, $embedding)
                YIELD node, score
                RETURN node.id         AS id,
                       node.label      AS label,
                       node.mo_ta      AS mo_ta,
                       node.dieu_khoan AS dieu_khoan,
                       node.gia_tri    AS gia_tri,
                       score
                ORDER BY score DESC
            """, top_k=top_k, embedding=embedding)
            return [dict(r) async for r in result]

    async def _graph_traversal(self, seed_ids: list[str], depth: int = 1):
        if not seed_ids:
            return []
        async with self.client.driver.session() as session:
            # Ưu tiên các node có nhiều kết nối trực tiếp nhất đến tập seed_nodes
            result = await session.run("""
                MATCH (seed:KhaiNiem)-[]-(related:KhaiNiem)
                WHERE seed.id IN $seed_ids AND NOT related.id IN $seed_ids
                WITH related, count(seed) AS connection_count
                ORDER BY connection_count DESC
                LIMIT 25
                RETURN DISTINCT
                    related.id         AS id,
                    related.label      AS label,
                    related.mo_ta      AS mo_ta,
                    related.dieu_khoan AS dieu_khoan,
                    related.gia_tri    AS gia_tri
            """, seed_ids=seed_ids)
            return [dict(r) async for r in result]

    async def _get_relationships(self, node_ids: list[str]):
        if not node_ids:
            return []
        async with self.client.driver.session() as session:
            result = await session.run("""
                MATCH (a:KhaiNiem)-[r]->(b:KhaiNiem)
                WHERE a.id IN $ids AND b.id IN $ids
                RETURN a.label AS from_label,
                       type(r) AS relation,
                       b.label AS to_label,
                       r.mo_ta AS mo_ta
            """, ids=node_ids)
            return [dict(r) async for r in result]

    def format_context(self, retrieval: dict) -> str:
        if not retrieval["nodes"]:
            return "Không tìm thấy thông tin liên quan trong quy chế."

        parts = ["=== THÔNG TIN TỪ QUY CHẾ ==="]
        for n in retrieval["nodes"]:
            dieu = n.get("dieu_khoan", "N/A")
            label = n.get("label", "")
            gia_tri = n.get("gia_tri", "")
            mo_ta = n.get("mo_ta", "")

            block = f"[{dieu}] {label}"
            if gia_tri:
                block += f"\n  Giá trị: {gia_tri}"
            if mo_ta:
                block += f"\n  Mô tả: {mo_ta[:300]}"
            parts.append(block)

        if retrieval["relationships"]:
            parts.append("=== QUAN HỆ ===")
            for r in retrieval["relationships"][:8]:
                parts.append(
                    f"• {r['from_label']} [{r['relation']}] {r['to_label']}"
                )

        return "\n\n".join(parts)