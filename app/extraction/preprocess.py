from io import BytesIO
from pathlib import Path
import fitz
from PIL import Image, ImageEnhance, ImageOps

def document_to_image(raw: bytes, filename: str) -> tuple[bytes, str]:
    """Convert the first PDF page or normalize an uploaded image to PNG."""
    if Path(filename).suffix.lower() == ".pdf" or raw.startswith(b"%PDF"):
        with fitz.open(stream=raw, filetype="pdf") as pdf:
            if not pdf.page_count: raise ValueError("PDF contains no pages")
            pix = pdf.load_page(0).get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
            raw = pix.tobytes("png")
    with Image.open(BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image = ImageOps.autocontrast(image)
        image = ImageEnhance.Contrast(image).enhance(1.05)
        output = BytesIO(); image.save(output, format="PNG", optimize=True)
        return output.getvalue(), "image/png"
