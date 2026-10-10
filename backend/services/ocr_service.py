"""
ArogyaMitra AI - OCR Service
Wrapper for Tesseract (pytesseract) and EasyOCR for extracting text from PDFs and images.
Per FEATURES.md §3 (Feature 1) and TECH_STACK.md §1.
"""

import io
from typing import Optional
from PIL import Image
from backend.core.logger import logger
from backend.config import OCR_MIN_TEXT_LENGTH
from backend.exceptions.arogya_errors import OCRExtractionError, UnsupportedFileTypeError


class OCRService:
    """Multi-engine OCR service with fallback mechanisms."""

    def __init__(self):
        self._easyocr_reader = None

    def _get_easyocr_reader(self):
        """Lazy load EasyOCR reader (downloads model on first call if not present)."""
        if self._easyocr_reader is None:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader(["en"], gpu=False)
            except Exception as e:
                logger.warning(f"[OCRService] EasyOCR initialization failed: {e}")
        return self._easyocr_reader

    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        """Extract text from raw image bytes using pytesseract with EasyOCR fallback."""
        text = ""
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logger.error(f"[OCRService] Failed to load image: {e}")
            raise OCRExtractionError("Unable to open image for OCR")

        # 1. Try pytesseract first
        try:
            import pytesseract
            text = pytesseract.image_to_string(image)
        except Exception as e:
            logger.warning(f"[OCRService] pytesseract failed or not installed: {e}")

        # 2. Try EasyOCR fallback if text is short
        if len(text.strip()) < OCR_MIN_TEXT_LENGTH:
            reader = self._get_easyocr_reader()
            if reader:
                try:
                    results = reader.readtext(image_bytes, detail=0)
                    text = " ".join(results)
                except Exception as e:
                    logger.warning(f"[OCRService] EasyOCR failed: {e}")

        clean_text = text.strip()
        if len(clean_text) < OCR_MIN_TEXT_LENGTH:
            logger.warning(
                f"[OCRService] OCR output below threshold ({len(clean_text)} < {OCR_MIN_TEXT_LENGTH})"
            )
            raise OCRExtractionError(
                "OCR extraction produced insufficient text. Please verify document quality or enter data manually."
            )

        return clean_text

    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF using pypdf/pdf2image + OCR."""
        text = ""

        # 1. First attempt: Direct digital text extraction via pypdf (if digital PDF)
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            logger.debug(f"[OCRService] Direct PDF text extraction failed: {e}")

        # 2. If scanned PDF (little or no digital text), render pages to images and run OCR
        if len(text.strip()) < OCR_MIN_TEXT_LENGTH:
            try:
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(pdf_bytes, first_page=1, last_page=3)
                ocr_texts = []
                for img in images:
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format="PNG")
                    try:
                        page_text = self.extract_text_from_image_bytes(img_byte_arr.getvalue())
                        ocr_texts.append(page_text)
                    except OCRExtractionError:
                        continue
                text = "\n".join(ocr_texts)
            except Exception as e:
                logger.warning(f"[OCRService] pdf2image conversion failed: {e}")

        clean_text = text.strip()
        if len(clean_text) < OCR_MIN_TEXT_LENGTH:
            raise OCRExtractionError(
                "Could not extract sufficient text from PDF. The document may be empty or unreadable."
            )

        return clean_text

    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        """Extract text according to file MIME type."""
        logger.info(f"[OCRService] Extracting text for MIME type: {mime_type}")
        if mime_type == "application/pdf":
            return self.extract_text_from_pdf_bytes(file_bytes)
        elif mime_type in ["image/jpeg", "image/png"]:
            return self.extract_text_from_image_bytes(file_bytes)
        elif mime_type.startswith("text/"):
            return file_bytes.decode("utf-8", errors="ignore")
        else:
            raise UnsupportedFileTypeError(f"Unsupported MIME type: {mime_type}")
