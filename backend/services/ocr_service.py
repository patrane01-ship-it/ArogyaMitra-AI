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
        self._easyocr_reader_lang = None

    def _get_easyocr_reader(self, lang_code: str = "en"):
        """Lazy load EasyOCR reader (downloads model on first call if not present)."""
        easyocr_lang = {"eng": "en", "hin": "hi", "tam": "ta", "tel": "te"}.get(lang_code, "en")
        if self._easyocr_reader is None or self._easyocr_reader_lang != easyocr_lang:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader(["en", easyocr_lang] if easyocr_lang != "en" else ["en"], gpu=False)
                self._easyocr_reader_lang = easyocr_lang
            except Exception as e:
                logger.warning(f"[OCRService] EasyOCR initialization failed: {e}")
        return self._easyocr_reader

    def auto_detect_language(self, text: str) -> str:
        """Auto-detect language based on Unicode blocks."""
        if not text:
            return 'eng'
        
        counts = {'hin': 0, 'tam': 0, 'tel': 0}
        total_chars = len(text)
        
        for char in text:
            code = ord(char)
            if 0x0900 <= code <= 0x097F:
                counts['hin'] += 1
            elif 0x0B80 <= code <= 0x0BFF:
                counts['tam'] += 1
            elif 0x0C00 <= code <= 0x0C7F:
                counts['tel'] += 1
                
        for lang, count in counts.items():
            if count / total_chars > 0.1:
                return lang
        return 'eng'

    def normalize_param_name(self, name: str, lang: str) -> str:
        """Normalize extracted parameter name to English canonical name."""
        aliases = {
            'hba1c': 'HbA1c',
            'ग्लूकोज': 'Glucose',
            'हीमोग्लोबिन': 'Hemoglobin',
            'क्रिएटिनिन': 'Creatinine',
            'यूरिया': 'Urea',
            'कोलेस्ट्रॉल': 'Cholesterol',
            'हीमोग्लोबिन a1c': 'HbA1c',
            'रक्त शर्करा': 'Glucose'
        }
        clean_name = name.lower().strip()
        return aliases.get(clean_name, name)

    def extract_text_from_image_bytes(self, image_bytes: bytes, language: str = 'eng') -> str:
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
            tesseract_lang = {"eng": "eng", "hin": "hin", "tam": "tam", "tel": "tel"}.get(language, "eng")
            text = pytesseract.image_to_string(image, lang=tesseract_lang)
        except Exception as e:
            logger.warning(f"[OCRService] pytesseract failed or not installed: {e}")

        # 2. Try EasyOCR fallback if text is short
        if len(text.strip()) < OCR_MIN_TEXT_LENGTH:
            reader = self._get_easyocr_reader(language)
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

    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes, language: str = 'eng') -> str:
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
                        page_text = self.extract_text_from_image_bytes(img_byte_arr.getvalue(), language=language)
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

    def extract_text(self, file_bytes: bytes, mime_type: str, language: str = 'eng') -> str:
        """Extract text according to file MIME type."""
        logger.info(f"[OCRService] Extracting text for MIME type: {mime_type} with language: {language}")
        if mime_type == "application/pdf":
            return self.extract_text_from_pdf_bytes(file_bytes, language=language)
        elif mime_type in ["image/jpeg", "image/png"]:
            return self.extract_text_from_image_bytes(file_bytes, language=language)
        elif mime_type.startswith("text/"):
            return file_bytes.decode("utf-8", errors="ignore")
        else:
            raise UnsupportedFileTypeError(f"Unsupported MIME type: {mime_type}")
