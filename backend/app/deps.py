from .core.graph_client import GraphClient
from .core.embedder import Embedder
from .core.retriever import HybridRetriever
from .core.generator import Generator

# Session store đơn giản dùng dict (đủ cho demo/học)
_session_store: dict = {}

def get_graph_client() -> GraphClient:
    return GraphClient.get_instance()

def get_embedder() -> Embedder:
    return Embedder.get_instance()

def get_retriever() -> HybridRetriever:
    return HybridRetriever(
        graph_client=get_graph_client(),
        embedder=get_embedder()
    )

def get_generator() -> Generator:
    return Generator()

def get_session_store() -> dict:
    return _session_store