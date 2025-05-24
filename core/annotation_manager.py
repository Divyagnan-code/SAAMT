import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import cv2

logger = logging.getLogger(__name__)

@dataclass
class BoundingBox:
    """Bounding box annotation"""
    x: float
    y: float
    width: float
    height: float
    class_id: int
    class_name: str
    confidence: float = 1.0
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Segmentation:
    """Segmentation annotation"""
    points: List[Tuple[float, float]]
    class_id: int
    class_name: str
    confidence: float = 1.0
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Classification:
    """Classification annotation"""
    class_id: int
    class_name: str
    confidence: float = 1.0
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ImageAnnotation:
    """Complete image annotation"""
    image_path: str
    image_width: int
    image_height: int
    bounding_boxes: List[BoundingBox]
    segmentations: List[Segmentation]
    classifications: List[Classification]
    is_annotated: bool = False
    created_at: str = ""
    modified_at: str = ""
    
    def to_dict(self):
        return {
            'image_path': self.image_path,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'bounding_boxes': [bb.to_dict() for bb in self.bounding_boxes],
            'segmentations': [seg.to_dict() for seg in self.segmentations],
            'classifications': [cls.to_dict() for cls in self.classifications],
            'is_annotated': self.is_annotated,
            'created_at': self.created_at,
            'modified_at': self.modified_at
        }

