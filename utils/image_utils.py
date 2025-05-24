# utils/image_utils.py
import logging
import cv2
import numpy as np
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def convert_to_rgb(image: np.ndarray) -> np.ndarray:
    """Convert image to RGB format"""
    logger.debug("Converting image to RGB")
    try:
        if len(image.shape) == 2:  # Grayscale
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 3:  # BGR
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image
    except Exception as e:
        logger.error(f"Error converting image to RGB: {str(e)}")
        return image

def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize image to 0-1 range"""
    logger.debug("Normalizing image")
    try:
        return cv2.normalize(image, None, 0, 1, cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    except Exception as e:
        logger.error(f"Error normalizing image: {str(e)}")
        return image

def resize_with_aspect(image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    """Resize image maintaining aspect ratio"""
    logger.debug(f"Resizing image to {target_size} with aspect ratio")
    try:
        h, w = image.shape[:2]
        target_w, target_h = target_size
        
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        padded = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        padded[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
        
        return padded
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        return image