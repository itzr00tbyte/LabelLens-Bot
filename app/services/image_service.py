from io import BytesIO
import math

import cv2
import numpy as np
from PIL import Image, ImageOps


class ImageProcessingService:
    @staticmethod
    def load_image(image_bytes: bytes) -> Image.Image:
        image = Image.open(BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image

    @staticmethod
    def resize_max_dim(image: Image.Image, max_dim: int = 2400) -> Image.Image:
        width, height = image.size
        if max(width, height) <= max_dim:
            return image
        
        ratio = max_dim / float(max(width, height))
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    @staticmethod
    def preprocess_for_ocr(image: Image.Image) -> np.ndarray:
        """
        Preprocesses a PIL image for optimal Tesseract OCR performance.
        Includes contrast enhancement, noise reduction, and adaptive thresholding.
        """
        # Convert PIL Image to OpenCV BGR then Grayscale
        img_np = np.array(image)
        if len(img_np.shape) == 3 and img_np.shape[2] == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        elif len(img_np.shape) == 3 and img_np.shape[2] == 4:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGBA2GRAY)
        else:
            gray = img_np.copy()

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Contrast enhancement with CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Deskew image if angle is detected
        deskewed = ImageProcessingService._deskew(enhanced)

        # Adaptive Thresholding
        thresh = cv2.adaptiveThreshold(
            deskewed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
        )

        return thresh

    @staticmethod
    def _deskew(image_gray: np.ndarray) -> np.ndarray:
        coords = np.column_stack(np.where(image_gray < 200))
        if len(coords) < 100:
            return image_gray

        angle = 0.0
        try:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
        except Exception:
            return image_gray

        if abs(angle) < 0.5 or abs(angle) > 45:
            return image_gray

        (h, w) = image_gray.shape[:2]
        center = (w // 2, h // 2)
        m = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image_gray, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        return rotated
