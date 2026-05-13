from pypdf import PdfReader
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PDFLoader:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def load_pages(self) -> list[str]:
        logger.info(f"Reading PDF: {self.pdf_path}")
        reader = PdfReader(self.pdf_path)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
        logger.info(f"Loaded {len(pages)} pages from PDF")
        return pages

    def chunk_by_dieu(self, pages: list[str], chunk_size: int = 3) -> list[str]:
        """
        Chia văn bản thành các chunk theo nhóm trang.
        Mỗi chunk gồm chunk_size trang liên tiếp.
        """
        chunks = []
        for i in range(0, len(pages), chunk_size):
            chunk = "\n\n".join(pages[i:i + chunk_size])
            if len(chunk.strip()) > 100:  # Bỏ qua chunk quá ngắn
                chunks.append(chunk)
        logger.info(f"Created {len(chunks)} chunks")
        return chunks