# ui/tools_panel.py
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QSlider, QLabel, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal
from config.settings import SETTINGS

logger = logging.getLogger(__name__)

class ToolsPanel(QWidget):
    """Panel for annotation tools and settings"""
    
    # Signals
    tool_changed = pyqtSignal(str)
    class_changed = pyqtSignal(int, str)
    threshold_changed = pyqtSignal(float)
    auto_annotate_requested = pyqtSignal(str, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing ToolsPanel")
        
        self.current_tool = "select"
        self.current_class_id = 0
        self.current_class_name = "default"
        self.threshold = SETTINGS['MODELS']['default_confidence_threshold']
        
        self._setup_ui()
        self._setup_connections()
        logger.info("ToolsPanel initialized successfully")
    
    def _setup_ui(self):
        """Setup the UI layout"""
        logger.debug("Setting up ToolsPanel UI")
        layout = QVBoxLayout()
        
        # Tool selection
        self.tool_combo = QComboBox()
        self.tool_combo.addItems(["Select", "Bounding Box", "Segmentation", "Classification"])
        layout.addWidget(QLabel("Annotation Tool:"))
        layout.addWidget(self.tool_combo)
        
        # Class selection
        self.class_combo = QComboBox()
        self.class_combo.addItem("default")
        layout.addWidget(QLabel("Class:"))
        layout.addWidget(self.class_combo)
        
        # Add new class
        self.new_class_input = QLineEdit()
        self.new_class_input.setPlaceholderText("Enter new class name")
        self.add_class_button = QPushButton("Add Class")
        layout.addWidget(self.new_class_input)
        layout.addWidget(self.add_class_button)
        
        # Threshold slider
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(int(self.threshold * 100))
        self.threshold_label = QLabel(f"Confidence Threshold: {self.threshold:.2f}")
        layout.addWidget(self.threshold_label)
        layout.addWidget(self.threshold_slider)
        
        # Auto-annotate button
        self.auto_annotate_button = QPushButton("Auto-Annotate")
        layout.addWidget(self.auto_annotate_button)
        
        # Model selection
        self.model_combo = QComboBox()
        layout.addWidget(QLabel("Model:"))
        layout.addWidget(self.model_combo)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _setup_connections(self):
        """Setup signal connections"""
        logger.debug("Setting up ToolsPanel connections")
        self.tool_combo.currentTextChanged.connect(self._on_tool_changed)
        self.add_class_button.clicked.connect(self._on_add_class)
        self.class_combo.currentTextChanged.connect(self._on_class_changed)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        self.auto_annotate_button.clicked.connect(self._on_auto_annotate)
    
    def update_classes(self, classes: dict):
        """Update class list"""
        logger.debug(f"Updating classes: {classes}")
        self.class_combo.clear()
        for class_id, class_name in classes.items():
            self.class_combo.addItem(class_name, class_id)
    
    def update_models(self, models: dict):
        """Update model list"""
        logger.debug(f"Updating models: {list(models.keys())}")
        self.model_combo.clear()
        for model_name in models.keys():
            self.model_combo.addItem(model_name)
    
    def _on_tool_changed(self, tool: str):
        """Handle tool selection change"""
        logger.debug(f"Tool changed: {tool}")
        self.current_tool = tool.lower()
        self.tool_changed.emit(self.current_tool)
    
    def _on_add_class(self):
        """Handle new class addition"""
        class_name = self.new_class_input.text().strip()
        if class_name:
            logger.debug(f"Adding new class: {class_name}")
            self.current_class_id += 1
            self.class_combo.addItem(class_name, self.current_class_id)
            self.class_changed.emit(self.current_class_id, class_name)
            self.new_class_input.clear()
    
    def _on_class_changed(self, class_name: str):
        """Handle class selection change"""
        class_id = self.class_combo.currentData()
        logger.debug(f"Class changed: {class_id} - {class_name}")
        self.current_class_id = class_id
        self.current_class_name = class_name
        self.class_changed.emit(class_id, class_name)
    
    def _on_threshold_changed(self, value: int):
        """Handle threshold change"""
        self.threshold = value / 100.0
        logger.debug(f"Threshold changed: {self.threshold}")
        self.threshold_label.setText(f"Confidence Threshold: {self.threshold:.2f}")
        self.threshold_changed.emit(self.threshold)
    
    def _on_auto_annotate(self):
        """Handle auto-annotate request"""
        model_name = self.model_combo.currentText()
        logger.debug(f"Auto-annotate requested with model {model_name} and threshold {self.threshold}")
        if model_name:
            self.auto_annotate_requested.emit(model_name, self.threshold)
    
    def setEnabled(self, enabled: bool):
        """Enable or disable the widget"""
        super().setEnabled(enabled)
        logger.debug(f"ToolsPanel enabled: {enabled}")