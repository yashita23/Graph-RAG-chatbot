import json
import time
import requests
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

API_URL = "http://localhost:8000/chat"
DATASET_PATH = "data/evaluation_dataset.json"
OUTPUT_PATH = f"eval_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# ============================================================
# Màu sắc terminal
# ============================================================
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

print(f"{YELLOW}Đang tải mô hình SBERT (keepitreal/vietnamese-sbert) để chấm điểm...{RESET}")
# Tận dụng mô hình SBERT có sẵn trong requirements của project
sbert_model = SentenceTransformer("keepitreal/vietnamese-sbert")


def load_dataset(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def call_api(question: str, retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        try:
            res = requests.post(API_URL, json={"message": question}, timeout=120)
            if res.status_code == 200:
                return res.json()
            else:
                print(f"  {YELLOW}API error {res.status_code}, retry {attempt+1}{RESET}")
        except Exception as e:
            print(f"  {YELLOW}Request failed: {e}, retry {attempt+1}{RESET}")
        time.sleep(2)
    return {"answer": "", "retrieved_nodes": [], "relationships": []}


def score_semantic_similarity(answer: str, ground_truth: str) -> float:
    """Tính độ tương đồng ngữ nghĩa bằng Cosine Similarity."""
    if not answer.strip() or not ground_truth.strip():
        return 0.0
    emb1 = sbert_model.encode(answer, convert_to_tensor=True)
    emb2 = sbert_model.encode(ground_truth, convert_to_tensor=True)
    cosine_scores = util.cos_sim(emb1, emb2)
    return max(0.0, cosine_scores.item())


def score_keyword(answer: str, keywords: list[str]) -> float:
    """Kiểm tra tỷ lệ xuất hiện của các từ khóa cứng (số liệu, tên riêng)."""
    if not keywords: return 1.0
    ans_lower = answer.lower()
    found = sum(1 for kw in keywords if kw.lower() in ans_lower)
    return found / len(keywords)


def score_nodes(retrieved_nodes: list[dict], expected_nodes: list[str]) -> float:
    """Đánh giá Node Hit Rate (Tỷ lệ tìm thấy node kỳ vọng trong Graph)."""
    if not expected_nodes: return 1.0
    texts = " ".join([str(n).lower() for n in retrieved_nodes])
    hits = sum(1 for exp in expected_nodes if exp.lower() in texts)
    return hits / len(expected_nodes)


def score_dieu_khoan(nodes: list[dict], expected_dieu: str | None) -> bool:
    """Kiểm tra điều khoản có được retrieve đúng không."""
    if expected_dieu is None: return True
    for node in nodes:
        dieu = node.get("dieu_khoan", "")
        if dieu and expected_dieu.lower() in dieu.lower():
            return True
    return False


def check_hallucination_semantic(answer: str) -> dict:
    """Kiểm tra xem model có từ chối trả lời an toàn không."""
    # So sánh câu trả lời với một câu từ chối chuẩn
    refusal_anchor = "Quy chế đào tạo không quy định hoặc không có thông tin về vấn đề này."
    score = score_semantic_similarity(answer, refusal_anchor)
    
    # Những từ khóa thể hiện rõ sự từ chối
    explicit_refusals = ["không quy định", "không đề cập", "không có trong tài liệu", "không tìm thấy"]
    has_explicit = any(word in answer.lower() for word in explicit_refusals)
    
    passed = score > 0.45 or has_explicit
    return {"passed": passed, "score": score}


def evaluate_question(q: dict) -> dict:
    print(f"\n{BLUE}[Q{q['id']:02d}]{RESET} {q['question']}")

    start = time.time()
    result = call_api(q["question"])
    elapsed = time.time() - start

    answer = result.get("answer", "")
    nodes = result.get("retrieved_nodes", [])
    is_hallucination = q.get("hallucination_check", False)

    # 1. RETRIEVAL METRICS
    node_hit_rate = score_nodes(nodes, q.get("expected_nodes", []))
    dieu_correct = score_dieu_khoan(nodes, q.get("expected_dieu"))

    # 2. GENERATION METRICS & TỔNG HỢP
    if is_hallucination:
        hall_res = check_hallucination_semantic(answer)
        overall_score = hall_res["score"]
        overall = hall_res["passed"]
        kw_score, sem_score = 0.0, 0.0
    else:
        sem_score = score_semantic_similarity(answer, q["ground_truth"])
        kw_score = score_keyword(answer, q.get("expected_keywords", []))
        
        # Generation Score ưu tiên Semantic (60%) và Keyword (40%)
        generation_score = (sem_score * 0.6) + (kw_score * 0.4)
        
        # Retrieval Score kết hợp Hit Rate và Điều khoản
        retrieval_score = (node_hit_rate * 0.5) + (1.0 if dieu_correct else 0.0) * 0.5
        
        # Tổng kết: Retrieval (40%), Generation (60%)
        overall_score = (retrieval_score * 0.4) + (generation_score * 0.6)
        overall = overall_score >= 0.65  # Ngưỡng pass

    # IN KẾT QUẢ
    status = f"{GREEN}✓ PASS{RESET}" if overall else f"{RED}✗ FAIL{RESET}"
    print(f"  {status} | Score: {overall_score:.0%} | Time: {elapsed:.1f}s")
    
    if is_hallucination:
        print(f"  Hallucination Test: {'Pass' if overall else 'Fail'} (Độ tương tự từ chối: {overall_score:.0%})")
    else:
        dieu_status = f"{GREEN}✓{RESET}" if dieu_correct else f"{RED}✗{RESET}"
        print(f"  Retrieval: Node Hit Rate: {node_hit_rate:.0%} | Điều khoản: {dieu_status}")
        print(f"  Generation: Semantic Sim: {sem_score:.0%} | Keyword Match: {kw_score:.0%}")

    ans_preview = answer.replace('\n', ' ')
    print(f"  Answer: {ans_preview[:120]}{'...' if len(ans_preview) > 120 else ''}")

    return {
        "id": q["id"],
        "category": q["category"],
        "difficulty": q["difficulty"],
        "question": q["question"],
        "answer": answer,
        "retrieved_nodes": [n.get("label", "") for n in nodes],
        "node_hit_rate": node_hit_rate,
        "dieu_correct": dieu_correct,
        "semantic_score": sem_score if not is_hallucination else 0.0,
        "keyword_score": kw_score if not is_hallucination else 0.0,
        "hallucination_check": is_hallucination,
        "overall_score": overall_score,
        "passed": overall,
        "elapsed_seconds": elapsed,
    }


def print_summary(results: list[dict], dataset: dict):
    total = len(results)
    if total == 0: return
        
    passed = sum(1 for r in results if r["passed"])
    non_hall = [r for r in results if not r["hallucination_check"]]
    hall_results = [r for r in results if r["hallucination_check"]]
    
    avg_overall = sum(r["overall_score"] for r in results) / total
    avg_node = sum(r["node_hit_rate"] for r in non_hall) / len(non_hall) if non_hall else 0
    avg_dieu = sum(1 for r in non_hall if r["dieu_correct"]) / len(non_hall) if non_hall else 0
    avg_sem = sum(r["semantic_score"] for r in non_hall) / len(non_hall) if non_hall else 0
    avg_kw = sum(r["keyword_score"] for r in non_hall) / len(non_hall) if non_hall else 0
    
    print(f"\n{'='*60}")
    print(f"{BOLD}TỔNG KẾT ĐÁNH GIÁ (LOCAL EVALUATION){RESET}")
    print(f"{'='*60}")
    print(f"Tổng câu hỏi: {total}")
    print(f"Pass/Fail: {GREEN}{passed}{RESET}/{RED}{total-passed}{RESET}")
    print(f"Overall Score TB: {BOLD}{avg_overall:.1%}{RESET}")
    
    if non_hall:
        print(f"\n{BOLD}1. RETRIEVAL METRICS (Graph Search):{RESET}")
        print(f"  - Node Hit Rate TB: {avg_node:.1%}")
        print(f"  - Điều khoản Recall: {avg_dieu:.1%} ({sum(1 for r in non_hall if r['dieu_correct'])}/{len(non_hall)} câu)")
        
        print(f"\n{BOLD}2. GENERATION METRICS (Qwen2.5:7b):{RESET}")
        print(f"  - Semantic Similarity: {avg_sem:.1%} (Độ đúng ý nghĩa)")
        print(f"  - Keyword Match: {avg_kw:.1%} (Độ chính xác từ khóa cứng)")
        
    if hall_results:
        hall_pass = sum(1 for r in hall_results if r["passed"])
        print(f"\n{BOLD}3. HALLUCINATION TEST:{RESET}")
        print(f"  - Tỷ lệ từ chối an toàn: {hall_pass}/{len(hall_results)}")
        
    print(f"\nThời gian TB/câu: {sum(r['elapsed_seconds'] for r in results) / total:.1f}s")


def main():
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Graph RAG Evaluation — QCDT 2025 (Local){RESET}")
    print(f"{'='*60}")
    print(f"API: {API_URL}")
    print(f"SBERT: keepitreal/vietnamese-sbert")

    try:
        requests.get("http://localhost:8000/health", timeout=5)
    except:
        print(f"Backend: {RED}OFFLINE — Hãy khởi động backend trước!{RESET}")
        return

    dataset = load_dataset(DATASET_PATH)
    questions = dataset["questions"]
    print(f"Số câu hỏi: {len(questions)}\n")

    results = []
    for q in questions:
        results.append(evaluate_question(q))
        time.sleep(0.5)  # Tránh overload Ollama

    print_summary(results, dataset)

    output = {
        "metadata": {
            "evaluated_at": datetime.now().isoformat(),
            "api_url": API_URL,
            "total_questions": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "overall_score": sum(r["overall_score"] for r in results) / len(results) if results else 0,
            "evaluation_method": "Semantic Similarity (vietnamese-sbert) + Keyword + Node Hit"
        },
        "results": results
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{GREEN}Kết quả đã lưu vào: {OUTPUT_PATH}{RESET}")


if __name__ == "__main__":
    main()
