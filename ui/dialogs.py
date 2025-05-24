# ui/dialogs.py
import logging
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton, QFileDialog, QComboBox
from PyQt5.QtCore import Qt
from config.settings import SETTINGS

logger = logging.getLogger(__name__)

class ProjectDialog(QDialog):
    """Dialog for creating new projects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing ProjectDialog")
        self.setWindowTitle("New Project")
        self.setModal(True)
        self._setup_ui()
        logger.info("ProjectDialog initialized successfully")
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        logger.debug("Setting up ProjectDialog UI")
        layout = QVBoxLayout()
        
        # Project name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter project name")
        layout.addWidget(self.name_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter project description")
        layout.addWidget(self.description_input)
        
        # Image directory
        self.image_dir_input = QLineEdit()
        self.image_dir_button = QPushButton("Browse...")
        self.image_dir_button.clicked.connect(self._browse_image_dir)
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.image_dir_input)
        dir_layout.addWidget(self.image_dir_button)
        layout.addLayout(dir_layout)
        
        # Annotation format
        self.format_combo = QComboBox()
        self.format_combo.addItems(SETTINGS['ANNOTATION']['supported_formats'])
        self.format_combo.setCurrentText(SETTINGS['ANNOTATION']['default_format'])
        layout.addWidget(self.format_combo)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def _browse_image_dir(self):
        """Browse for image directory"""
        logger.debug("Browsing for image directory")
        directory = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if directory:
            self.image_dir_input.setText(directory)
            logger.debug(f"Selected image directory: {directory}")
    
    def get_project_data(self) -> dict:
        """Get project data from inputs"""
        logger.debug("Getting project data")
        return {
            'name': self.name_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'image_directory': self.image_dir_input.text().strip(),
            'annotation_format': self.format_combo.currentText()
        }

class SettingsDialog(QDialog):
    """Dialog for application settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing SettingsDialog")
        self.setWindowTitle("Settings")
        self.setModal(True)
        self._setup_ui()
        logger.info("SettingsDialog initialized successfully")
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        logger.debug("Setting up SettingsDialog UI")
        layout = QVBoxLayout()
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText("Dark" if SETTINGS['UI']['dark_theme'] else "Light")
        layout.addWidget(QLabel("Theme:"))
        layout.addWidget(self.theme_combo)
        
        # Auto-save
        self.auto_save_input = QLineEdit(str(SETTINGS['UI']['auto_save_interval']))
        layout.addWidget(QLabel("Auto-save interval (seconds):"))
        layout.addWidget(self.auto_save_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self._save_settings)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def _save_settings(self):
        """Save settings and accept dialog"""
        logger.debug("Saving settings")
        try:
            SETTINGS['UI']['dark_theme'] = self.theme_combo.currentText() == "Dark"
            SETTINGS['UI']['auto_save_interval'] = int(self.auto_save_input.text())
            from config.settings import save_user_settings
            save_user_settings()
            self.accept()
        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}")

class AboutDialog(QDialog):
    """Dialog for about information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing AboutDialog")
        self.setWindowTitle("About")
        self.setModal(True)
        self._setup_ui()
        logger.info("AboutDialog initialized successfully")
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        logger.debug("Setting up AboutDialog UI")
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Advanced Image Annotation Framework"))
        layout.addWidget(QLabel("Version 1.0.0"))
        layout.addWidget(QLabel("Developed for efficient image annotation"))
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        self.setLayout(layout)