# ui/annotation_widget.py
import logging
import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from typing import Optional, List, Tuple
from core.annotation_manager import AnnotationManager, BoundingBox, Segmentation, Classification
from core.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class AnnotationWidget(QWidget):
    """Widget for displaying and annotating images"""
    
    # Signals
    annotation_added = pyqtSignal(dict)
    annotation_removed = pyqtSignal(int)
    annotation_modified = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing AnnotationWidget")
        
        self.image_processor = ImageProcessor()
        self.annotation_manager = AnnotationManager()
        self.current_image = None
        self.current_image_path = None
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.pixmap_item = None
        self.current_tool = "select"  # select, bbox, segmentation, classification
        self.current_class = (0, "default")
        self.drawing = False
        self.start_point = None
        self.current_bbox = None
        self.current_segmentation = []
        
        self._setup_ui()
        logger.info("AnnotationWidget initialized successfully")
    
    def _setup_ui(self):
        """Setup the UI layout"""
        logger.debug("Setting up AnnotationWidget UI")
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setMouseTracking(True)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Connect mouse events
        self.view.mousePressEvent = self._mouse_press_event
        self.view.mouseMoveEvent = self._mouse_move_event
        self.view.mouseReleaseEvent = self._mouse_release_event
    
    def set_image(self, image_path: str):
        """Set the image to annotate"""
        logger.debug(f"Setting image: {image_path}")
        try:
            image = self.image_processor.load_image(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return
            
            self.current_image = image
            self.current_image_path = image_path
            height, width = image.shape[:2]
            
            # Convert to QImage
            qimage = QImage(image.data, width, height, 3 * width, QImage.Format_RGB888)
            qimage = qimage.rgbSwapped()
            pixmap = QPixmap.fromImage(qimage)
            
            # Update scene
            if self.pixmap_item:
                self.scene.removeItem(self.pixmap_item)
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.pixmap_item)
            self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
            
            # Create or load annotation
            if not self.annotation_manager.get_annotation(image_path):
                self.annotation_manager.create_annotation(image_path, width, height)
            
            self._update_annotations()
            logger.debug(f"Image set successfully: {image_path}")
            
        except Exception as e:
            logger.error(f"Error setting image {image_path}: {str(e)}")
    
    def set_tool(self, tool: str):
        """Set the current annotation tool"""
        logger.debug(f"Setting tool: {tool}")
        self.current_tool = tool
        self.drawing = False
        self.start_point = None
        self.current_segmentation = []
    
    def set_class(self, class_id: int, class_name: str):
        """Set the current class for annotation"""
        logger.debug(f"Setting class: {class_id} - {class_name}")
        self.current_class = (class_id, class_name)
        self.annotation_manager.add_class(class_id, class_name)
    
    def _mouse_press_event(self, event):
        """Handle mouse press events"""
        if not self.current_image_path:
            return
        
        pos = self.view.mapToScene(event.pos())
        x, y = pos.x(), pos.y()
        
        logger.debug(f"Mouse press at ({x}, {y}) with tool {self.current_tool}")
        
        if self.current_tool == "bbox" and event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = QPointF(x, y)
            self.current_bbox = self.scene.addRect(QRectF(self.start_point, self.start_point))
            pen = QPen(QColor(0, 255, 0), 2, Qt.DashLine)
            self.current_bbox.setPen(pen)
        
        elif self.current_tool == "segmentation" and event.button() == Qt.LeftButton:
            self.drawing = True
            self.current_segmentation.append((x, y))
            if len(self.current_segmentation) > 1:
                self._draw_segmentation()
    
    def _mouse_move_event(self, event):
        """Handle mouse move events"""
        if not self.current_image_path or not self.drawing:
            return
        
        pos = self.view.mapToScene(event.pos())
        x, y = pos.x(), pos.y()
        
        logger.debug(f"Mouse move to ({x}, {y})")
        
        if self.current_tool == "bbox" and self.current_bbox:
            rect = QRectF(self.start_point, QPointF(x, y)).normalized()
            self.current_bbox.setRect(rect)
    
    def _mouse_release_event(self, event):
        """Handle mouse release events"""
        if not self.current_image_path or not self.drawing:
            return
        
        pos = self.view.mapToScene(event.pos())
        x, y = pos.x(), pos.y()
        
        logger.debug(f"Mouse release at ({x}, {y})")
        
        if self.current_tool == "bbox" and self.current_bbox:
            rect = self.current_bbox.rect().normalized()
            if rect.width() > 5 and rect.height() > 5:  # Minimum size check
                bbox = BoundingBox(
                    x=rect.x(),
                    y=rect.y(),
                    width=rect.width(),
                    height=rect.height(),
                    class_id=self.current_class[0],
                    class_name=self.current_class[1]
                )
                self.annotation_manager.add_bounding_box(self.current_image_path, bbox)
                self.annotation_added.emit(bbox.to_dict())
            
            self.scene.removeItem(self.current_bbox)
            self.current_bbox = None
            self.drawing = False
            self._update_annotations()
        
        elif self.current_tool == "segmentation":
            if event.button() == Qt.RightButton:  # Finish segmentation
                if len(self.current_segmentation) >= 3:
                    segmentation = Segmentation(
                        points=self.current_segmentation,
                        class_id=self.current_class[0],
                        class_name=self.current_class[1]
                    )
                    self.annotation_manager.add_segmentation(self.current_image_path, segmentation)
                    self.annotation_added.emit(segmentation.to_dict())
                
                self.current_segmentation = []
                self.drawing = False
                self._update_annotations()
    
    def _draw_segmentation(self):
        """Draw current segmentation points"""
        logger.debug("Drawing segmentation")
        # Clear previous segmentation drawings
        for item in self.scene.items():
            if isinstance(item, QGraphicsPolygonItem):
                self.scene.removeItem(item)
        
        if len(self.current_segmentation) > 1:
            points = [QPointF(x, y) for x, y in self.current_segmentation]
            polygon = self.scene.addPolygon(points, QPen(QColor(0, 255, 0), 2), QBrush(QColor(0, 255, 0, 50)))
    
    def _update_annotations(self):
        """Update displayed annotations"""
        logger.debug("Updating annotations display")
        
        # Clear previous annotations
        for item in self.scene.items():
            if isinstance(item, (QGraphicsRectItem, QGraphicsPolygonItem)):
                self.scene.removeItem(item)
        
        annotation = self.annotation_manager.get_annotation(self.current_image_path)
        if not annotation:
            return
        
        # Draw bounding boxes
        for bbox in annotation.bounding_boxes:
            rect = QRectF(bbox.x, bbox.y, bbox.width, bbox.height)
            pen = QPen(QColor(0, 255, 0), 2)
            brush = QBrush(QColor(0, 255, 0, 50))
            self.scene.addRect(rect, pen, brush)
        
        # Draw segmentations
        for seg in annotation.segmentations:
            points = [QPointF(x, y) for x, y in seg.points]
            pen = QPen(QColor(0, 0, 255), 2)
            brush = QBrush(QColor(0, 0, 255, 50))
            self.scene.addPolygon(points, pen, brush)
    
    def auto_annotate(self, model_name: str, threshold: float):
        """Perform auto-annotation on current image"""
        logger.info(f"Auto-annotating image {self.current_image_path} with model {model_name}")
        try:
            from models.inference_engine import InferenceEngine
            inference_engine = InferenceEngine(SETTINGS['PATHS']['models_dir'])
            if not inference_engine.load_model(model_name):
                logger.error(f"Failed to load model {model_name}")
                return
            
            result = inference_engine.predict(model_name, self.current_image, 
                                           confidence_threshold=threshold)
            if result:
                for bbox in result.get('bounding_boxes', []):
                    if bbox['confidence'] >= threshold:
                        annotation_bbox = BoundingBox(
                            x=bbox['x'],
                            y=bbox['y'],
                            width=bbox['width'],
                            height=bbox['height'],
                            class_id=bbox['class_id'],
                            class_name=bbox['class_name'],
                            confidence=bbox['confidence']
                        )
                        self.annotation_manager.add_bounding_box(self.current_image_path, annotation_bbox)
                
                for mask in result.get('masks', []):
                    if mask['confidence'] >= threshold:
                        segmentation = Segmentation(
                            points=mask['points'],
                            class_id=mask['class_id'],
                            class_name=mask['class_name'],
                            confidence=mask['confidence']
                        )
                        self.annotation_manager.add_segmentation(self.current_image_path, segmentation)
                
                for cls in result.get('classes', []):
                    if cls['confidence'] >= threshold:
                        classification = Classification(
                            class_id=cls['class_id'],
                            class_name=cls['class_name'],
                            confidence=cls['confidence']
                        )
                        self.annotation_manager.add_classification(self.current_image_path, classification)
                
                self.annotation_updated.emit()
                self._update_annotations()
                logger.info("Auto-annotation completed")
                
        except Exception as e:
            logger.error(f"Auto-annotation failed: {str(e)}")
    
    def setEnabled(self, enabled: bool):
        """Enable or disable the widget"""
        super().setEnabled(enabled)
        logger.debug(f"AnnotationWidget enabled: {enabled}")