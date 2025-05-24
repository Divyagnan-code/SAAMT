# core/image_processor.py
import cv2
import numpy as np
import logging
from typing import Tuple, List, Optional, Dict
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles image processing operations"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"ImageProcessor initialized with {max_workers} workers")
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load image from path"""
        logger.debug(f"Loading image: {image_path}")
        
        try:
            if not Path(image_path).exists():
                logger.error(f"Image file not found: {image_path}")
                return None
            
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            logger.debug(f"Image loaded successfully: {image.shape}")
            return image
            
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {str(e)}")
            return None
    
    def load_image_async(self, image_path: str, callback=None):
        """Load image asynchronously"""
        logger.debug(f"Loading image asynchronously: {image_path}")
        
        def load_task():
            image = self.load_image(image_path)
            if callback:
                callback(image_path, image)
            return image
        
        future = self.executor.submit(load_task)
        return future
    
    def resize_image(self, image: np.ndarray, target_size: Tuple[int, int], 
                    maintain_aspect: bool = True) -> np.ndarray:
        """Resize image to target size"""
        logger.debug(f"Resizing image from {image.shape[:2]} to {target_size}")
        
        try:
            if maintain_aspect:
                # Calculate scaling factor
                h, w = image.shape[:2]
                target_w, target_h = target_size
                
                scale = min(target_w / w, target_h / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                
                # Resize image
                resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                
                # Create padded image
                padded = np.zeros((target_h, target_w, 3), dtype=np.uint8)
                y_offset = (target_h - new_h) // 2
                x_offset = (target_w - new_w) // 2
                padded[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
                
                return padded
            else:
                return cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)
                
        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
            return image
    
    def get_image_info(self, image_path: str) -> Optional[Dict]:
        """Get image information"""
        logger.debug(f"Getting image info: {image_path}")
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) > 2 else 1
            file_size = Path(image_path).stat().st_size
            
            info = {
                'path': image_path,
                'width': width,
                'height': height,
                'channels': channels,
                'file_size': file_size,
                'format': Path(image_path).suffix.lower()
            }
            
            logger.debug(f"Image info: {info}")
            return info
            
        except Exception as e:
            logger.error(f"Error getting image info for {image_path}: {str(e)}")
            return None
    
    def convert_coordinates(self, coords: List[Tuple[float, float]], 
                          from_size: Tuple[int, int], to_size: Tuple[int, int]) -> List[Tuple[float, float]]:
        """Convert coordinates between different image sizes"""
        logger.debug(f"Converting coordinates from {from_size} to {to_size}")
        
        try:
            from_w, from_h = from_size
            to_w, to_h = to_size
            
            scale_x = to_w / from_w
            scale_y = to_h / from_h
            
            converted_coords = []
            for x, y in coords:
                new_x = x * scale_x
                new_y = y * scale_y
                converted_coords.append((new_x, new_y))
            
            return converted_coords
            
        except Exception as e:
            logger.error(f"Error converting coordinates: {str(e)}")
            return coords
    
    def apply_preprocessing(self, image: np.ndarray, operations: List[str]) -> np.ndarray:
        """Apply preprocessing operations to image"""
        logger.debug(f"Applying preprocessing: {operations}")
        
        processed_image = image.copy()
        
        try:
            for operation in operations:
                if operation == 'normalize':
                    processed_image = cv2.normalize(processed_image, None, 0, 255, cv2.NORM_MINMAX)
                elif operation == 'grayscale':
                    processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
                    processed_image = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2BGR)
                elif operation == 'blur':
                    processed_image = cv2.GaussianBlur(processed_image, (5, 5), 0)
                elif operation == 'sharpen':
                    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                    processed_image = cv2.filter2D(processed_image, -1, kernel)
                elif operation == 'histogram_equalization':
                    if len(processed_image.shape) == 3:
                        processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2YUV)
                        processed_image[:,:,0] = cv2.equalizeHist(processed_image[:,:,0])
                        processed_image = cv2.cvtColor(processed_image, cv2.COLOR_YUV2BGR)
                    else:
                        processed_image = cv2.equalizeHist(processed_image)
                
            return processed_image
            
        except Exception as e:
            logger.error(f"Error applying preprocessing: {str(e)}")
            return image
    
    def extract_roi(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract region of interest from image"""
        logger.debug(f"Extracting ROI: {bbox}")
        
        try:
            x, y, w, h = bbox
            roi = image[y:y+h, x:x+w]
            return roi
            
        except Exception as e:
            logger.error(f"Error extracting ROI: {str(e)}")
            return image
    
    def batch_process_images(self, image_paths: List[str], operation_func, callback=None):
        """Process multiple images in batch"""
        logger.info(f"Batch processing {len(image_paths)} images")
        
        def process_batch():
            results = []
            for i, image_path in enumerate(image_paths):
                try:
                    result = operation_func(image_path)
                    results.append(result)
                    
                    if callback:
                        progress = (i + 1) / len(image_paths) * 100
                        callback(progress, image_path, result)
                        
                except Exception as e:
                    logger.error(f"Error processing {image_path}: {str(e)}")
                    results.append(None)
            
            return results
        
        future = self.executor.submit(process_batch)
        return future
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up ImageProcessor")
        self.executor.shutdown(wait=True)