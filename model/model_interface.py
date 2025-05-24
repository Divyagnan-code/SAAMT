# models/model_interface.py
import abc
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

class ModelInterface(abc.ABC):
    """Abstract base class for all models"""
    
    def __init__(self, model_path: str, device: str = 'cpu'):
        self.model_path = model_path
        self.device = device
        self.is_loaded = False
        self.model_info = {}
        logger.info(f"ModelInterface initialized: {model_path}")
    
    @abc.abstractmethod
    def load_model(self):
        """Load the model"""
        pass
    
    @abc.abstractmethod
    def predict(self, image: np.ndarray, **kwargs) -> Dict[str, Any]:
        """Make prediction on image"""
        pass
    
    @abc.abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass
    
    def unload_model(self):
        """Unload the model"""
        logger.info(f"Unloading model: {self.model_path}")
        self.is_loaded = False

class DetectionModel(ModelInterface):
    """Object detection model interface"""
    
    def predict_bounding_boxes(self, image: np.ndarray, confidence_threshold: float = 0.5,
                             iou_threshold: float = 0.4) -> List[Dict]:
        """Predict bounding boxes"""
        logger.debug(f"Predicting bounding boxes with confidence={confidence_threshold}, iou={iou_threshold}")
        
        prediction = self.predict(image, confidence_threshold=confidence_threshold, iou_threshold=iou_threshold)
        return prediction.get('bounding_boxes', [])

class SegmentationModel(ModelInterface):
    """Segmentation model interface"""
    
    def predict_masks(self, image: np.ndarray, **kwargs) -> List[Dict]:
        """Predict segmentation masks"""
        logger.debug("Predicting segmentation masks")
        
        prediction = self.predict(image, **kwargs)
        return prediction.get('masks', [])

class ClassificationModel(ModelInterface):
    """Classification model interface"""
    
    def predict_classes(self, image: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Predict image classes"""
        logger.debug(f"Predicting classes with top_k={top_k}")
        
        prediction = self.predict(image, top_k=top_k)
        return prediction.get('classes', [])