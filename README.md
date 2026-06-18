

---

##  Giới thiệu
**Graph RAG Chatbot** là một trợ lý ảo thông minh được thiết kế đặc biệt để giải đáp các thắc mắc về **Quy chế đào tạo Đại học Bách Khoa Hà Nội (QCDT_2025)**. 

Bằng cách kết hợp phương pháp tìm kiếm vector truyền thống với duyệt **Đồ thị Tri thức (Knowledge Graph)**, hệ thống có khả năng cung cấp câu trả lời cực kỳ chuẩn xác, luôn trích dẫn nguồn (Điều/Khoản) và triệt tiêu hoàn toàn vấn đề "Ảo giác" (Hallucination) của các AI thông thường.

## Tính năng nổi bật
-  **100% Local / Offline**: Mọi dữ liệu và quy trình suy luận (từ Vector Search đến LLM Generation) đều diễn ra trên máy cá nhân, bảo vệ quyền riêng tư tuyệt đối.
- **Kiến trúc Graph RAG**: Lưu trữ 48 điều khoản pháp lý dưới dạng Mạng lưới liên kết (Nodes & Edges). Trích xuất chính xác tín chỉ, số tháng, và điều kiện nhờ thuật toán đếm kết nối ưu tiên.
-  **Real-time Streaming**: Phản hồi theo thời gian thực token-by-token qua WebSockets mang lại trải nghiệm mượt mà.
- **Giải thích rõ ràng (Explainable AI)**: Tích hợp đồ thị D3.js ngay trên UI, cho phép người dùng nhìn thấy chính xác "não bộ" của AI đang quét qua những vùng thông tin nào để trả lời.
-  **Chống ảo giác (Anti-Hallucination)**: Hệ thống an toàn 100%, sẵn sàng từ chối các câu hỏi nằm ngoài phạm vi hoặc gài bẫy.

## Công nghệ sử dụng
### Backend
- **Framework**: `FastAPI` (REST + WebSockets).
- **Graph Database**: `Neo4j` (chạy qua Docker).
- **LLM**: `Ollama` với mô hình `qwen2.5:7b`.
- **Embedding**: `keepitreal/vietnamese-sbert` (768 chiều).

### Frontend
- **Framework**: `Next.js 16.2`, `React 19`.
- **Styling**: `Tailwind CSS v4`.
- **Visualization**: `D3.js` (Graph Panel).

## Hướng dẫn cài đặt

### Yêu cầu hệ thống
- Tối thiểu 8GB RAM (Khuyến nghị 16GB).
- Python 3.11+, Node.js 18+.
- Docker Desktop.
- Ollama (cài đặt model: `ollama run qwen2.5:7b`).

### Bước 1: Khởi động Database
```bash
# Khởi tạo Neo4j qua Docker
docker compose up -d neo4j
```

### Bước 2: Chạy Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate      # Trên Windows
# source venv/bin/activate  # Trên Linux/macOS

pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

### Bước 3: Chạy Frontend (Mở Terminal mới)
```bash
cd frontend
npm install
npm run dev
```
Truy cập ứng dụng tại: **http://localhost:3000**

## Kết quả Đánh giá (Evaluation Metrics)
Hệ thống được đánh giá tự động dựa trên 50 test-cases siêu khó. Kết quả đo kiểm nội bộ (Local) đạt được:

| Chỉ số (Metric) | Kết quả Đạt được |
| --- | --- |
| **Pass / Fail Ratio** | `86% Pass` (43/50 câu) |
| **Node Hit Rate** | `81.7%` (Tìm đúng dữ liệu cốt lõi) |
| **Điều khoản Recall** | `100.0%` (Trích dẫn đúng 100% văn bản) |
| **Kiểm soát Hallucination** | `100% Pass` (Tuyệt đối không bịa thông tin) |

