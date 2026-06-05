import ollama
from ..utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý hỏi đáp về Quy chế đào tạo ĐHBK Hà Nội (QCDT_2025).

QUY TẮC BẮT BUỘC:
1. TRẢ LỜI BẰNG TIẾNG VIỆT 100%. Tuyệt đối KHÔNG sử dụng tiếng Trung Quốc (Chinese) hay bất kỳ ngôn ngữ nào khác.
2. TRẢ LỜI TRỰC TIẾP, ĐI THẲNG VÀO VẤN ĐỀ. Tuyệt đối KHÔNG rào đón (ví dụ: cấm dùng các câu như "Theo thông tin trong ngữ cảnh", "Theo văn bản bạn cung cấp").
3. Chỉ dùng thông tin trong NGỮ CẢNH bên dưới.
4. Mỗi mục trong NGỮ CẢNH có dòng "Giá trị: ..." hoặc các con số (tín chỉ, tháng, phần trăm) — bạn BẮT BUỘC PHẢI trích xuất và ghi chính xác các con số này vào câu trả lời.
5. KHÔNG chém gió, KHÔNG nói "không có thông tin" nếu NGỮ CẢNH đã có dữ liệu.
6. Nếu ngữ cảnh KHÔNG nhắc đến thông tin mà người dùng hỏi, chỉ đáp gọn: "Quy chế đào tạo không quy định hoặc không có thông tin về vấn đề này."

=== NGỮ CẢNH ===
{graph_context}
=== HẾT ==="""


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
            options={
                "temperature": 0.1,
                "num_predict": 1024,
                "stop": ["根据", "按照", "该", "其中", "学分", "学期"],
            }
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