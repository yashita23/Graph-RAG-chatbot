from sentence_transformers import SentenceTransformer
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class Embedder:
    _instance = None

    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded!")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def encode(self, text: str) -> list[float]:
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=True)
        return embeddings.tolist()