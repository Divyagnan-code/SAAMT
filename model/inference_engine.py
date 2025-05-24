# models/inference_engine.py
import os
import logging
import importlib
from typing import Dict, List, Optional, Any
import numpy as np
import torch
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger(__name__)

class InferenceEngine:
    """Manages model loading and inference"""
    
    def __init__(self, models_dir: str, device: str = 'auto'):
        self.models_dir = Path(models_dir)
        self.device = self._determine_device(device)
        self.loaded_models: Dict[str, Any] = {}
        self.model_configs: Dict[str, Dict] = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        logger.info(f"InferenceEngine initialized with device: {self.device}")
        self._discover_models()
    
    def _determine_device(self, device: str) -> str:
        """Determine the best device to use"""
        if device == 'auto':
            if torch.cuda.is_available():
                device = 'cuda'
                logger.info("CUDA available, using GPU")
            else:
                device = 'cpu'
                logger.info("CUDA not available, using CPU")
        
        logger.info(f"Using device: {device}")
        return device
    
    def _discover_models(self):
        """Discover available models in models directory"""
        logger.info("Discovering available models")
        
        try:
            if not self.models_dir.exists():
                logger.warning(f"Models directory not found: {self.models_dir}")
                return
            
            for model_dir in self.models_dir.iterdir():
                if model_dir.is_dir():
                    config_file = model_dir / "config.json"
                    if config_file.exists():
                        try:
                            import json
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                            
                            self.model_configs[model_dir.name] = config
                            logger.debug(f"Discovered model: {model_dir.name}")
                            
                        except Exception as e:
                            logger.error(f"Failed to load config for {model_dir.name}: {e}")
                            
        except Exception as e:
            logger.error(f"Error discovering models: {e}")
    
    def get_available_models(self) -> Dict[str, Dict]:
        """Get list of available models"""
        return self.model_configs.copy()
    
    def load_model(self, model_name: str) -> bool:
        """Load a model"""
        logger.info(f"Loading model: {model_name}")
        
        if model_name in self.loaded_models:
            logger.info(f"Model {model_name} already loaded")
            return True
        
        if model_name not in self.model_configs:
            logger.error(f"Model {model_name} not found in available models")
            return False
        
        try:
            config = self.model_configs[model_name]
            model_type = config.get('type', 'detection')
            model_path = self.models_dir / model_name / config.get('model_file', 'model.pt')
            
            if model_type == 'detection':
                model = self._load_detection_model(model_path, config)
            elif model_type == 'segmentation':
                model = self._load_segmentation_model(model_path, config)
            elif model_type == 'classification':
                model = self._load_classification_model(model_path, config)
            else:
                logger.error(f"Unsupported model type: {model_type}")
                return False
            
            self.loaded_models[model_name] = model
            logger.info(f"Model {model_name} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {str(e)}")
            return False
    
    def unload_model(self, model_name: str):
        """Unload a model"""
        logger.info(f"Unloading model: {model_name}")
        
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            # Force garbage collection
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"Model {model_name} unloaded")
    
    def predict(self, model_name: str, image: np.ndarray, **kwargs) -> Optional[Dict]:
        """Make prediction using specified model"""
        logger.debug(f"Making prediction with model: {model_name}")
        
        if model_name not in self.loaded_models:
            logger.error(f"Model {model_name} not loaded")
            return None
        
        try:
            model = self.loaded_models[model_name]
            result = model.predict(image, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for model {model_name}: {str(e)}")
            return None
    
    def predict_async(self, model_name: str, image: np.ndarray, callback=None, **kwargs) -> Future:
        """Make asynchronous prediction"""
        logger.debug(f"Making async prediction with model: {model_name}")
        
        def predict_task():
            result = self.predict(model_name, image, **kwargs)
            if callback:
                callback(result)
            return result
        
        future = self.executor.submit(predict_task)
        return future
    
    def batch_predict(self, model_name: str, images: List[np.ndarray], 
                     progress_callback=None, **kwargs) -> List[Optional[Dict]]:
        """Make batch predictions"""
        logger.info(f"Making batch prediction with model: {model_name}, {len(images)} images")
        
        if model_name not in self.loaded_models:
            logger.error(f"Model {model_name} not loaded")
            return [None] * len(images)
        
        results = []
        
        try:
            for i, image in enumerate(images):
                result = self.predict(model_name, image, **kwargs)
                results.append(result)
                
                if progress_callback:
                    progress = (i + 1) / len(images) * 100
                    progress_callback(progress, i, result)
                    
                logger.debug(f"Processed image {i+1}/{len(images)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch prediction failed: {str(e)}")
            return [None] * len(images)
    
    def _load_detection_model(self, model_path: Path, config: Dict):
        """Load detection model"""        
        logger.debug(f"Loading detection model from {model_path}")
        
        # This is a placeholder - implement actual model loading based on your model format
        class MockDetectionModel:
            def __init__(self, model_path, config, device):
                self.model_path = model_path
                self.config = config
                self.device = device
                self.classes = config.get('classes', [])
                
            def predict(self, image, confidence_threshold=0.5, iou_threshold=0.4):
                # Mock prediction - replace with actual model inference
                h, w = image.shape[:2]
                return {
                    'bounding_boxes': [
                        {
                            'x': 100, 'y': 100, 'width': 200, 'height': 150,
                            'class_id': 0, 'class_name': 'object',
                            'confidence': 0.8
                        }
                    ]
                }
        
        return MockDetectionModel(model_path, config, self.device)
    
    def _load_segmentation_model(self, model_path: Path, config: Dict):
        """Load segmentation model"""
        logger.debug(f"Loading segmentation model from {model_path}")
        
        # This is a placeholder - implement actual model loading
        class MockSegmentationModel:
            def __init__(self, model_path, config, device):
                self.model_path = model_path
                self.config = config
                self.device = device
                self.classes = config.get('classes', [])
                
            def predict(self, image, **kwargs):
                # Mock prediction - replace with actual model inference
                return {
                    'masks': [
                        {
                            'points': [(100, 100), (200, 100), (200, 200), (100, 200)],
                            'class_id': 0, 'class_name': 'object',
                            'confidence': 0.8
                        }
                    ]
                }
        
        return MockSegmentationModel(model_path, config, self.device)
    
    def _load_classification_model(self, model_path: Path, config: Dict):
        """Load classification model"""
        logger.debug(f"Loading classification model from {model_path}")
        
        # This is a placeholder - implement actual model loading
        class MockClassificationModel:
            def __init__(self, model_path, config, device):
                self.model_path = model_path
                self.config = config
                self.device = device
                self.classes = config.get('classes', [])
                
            def predict(self, image, top_k=5):
                # Mock prediction - replace with actual model inference
                return {
                    'classes': [
                        {'class_id': 0, 'class_name': 'cat', 'confidence': 0.9},
                        {'class_id': 1, 'class_name': 'dog', 'confidence': 0.1}
                    ]
                }
        
        return MockClassificationModel(model_path, config, self.device)
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up InferenceEngine")
        
        # Unload all models
        for model_name in list(self.loaded_models.keys()):
            self.unload_model(model_name)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)