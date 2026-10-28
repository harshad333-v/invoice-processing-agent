from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image, ImageEnhance, ImageOps

MAX_PDF_PAGES = 8
MAX_PAGE_PIXELS = 16_000_000


def document_to_images(raw: bytes, filename: str, max_pages: int = MAX_PDF_PAGES) -> list[tuple[bytes, str]]:
    """Render a bounded number of PDF pages or normalize a single uploaded image."""
    is_pdf = Path(filename).suffix.lower() == ".pdf" or raw.startswith(b"%PDF")
    if is_pdf:
        results: list[tuple[bytes, str]] = []
        with fitz.open(stream=raw, filetype="pdf") as pdf:
            if pdf.page_count == 0:
                raise ValueError("PDF contains no pages")
            for page_number in range(min(pdf.page_count, max_pages)):
                page = pdf.load_page(page_number)
                rect = page.rect
                scale = min(1.7, (MAX_PAGE_PIXELS / max(rect.width * rect.height, 1)) ** 0.5)
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                results.append(_normalize_image(pix.tobytes("png")))
        return results
    return [_normalize_image(raw)]


def _normalize_image(raw: bytes) -> tuple[bytes, str]:
    with Image.open(BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image = ImageOps.autocontrast(image)
        image = ImageEnhance.Contrast(image).enhance(1.05)
        output = BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue(), "image/png"


def document_to_image(raw: bytes, filename: str) -> tuple[bytes, str]:
    """Backward-compatible helper returning the first page."""
    return document_to_images(raw, filename)[0]
