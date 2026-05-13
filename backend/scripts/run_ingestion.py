import sys
import os

# Thêm backend vào Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.pipeline import run_pipeline

PDF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "QCDT_2025_5445_QD-DHBK.pdf"
)

if __name__ == "__main__":
    if not os.path.exists(PDF_PATH):
        print(f"ERROR: PDF not found at {PDF_PATH}")
        print("Please copy your PDF file to backend/data/ folder")
        sys.exit(1)

    run_pipeline(PDF_PATH, use_cache=True)