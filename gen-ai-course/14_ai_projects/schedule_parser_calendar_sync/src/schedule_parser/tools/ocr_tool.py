from typing import Optional, Tuple
from ..config import settings
from ..utils.logger import logger


class OCRTool:
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            from google.cloud import vision

            if settings.google_application_credentials:
                self.client = vision.ImageAnnotatorClient()
        except Exception as e:
            logger.warning(f"Google Vision not configured: {e}")

    def extract_text(self, image_bytes: bytes) -> Tuple[str, float]:
        if not self.client:
            return self._fallback_extract(image_bytes)
        try:
            from google.cloud import vision

            image = vision.Image(content=image_bytes)
            response = self.client.text_detection(image=image)
            if response.error.message:
                logger.error(f"Vision API error: {response.error.message}")
                return "", 0.0
            texts = response.text_annotations
            if texts:
                confidence = 0.9
                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        confidence = min(confidence, block.confidence)
                return texts[0].description, confidence
            return "", 0.0
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return "", 0.0

    def _fallback_extract(self, image_bytes: bytes) -> Tuple[str, float]:
        logger.warning("Using fallback OCR (pytesseract not available)")
        return "", 0.0
