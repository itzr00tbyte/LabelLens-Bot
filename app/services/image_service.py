import os
from io import BytesIO
import cv2
import numpy as np
from PIL import Image, ImageOps

from app.config import settings


class ImageProcessingService:
    @staticmethod
    def load_image(image_bytes: bytes) -> Image.Image:
        """Loads image from raw bytes, corrects EXIF orientation, and converts to RGB."""
        image = Image.open(BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image

    @staticmethod
    def resize_max_dim(image: Image.Image, max_dim: int = 2400) -> Image.Image:
        """Rescales high-res image proportionally so max dimension does not exceed max_dim."""
        width, height = image.size
        if max(width, height) <= max_dim:
            return image
        ratio = max_dim / float(max(width, height))
        return image.resize((int(width * ratio), int(height * ratio)), Image.Resampling.LANCZOS)

    @staticmethod
    def detect_and_crop_document(img_np: np.ndarray) -> np.ndarray:
        """Detects document boundary contours and crops to bounding polygon if valid."""
        try:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 50, 200)

            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

            for c in contours:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                if len(approx) == 4 and cv2.contourArea(c) > (img_np.shape[0] * img_np.shape[1] * 0.25):
                    # Found document quad contour
                    pts = approx.reshape(4, 2)
                    rect = ImageProcessingService._order_points(pts)
                    (tl, tr, br, bl) = rect

                    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                    max_width = max(int(width_a), int(width_b))

                    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
                    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
                    max_height = max(int(height_a), int(height_b))

                    dst = np.array([
                        [0, 0],
                        [max_width - 1, 0],
                        [max_width - 1, max_height - 1],
                        [0, max_height - 1]
                    ], dtype="float32")

                    M = cv2.getPerspectiveTransform(rect, dst)
                    warped = cv2.warpPerspective(img_np, M, (max_width, max_height))
                    return warped
        except Exception:
            pass

        return img_np

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    @staticmethod
    def deskew(image_gray: np.ndarray) -> np.ndarray:
        """Corrects text skew angle using minAreaRect on dark pixels."""
        coords = np.column_stack(np.where(image_gray < 200))
        if len(coords) < 100:
            return image_gray
        try:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            angle = -(90 + angle) if angle < -45 else -angle
        except Exception:
            return image_gray

        if abs(angle) < 0.5 or abs(angle) > 45:
            return image_gray

        (h, w) = image_gray.shape[:2]
        m = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        return cv2.warpAffine(image_gray, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    @staticmethod
    def preprocess_for_ocr(image: Image.Image) -> np.ndarray:
        """Applies non-destructive OCR preprocessing: CLAHE, denoising, deskew, and adaptive thresholding."""
        img_np = np.array(image)
        if len(img_np.shape) == 3 and img_np.shape[2] == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        elif len(img_np.shape) == 3 and img_np.shape[2] == 4:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGBA2GRAY)
        else:
            gray = img_np.copy()

        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        deskewed = ImageProcessingService.deskew(enhanced)
        return cv2.adaptiveThreshold(deskewed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8)

    @staticmethod
    def save_processed_image(processed_np: np.ndarray, document_id: str) -> str:
        """Saves processed image to storage/processed/{doc_id}_processed.png."""
        os.makedirs(os.path.join(settings.STORAGE_DIR, "processed"), exist_ok=True)
        target_path = os.path.join(settings.STORAGE_DIR, "processed", f"{document_id}_processed.png")
        cv2.imwrite(target_path, processed_np)
        return target_path
