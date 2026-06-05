from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ..models.chat import ChatRequest, ChatResponse
from ..core.retriever import HybridRetriever
from ..core.generator import Generator
from ..deps import get_retriever, get_generator, get_session_store
from ..utils.logger import get_logger
import uuid

logger = get_logger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    retriever: HybridRetriever = Depends(get_retriever),
    generator: Generator = Depends(get_generator),
    store: dict = Depends(get_session_store),
):
    session_id = req.session_id or str(uuid.uuid4())
    history = store.get(session_id, [])

    retrieval = await retriever.retrieve(req.message)
    context = retriever.format_context(retrieval)
    answer = await generator.generate(req.message, context, history)

    history += [
        {"role": "user", "content": req.message},
        {"role": "assistant", "content": answer},
    ]
    store[session_id] = history[-20:]

    return ChatResponse(
        answer=answer,
        retrieved_nodes=[
            {"label": n["label"], "dieu_khoan": n.get("dieu_khoan", "")}
            for n in retrieval["nodes"]
        ],
        relationships=retrieval["relationships"],
        session_id=session_id,
    )


@router.websocket("/ws/chat")
async def ws_chat(
    websocket: WebSocket,
    retriever: HybridRetriever = Depends(get_retriever),
    generator: Generator = Depends(get_generator),
    store: dict = Depends(get_session_store),
):
    await websocket.accept()
    logger.info("WebSocket connection opened")

    try:
        while True:
            data = await websocket.receive_json()
            session_id = data.get("session_id", str(uuid.uuid4()))
            query = data["message"]
            history = store.get(session_id, [])

            # Gửi retrieved nodes trước
            retrieval = await retriever.retrieve(query)
            context = retriever.format_context(retrieval)
            await websocket.send_json({
                "type": "context",
                "retrieved_nodes": [
                    {"label": n["label"], "dieu_khoan": n.get("dieu_khoan", "")}
                    for n in retrieval["nodes"]
                ],
                "relationships": retrieval["relationships"],
            })

            # Stream từng token
            full_answer = []
            async for token in generator.stream(query, context, history):
                full_answer.append(token)
                await websocket.send_json({"type": "token", "content": token})

            answer = "".join(full_answer)
            await websocket.send_json({"type": "done"})

            history += [
                {"role": "user", "content": query},
                {"role": "assistant", "content": answer},
            ]
            store[session_id] = history[-20:]

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")