import logging
import os
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
from core.image_processor import ImageProcessor
from utils.async_utils import AsyncImageLoader
import numpy as np
from typing import List, Optional
from config.settings import SETTINGS

logger = logging.getLogger(__name__)

class ImageListWidget(QListWidget):
    """Widget for displaying list of images"""
    
    # Signals
    image_selected = pyqtSignal(str)
    images_loaded = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing ImageListWidget")
        
        self.image_processor = ImageProcessor()
        self.async_loader = AsyncImageLoader()
        self.image_paths = []
        
        self._setup_ui()
        self._setup_connections()
        logger.info("ImageListWidget initialized successfully")
    
    def _setup_ui(self):
        """Setup the UI"""
        logger.debug("Setting up ImageListWidget UI")
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setStyleSheet("""
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { background-color: #0078d4; }
        """)
    
    def _setup_connections(self):
        """Setup signal connections"""
        logger.debug("Setting up ImageListWidget connections")
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.async_loader.image_loaded.connect(self._on_image_loaded)
    
    def load_images(self, directory: Optional[str] = None):
        """Load images from a directory asynchronously, with fallback to default directory"""
        logger.info(f"Loading images from directory: {directory or 'default'}")
        
        # Fallback to default directory if none provided
        if not directory or not os.path.isdir(directory):
            default_dir = os.path.join(SETTINGS['PATHS']['projects_dir'], 'images')
            logger.warning(f"Invalid or no directory provided ({directory}), falling back to: {default_dir}")
            directory = default_dir
        
        # Ensure directory exists
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to access image directory:\n{str(e)}")
            return
        
        # Clear existing images
        self.clear()
        self.image_paths = []
        
        try:
            supported_formats = ['.jpg', '.jpeg', '.png', '.bmp']
            image_files = [file for file in Path(directory).iterdir() if file.suffix.lower() in supported_formats]
            
            if not image_files:
                logger.warning(f"No supported images found in {directory}")
                QMessageBox.information(self, "No Images", f"No supported images found in {directory}.")
                self.images_loaded.emit()
                return
            
            for file in image_files:
                image_path = str(file)
                self.image_paths.append(image_path)
                self.async_loader.load_image(image_path)
            
            logger.debug(f"Found {len(self.image_paths)} images in {directory}")
            
        except Exception as e:
            logger.error(f"Error loading images from {directory}: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load images:\n{str(e)}")
            self.images_loaded.emit()
    
    def _on_image_loaded(self, image_path: str, image: np.ndarray):
        """Handle async image load completion"""
        logger.debug(f"Image loaded: {image_path}")
        if image is not None:
            item = QListWidgetItem(os.path.basename(image_path))
            item.setData(Qt.UserRole, image_path)
            self.addItem(item)
        else:
            logger.warning(f"Failed to load image: {image_path}")
            self.image_paths.remove(image_path)  # Remove invalid image path
        self.images_loaded.emit()
    
    def _on_selection_changed(self):
        """Handle image selection"""
        selected_items = self.selectedItems()
        if selected_items:
            image_path = selected_items[0].data(Qt.UserRole)
            logger.debug(f"Image selected: {image_path}")
            self.image_selected.emit(image_path)
    
    def get_image_paths(self) -> List[str]:
        """Get list of loaded image paths"""
        return self.image_paths.copy()
    
    def setEnabled(self, enabled: bool):
        """Enable or disable the widget"""
        super().setEnabled(enabled)
        logger.debug(f"ImageListWidget enabled: {enabled}")