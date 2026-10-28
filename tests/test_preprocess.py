from io import BytesIO
import fitz
from PIL import Image
from app.extraction.preprocess import document_to_image, document_to_images


def test_png_normalizes_to_png():
    buffer = BytesIO()
    Image.new("RGB", (24, 24), "white").save(buffer, format="PNG")
    data, mime = document_to_image(buffer.getvalue(), "invoice.png")
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    assert mime == "image/png"


def test_pdf_renders_multiple_pages():
    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page(width=300, height=400)
        page.insert_text((30, 30), "Synthetic invoice")
    raw = doc.tobytes()
    doc.close()
    pages = document_to_images(raw, "multi.pdf")
    assert len(pages) == 2
    composite, mime = document_to_image(raw, "multi.pdf")
    assert mime == "image/png"
    with Image.open(BytesIO(composite)) as image:
        assert image.height > image.width
