import ollama
from ..utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý hỏi đáp chuyên sâu về Quy chế đào tạo của Đại học Bách Khoa Hà Nội (QCDT_2025).

=== NGỮ CẢNH TỪ KNOWLEDGE GRAPH ===
{graph_context}
=== HẾT NGỮ CẢNH ===

Quy tắc TỐI QUAN TRỌNG:
1. CHỈ dựa vào thông tin trong NGỮ CẢNH ở trên. KHÔNG dùng kiến thức ngoài.
2. Khi trả lời về con số/ngưỡng (TC, điểm, thời gian), hãy đọc KỸ phần [gia_tri] trong ngữ cảnh.
3. Luôn trích dẫn Điều/khoản cụ thể (ví dụ: "Theo Điều 10, khoản 2...").
4. Nếu ngữ cảnh có nhiều trường hợp khác nhau (ví dụ: SV bình thường vs SV cảnh báo), hãy trình bày ĐẦY ĐỦ tất cả trường hợp.
5. Nếu câu hỏi liên quan đến nhiều điều khoản, tổng hợp đầy đủ.
6. Nếu không có thông tin trong ngữ cảnh, nói rõ "Quy chế không quy định cụ thể về vấn đề này".
7. Trả lời bằng tiếng Việt, rõ ràng, dùng danh sách khi có nhiều điều kiện."""


class Generator:
    def __init__(self):
        self.model = "qwen2.5:7b"
        logger.info("Ollama generator initialized")

    async def stream(self, query: str, graph_context: str, history: list[dict]):
        system = SYSTEM_PROMPT.format(graph_context=graph_context)
        messages = [{"role": "system", "content": system}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        stream = ollama.chat(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk["message"]["content"]
            if delta:
                yield delta

    async def generate(self, query: str, graph_context: str, history: list[dict]) -> str:
        chunks = []
        async for chunk in self.stream(query, graph_context, history):
            chunks.append(chunk)
        return "".join(chunks)