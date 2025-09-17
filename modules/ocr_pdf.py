# ocr_pdf_module_prod.py
import io
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_page_to_pil(page, zoom=2):
    """Render a PyMuPDF page to PIL Image with zoom (scale)."""
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return img

def ocr_with_tesseract(pil_image, lang=None, config='--oem 1 --psm 3'):
    import pytesseract
    return pytesseract.image_to_string(pil_image, lang=lang, config=config)

def ocr_with_easyocr(pil_image, lang_list=None, reader=None, gpu=False):
    import numpy as np
    if reader is None:
        import easyocr
        reader = easyocr.Reader(lang_list or ['en'], gpu=gpu)
    img_arr = np.array(pil_image.convert('RGB'))
    result = reader.readtext(img_arr, detail=0, paragraph=True)
    text = "\n".join(result)
    return text, reader

def parse_page_range(s, maxpage):
    s = s.strip().lower()
    if s in ('all', '*', ''):
        return list(range(1, maxpage+1))
    pages = set()
    for part in s.split(','):
        part = part.strip()
        if '-' in part:
            a, b = map(int, part.split('-', 1))
            pages.update(range(max(1, a), min(maxpage, b)+1))
        else:
            n = int(part)
            if 1 <= n <= maxpage:
                pages.add(n)
    return sorted(pages)

def ocr_pdf(
    pdf_path,
    method="tesseract",
    pages="all",
    lang=None,
    zoom=2.0,
    tesseract_config="--oem 1 --psm 3",
    gpu=False
):
    """
    OCR a PDF and return results in-memory.

    Returns:
        dict: {
            "combined_text": str,
            "pages": [str, str, ...]
        }
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    n_pages = doc.page_count
    pages_to_process = parse_page_range(pages, n_pages)

    page_texts = []
    easyocr_reader = None
    if method == "easyocr":
        lang_list = [l.strip() for l in (lang or "en").split(",")]
        import easyocr
        logger.info("Initializing EasyOCR reader...")
        easyocr_reader = easyocr.Reader(lang_list, gpu=gpu)

    if method == "tesseract":
        import pytesseract
        # Uncomment if Tesseract path needed
        # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    for pnum in tqdm(pages_to_process, desc="OCR pages"):
        try:
            page = doc.load_page(pnum - 1)
            pil_img = render_page_to_pil(page, zoom=zoom)

            if method == "tesseract":
                text = ocr_with_tesseract(pil_img, lang=lang, config=tesseract_config)
            else:
                text, easyocr_reader = ocr_with_easyocr(
                    pil_img, lang_list=(lang or "en").split(","), reader=easyocr_reader, gpu=gpu
                )

            text = text.replace("\r\n", "\n").strip()
            if not text:
                text = "[NO TEXT DETECTED]"

            page_texts.append(text)

        except Exception as e:
            logger.error(f"Failed OCR on page {pnum}: {e}")
            page_texts.append("[OCR FAILED]")

    combined_text = "\n\n".join([f"--- PAGE {i+1} ---\n{text}" for i, text in enumerate(page_texts)])
    return {"combined_text": combined_text, "pages": page_texts}


def ocr_pdf_async(*args, **kwargs):
    """Run OCR in background thread."""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(ocr_pdf, *args, **kwargs)
    return future
