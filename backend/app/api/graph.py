from fastapi import APIRouter, Depends
from ..core.graph_client import GraphClient
from ..deps import get_graph_client
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/graph/nodes")
async def get_nodes(client: GraphClient = Depends(get_graph_client)):
    nodes = await client.get_all_nodes()
    return {"nodes": nodes, "total": len(nodes)}


@router.get("/graph/edges")
async def get_edges(client: GraphClient = Depends(get_graph_client)):
    edges = await client.get_all_edges()
    return {"edges": edges, "total": len(edges)}


@router.get("/graph/stats")
async def get_stats(client: GraphClient = Depends(get_graph_client)):
    stats = await client.get_stats()
    return stats