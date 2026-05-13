from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.chat import router as chat_router
from .api.graph import router as graph_router
from .core.graph_client import GraphClient
from .core.embedder import Embedder
from .utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Graph RAG Chatbot — Quy chế ĐHBK Hà Nội",
    version="1.0.0"
)

# CORS cho phép frontend kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(graph_router)


@app.on_event("startup")
async def startup():
    logger.info("Starting up...")
    # Khởi tạo sẵn các singleton
    GraphClient.get_instance()
    Embedder.get_instance()
    logger.info("Backend ready!")


@app.on_event("shutdown")
async def shutdown():
    await GraphClient.get_instance().close()
    logger.info("Shutdown complete")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}