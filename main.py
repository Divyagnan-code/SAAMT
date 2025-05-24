# main.py
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from config.settings import setup_logging, SETTINGS

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Advanced Annotation Framework")
    
    # Create application
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    
    # Apply dark theme if enabled
    if SETTINGS['UI']['dark_theme']:
        apply_dark_theme(app)
    
    try:
        # Create main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("Application started successfully")
        
        # Run application
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

def apply_dark_theme(app):
    """Apply dark theme to the application"""
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4c4c4c;
        }
        QPushButton:pressed {
            background-color: #1c1c1c;
        }
        QListWidget {
            background-color: #1e1e1e;
            border: 1px solid #555555;
        }
        QListWidget::item {
            padding: 5px;
            border-bottom: 1px solid #555555;
        }
        QListWidget::item:selected {
            background-color: #0078d4;
        }
        QSlider::groove:horizontal {
            background-color: #555555;
            height: 6px;
        }
        QSlider::handle:horizontal {
            background-color: #0078d4;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
    """)

if __name__ == "__main__":
    main()
