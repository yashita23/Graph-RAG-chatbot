import ollama
import json
import time
import re
from ..utils.logger import get_logger

logger = get_logger(__name__)

EXTRACT_PROMPT = """Bạn là công cụ trích xuất dữ liệu. Chỉ trả về JSON, không giải thích.

Từ đoạn văn bản quy chế đào tạo ĐHBK Hà Nội dưới đây, trích xuất entities và relations.

Trả về ĐÚNG định dạng JSON này (không thêm bất kỳ text nào khác):
{"nodes":[{"id":"id_snake_case","label":"tên ngắn","type":"KhaiNiem","properties":{"mo_ta":"mô tả","dieu_khoan":"Điều X","gia_tri":"số liệu"}}],"edges":[{"from":"id1","to":"id2","relation":"lien_quan","properties":{"mo_ta":"giải thích"}}]}

Văn bản cần phân tích:
"""


class EntityExtractor:
    def __init__(self):
        self.model = "qwen2.5:7b"

    def extract(self, chunk: str) -> dict:
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là công cụ trích xuất JSON. Chỉ trả về JSON hợp lệ, không có text khác, không có markdown, không có giải thích."
                },
                {
                    "role": "user",
                    "content": EXTRACT_PROMPT + chunk[:2000]  # Giới hạn chunk size
                }
            ],
            options={
                "temperature": 0.0,
                "num_predict": 2000,
            }
        )
        raw = response["message"]["content"].strip()

        # Tìm JSON trong response
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            raw = json_match.group()

        return json.loads(raw)

    def extract_all(self, chunks: list[str]) -> dict:
        all_nodes = {}
        all_edges = []

        for i, chunk in enumerate(chunks):
            logger.info(f"Extracting chunk {i+1}/{len(chunks)}...")
            try:
                result = self.extract(chunk)
                for node in result.get("nodes", []):
                    if isinstance(node, dict) and "id" in node:
                        all_nodes[node["id"]] = node
                all_edges.extend(result.get("edges", []))
                logger.info(f"  -> Got {len(result.get('nodes',[]))} nodes, {len(result.get('edges',[]))} edges")
            except Exception as e:
                logger.warning(f"Chunk {i+1} error: {e}")

        valid_ids = set(all_nodes.keys())
        valid_edges = [
            e for e in all_edges
            if isinstance(e, dict) and e.get("from") in valid_ids and e.get("to") in valid_ids
        ]

        logger.info(f"Total: {len(all_nodes)} nodes, {len(valid_edges)} edges")
        return {"nodes": list(all_nodes.values()), "edges": valid_edges}