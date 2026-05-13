import json
import os
from .pdf_loader import PDFLoader
from .entity_extractor import EntityExtractor
from .neo4j_loader import Neo4jLoader
from ..utils.logger import get_logger

logger = get_logger(__name__)

CACHE_PATH = os.path.join(os.path.dirname(__file__), "../../data/entities_cache.json")


def run_pipeline(pdf_path: str, use_cache: bool = True):
    logger.info("=" * 50)
    logger.info("Starting Graph RAG Ingestion Pipeline")
    logger.info("=" * 50)

    # Bước 1: Kiểm tra cache
    if use_cache and os.path.exists(CACHE_PATH):
        logger.info("Cache found! Loading entities from cache...")
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            entities = json.load(f)
        logger.info(f"Loaded {len(entities['nodes'])} nodes, {len(entities['edges'])} edges from cache")
    else:
        # Bước 2: Đọc PDF
        logger.info("Step 1: Loading PDF...")
        loader = PDFLoader(pdf_path)
        pages = loader.load_pages()
        chunks = loader.chunk_by_dieu(pages, chunk_size=3)

        # Bước 3: Trích xuất entities bằng Gemini
        logger.info("Step 2: Extracting entities with Gemini...")
        extractor = EntityExtractor()
        entities = extractor.extract_all(chunks)

        # Lưu cache
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved cache to {CACHE_PATH}")

    # Bước 4: Nạp vào Neo4j
    logger.info("Step 3: Loading into Neo4j...")
    neo4j_loader = Neo4jLoader()
    try:
        neo4j_loader.load(entities)
    finally:
        neo4j_loader.close()

    logger.info("=" * 50)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Nodes: {len(entities['nodes'])}")
    logger.info(f"Edges: {len(entities['edges'])}")
    logger.info("=" * 50)