from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
from ..utils.logger import logger


class ImagePreprocessor:
    @staticmethod
    def preprocess(image_bytes: bytes) -> bytes:
        try:
            img = Image.open(BytesIO(image_bytes))
            img = img.convert("L")
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            img = img.filter(ImageFilter.MedianFilter(size=3))
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return image_bytes
