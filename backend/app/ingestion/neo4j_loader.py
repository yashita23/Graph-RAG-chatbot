from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from ..config import settings
from ..utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


class Neo4jLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL)

    def setup_indexes(self):
        with self.driver.session() as session:
            session.run("""
                CREATE CONSTRAINT quyche_node_id IF NOT EXISTS
                FOR (n:KhaiNiem) REQUIRE n.id IS UNIQUE
            """)
            session.run("""
                CREATE VECTOR INDEX quyche_embedding IF NOT EXISTS
                FOR (n:KhaiNiem) ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 768,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            session.run("""
                CREATE FULLTEXT INDEX quyche_fulltext IF NOT EXISTS
                FOR (n:KhaiNiem) ON EACH [n.label, n.mo_ta]
            """)
        logger.info("Indexes created successfully")

    def load(self, entities: dict):
        self.setup_indexes()
        nodes = entities["nodes"]
        edges = entities["edges"]

        # Tạo embeddings
        texts = [
            f"{n['label']} {n['properties'].get('mo_ta', '')} {n['properties'].get('gia_tri', '')}"
            for n in nodes
        ]
        logger.info(f"Creating embeddings for {len(nodes)} nodes...")
        embeddings = self.embedder.encode(texts, batch_size=32, show_progress_bar=True)

        # Nạp nodes vào Neo4j
        with self.driver.session() as session:
            for node, emb in zip(nodes, embeddings):
                props = node.get("properties", {})
                session.run("""
                    MERGE (n:KhaiNiem {id: $id})
                    SET n.label      = $label,
                        n.type       = $type,
                        n.mo_ta      = $mo_ta,
                        n.dieu_khoan = $dieu_khoan,
                        n.gia_tri    = $gia_tri,
                        n.embedding  = $embedding,
                        n.updated_at = $updated_at
                """,
                    id=node["id"],
                    label=node["label"],
                    type=node.get("type", "KhaiNiem"),
                    mo_ta=props.get("mo_ta", ""),
                    dieu_khoan=props.get("dieu_khoan", ""),
                    gia_tri=props.get("gia_tri", ""),
                    embedding=emb.tolist(),
                    updated_at=datetime.now().isoformat()
                )
        logger.info(f"Loaded {len(nodes)} nodes")

        # Nạp edges vào Neo4j
        with self.driver.session() as session:
            for edge in edges:
                relation = edge["relation"].upper()
                props = edge.get("properties", {})
                session.run(f"""
                    MATCH (a:KhaiNiem {{id: $from_id}})
                    MATCH (b:KhaiNiem {{id: $to_id}})
                    MERGE (a)-[r:{relation}]->(b)
                    SET r.mo_ta = $mo_ta
                """,
                    from_id=edge["from"],
                    to_id=edge["to"],
                    mo_ta=props.get("mo_ta", "")
                )
        logger.info(f"Loaded {len(edges)} edges")

    def close(self):
        self.driver.close()