class AnnotationManager:
    """Manages all annotation operations"""
    
    def __init__(self):
        self.annotations: Dict[str, ImageAnnotation] = {}
        self.classes: Dict[int, str] = {}
        self.undo_stack: List[Dict] = []
        self.redo_stack: List[Dict] = []
        logger.info("AnnotationManager initialized")
    
    def add_class(self, class_id: int, class_name: str):
        """Add a new class"""
        logger.debug(f"Adding class: {class_id} - {class_name}")
        self.classes[class_id] = class_name
    
    def get_classes(self) -> Dict[int, str]:
        """Get all classes"""
        return self.classes.copy()
    
    def create_annotation(self, image_path: str, width: int, height: int) -> ImageAnnotation:
        """Create new annotation for image"""
        logger.debug(f"Creating annotation for: {image_path}")
        
        annotation = ImageAnnotation(
            image_path=image_path,
            image_width=width,
            image_height=height,
            bounding_boxes=[],
            segmentations=[],
            classifications=[]
        )
        
        self.annotations[image_path] = annotation
        return annotation
    
    def get_annotation(self, image_path: str) -> Optional[ImageAnnotation]:
        """Get annotation for image"""
        return self.annotations.get(image_path)
    
    def add_bounding_box(self, image_path: str, bbox: BoundingBox):
        """Add bounding box to image annotation"""
        logger.debug(f"Adding bounding box to {image_path}: {bbox}")
        
        if image_path not in self.annotations:
            logger.error(f"No annotation found for image: {image_path}")
            return
        
        # Save state for undo
        self._save_state()
        
        self.annotations[image_path].bounding_boxes.append(bbox)
        self.annotations[image_path].is_annotated = True
        self._update_modified_time(image_path)
    
    def remove_bounding_box(self, image_path: str, index: int):
        """Remove bounding box from image annotation"""
        logger.debug(f"Removing bounding box {index} from {image_path}")
        
        if image_path not in self.annotations:
            logger.error(f"No annotation found for image: {image_path}")
            return
        
        # Save state for undo
        self._save_state()
        
        if 0 <= index < len(self.annotations[image_path].bounding_boxes):
            self.annotations[image_path].bounding_boxes.pop(index)
            self._update_modified_time(image_path)
    
    def add_segmentation(self, image_path: str, segmentation: Segmentation):
        """Add segmentation to image annotation"""
        logger.debug(f"Adding segmentation to {image_path}")
        
        if image_path not in self.annotations:
            logger.error(f"No annotation found for image: {image_path}")
            return
        
        # Save state for undo
        self._save_state()
        
        self.annotations[image_path].segmentations.append(segmentation)
        self.annotations[image_path].is_annotated = True
        self._update_modified_time(image_path)
    
    def add_classification(self, image_path: str, classification: Classification):
        """Add classification to image annotation"""
        logger.debug(f"Adding classification to {image_path}: {classification}")
        
        if image_path not in self.annotations:
            logger.error(f"No annotation found for image: {image_path}")
            return
        
        # Save state for undo
        self._save_state()
        
        self.annotations[image_path].classifications.append(classification)
        self.annotations[image_path].is_annotated = True
        self._update_modified_time(image_path)
    
    def undo(self):
        """Undo last operation"""
        if not self.undo_stack:
            logger.debug("Nothing to undo")
            return
        
        logger.debug("Performing undo operation")
        
        # Save current state to redo stack
        current_state = self._get_current_state()
        self.redo_stack.append(current_state)
        
        # Restore previous state
        previous_state = self.undo_stack.pop()
        self._restore_state(previous_state)
    
    def redo(self):
        """Redo last undone operation"""
        if not self.redo_stack:
            logger.debug("Nothing to redo")
            return
        
        logger.debug("Performing redo operation")
        
        # Save current state to undo stack
        current_state = self._get_current_state()
        self.undo_stack.append(current_state)
        
        # Restore next state
        next_state = self.redo_stack.pop()
        self._restore_state(next_state)
    
    def save_annotations(self, file_path: str, format_type: str = 'JSON'):
        """Save annotations to file"""
        logger.info(f"Saving annotations to {file_path} in {format_type} format")
        
        try:
            if format_type.upper() == 'JSON':
                self._save_json(file_path)
            elif format_type.upper() == 'COCO':
                self._save_coco(file_path)
            elif format_type.upper() == 'YOLO':
                self._save_yolo(file_path)
            else:
                logger.error(f"Unsupported format: {format_type}")
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"Failed to save annotations: {str(e)}")
            raise
    
    def load_annotations(self, file_path: str, format_type: str = 'JSON'):
        """Load annotations from file"""
        logger.info(f"Loading annotations from {file_path} in {format_type} format")
        
        try:
            if format_type.upper() == 'JSON':
                self._load_json(file_path)
            elif format_type.upper() == 'COCO':
                self._load_coco(file_path)
            elif format_type.upper() == 'YOLO':
                self._load_yolo(file_path)
            else:
                logger.error(f"Unsupported format: {format_type}")
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"Failed to load annotations: {str(e)}")
            raise
    
    def get_annotated_images(self) -> List[str]:
        """Get list of annotated images"""
        return [path for path, annotation in self.annotations.items() 
                if annotation.is_annotated]
    
    def get_unannotated_images(self) -> List[str]:
        """Get list of unannotated images"""
        return [path for path, annotation in self.annotations.items() 
                if not annotation.is_annotated]
    
    def get_annotation_stats(self) -> Dict:
        """Get annotation statistics"""
        total_images = len(self.annotations)
        annotated_images = len(self.get_annotated_images())
        unannotated_images = len(self.get_unannotated_images())
        
        total_bboxes = sum(len(ann.bounding_boxes) for ann in self.annotations.values())
        total_segmentations = sum(len(ann.segmentations) for ann in self.annotations.values())
        total_classifications = sum(len(ann.classifications) for ann in self.annotations.values())
        
        stats = {
            'total_images': total_images,
            'annotated_images': annotated_images,
            'unannotated_images': unannotated_images,
            'completion_rate': (annotated_images / total_images * 100) if total_images > 0 else 0,
            'total_bounding_boxes': total_bboxes,
            'total_segmentations': total_segmentations,
            'total_classifications': total_classifications
        }
        
        logger.debug(f"Annotation stats: {stats}")
        return stats
    
    def _save_state(self):
        """Save current state for undo functionality"""
        from config.settings import SETTINGS
        
        current_state = self._get_current_state()
        self.undo_stack.append(current_state)
        
        # Limit undo stack size
        max_undo_steps = SETTINGS['UI']['max_undo_steps']
        if len(self.undo_stack) > max_undo_steps:
            self.undo_stack.pop(0)
        
        # Clear redo stack when new action is performed
        self.redo_stack.clear()
    
    def _get_current_state(self) -> Dict:
        """Get current state for undo/redo"""
        return {
            'annotations': {path: ann.to_dict() for path, ann in self.annotations.items()},
            'classes': self.classes.copy()
        }
    
    def _restore_state(self, state: Dict):
        """Restore state from undo/redo"""
        self.classes = state['classes'].copy()
        self.annotations.clear()
        
        for path, ann_dict in state['annotations'].items():
            annotation = self._dict_to_annotation(ann_dict)
            self.annotations[path] = annotation
    
    def _dict_to_annotation(self, ann_dict: Dict) -> ImageAnnotation:
        """Convert dictionary to ImageAnnotation object"""
        bboxes = [BoundingBox(**bbox) for bbox in ann_dict['bounding_boxes']]
        segmentations = [Segmentation(**seg) for seg in ann_dict['segmentations']]
        classifications = [Classification(**cls) for cls in ann_dict['classifications']]
        
        return ImageAnnotation(
            image_path=ann_dict['image_path'],
            image_width=ann_dict['image_width'],
            image_height=ann_dict['image_height'],
            bounding_boxes=bboxes,
            segmentations=segmentations,
            classifications=classifications,
            is_annotated=ann_dict['is_annotated'],
            created_at=ann_dict.get('created_at', ''),
            modified_at=ann_dict.get('modified_at', '')
        )
    
    def _update_modified_time(self, image_path: str):
        """Update modification time for annotation"""
        from datetime import datetime
        if image_path in self.annotations:
            self.annotations[image_path].modified_at = datetime.now().isoformat()
    
    def _save_json(self, file_path: str):
        """Save annotations in JSON format"""
        data = {
            'classes': self.classes,
            'annotations': {path: ann.to_dict() for path, ann in self.annotations.items()}
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_json(self, file_path: str):
        """Load annotations from JSON format"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.classes = data.get('classes', {})
        # Convert string keys back to int for classes
        self.classes = {int(k): v for k, v in self.classes.items()}
        
        self.annotations.clear()
        for path, ann_dict in data.get('annotations', {}).items():
            annotation = self._dict_to_annotation(ann_dict)
            self.annotations[path] = annotation
    
    def _save_coco(self, file_path: str):
        """Save annotations in COCO format"""
        # Implementation for COCO format
        logger.info("COCO format save not yet implemented")
        pass
    
    def _load_coco(self, file_path: str):
        """Load annotations from COCO format"""
        # Implementation for COCO format
        logger.info("COCO format load not yet implemented")
        pass
    
    def _save_yolo(self, file_path: str):
        """Save annotations in YOLO format"""
        # Implementation for YOLO format
        logger.info("YOLO format save not yet implemented")
        pass
    
    def _load_yolo(self, file_path: str):
        """Load annotations from YOLO format"""
        # Implementation for YOLO format
        logger.info("YOLO format load not yet implemented")
        pass