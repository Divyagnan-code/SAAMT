# utils/async_utils.py
import logging
from PyQt5.QtCore import QObject, pyqtSignal
from core.image_processor import ImageProcessor
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)

class AsyncImageLoader(QObject):
    """Asynchronous image loader"""
    
    # Signals
    image_loaded = pyqtSignal(str, np.ndarray)
    
    def __init__(self, max_workers: int = 4):
        super().__init__()
        logger.info("Initializing AsyncImageLoader")
        self.image_processor = ImageProcessor(max_workers=max_workers)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info("AsyncImageLoader initialized successfully")
    
    def load_image(self, image_path: str):
        """Load image asynchronously"""
        logger.debug(f"Submitting async load for {image_path}")
        self.executor.submit(self._load_image_task, image_path)
    
    def _load_image_task(self, image_path: str):
        """Task to load image"""
        logger.debug(f"Loading image async: {image_path}")
        try:
            image = self.image_processor.load_image(image_path)
            if image is not None:
                self.image_loaded.emit(image_path, image)
            else:
                logger.error(f"Failed to load image: {image_path}")
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {str(e)}")
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up AsyncImageLoader")
        self.executor.shutdown(wait=True)