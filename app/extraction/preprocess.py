from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image, ImageEnhance, ImageOps

MAX_PDF_PAGES = 8
MAX_PAGE_PIXELS = 16_000_000
MAX_COMPOSITE_HEIGHT = 24_000


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
    """Return one normalized image; PDF pages are stacked into a bounded composite."""
    pages = [Image.open(BytesIO(data)).convert("RGB") for data, _ in document_to_images(raw, filename)]
    try:
        width = min(max(page.width for page in pages), 1800)
        resized = []
        for page in pages:
            if page.width > width:
                height = max(1, round(page.height * width / page.width))
                page = page.resize((width, height), Image.Resampling.LANCZOS)
            resized.append(page)
        canvas_width = max(page.width for page in resized)
        canvas_height = sum(page.height for page in resized) + 24 * (len(resized) - 1)
        if canvas_height > MAX_COMPOSITE_HEIGHT:
            scale = MAX_COMPOSITE_HEIGHT / canvas_height
            resized = [page.resize((max(1, int(page.width * scale)), max(1, int(page.height * scale))), Image.Resampling.LANCZOS) for page in resized]
            canvas_width = max(page.width for page in resized)
            canvas_height = sum(page.height for page in resized) + 24 * (len(resized) - 1)
        canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
        y = 0
        for page in resized:
            canvas.paste(page, (0, y))
            y += page.height + 24
        output = BytesIO()
        canvas.save(output, format="PNG", optimize=True)
        return output.getvalue(), "image/png"
    finally:
        for page in pages:
            page.close()
