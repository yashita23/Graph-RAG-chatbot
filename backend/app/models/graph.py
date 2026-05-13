from pydantic import BaseModel
from typing import Optional

class NodeModel(BaseModel):
    id: str
    label: str
    type: Optional[str] = None
    mo_ta: Optional[str] = None
    dieu_khoan: Optional[str] = None
    gia_tri: Optional[str] = None

class EdgeModel(BaseModel):
    from_label: str
    relation: str
    to_label: str
    mo_ta: Optional[str] = None

class StatsModel(BaseModel):
    total_nodes: int
    total_edges: int
    node_types: dict