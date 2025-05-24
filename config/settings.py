# config/settings.py
import os
import logging
import json
from pathlib import Path

# Default settings
SETTINGS = {
    'PATHS': {
        'models_dir': 'data/models',
        'annotations_dir': 'data/annotations',
        'projects_dir': 'data/projects',
        'temp_dir': 'data/temp',
        'logs_dir': 'logs'
    },
    'MODELS': {
        'default_confidence_threshold': 0.5,
        'default_iou_threshold': 0.4,
        'max_batch_size': 8,
        'device': 'auto'  # auto, cpu, cuda
    },
    'UI': {
        'dark_theme': True,
        'auto_save': True,
        'auto_save_interval': 300,  # seconds
        'max_undo_steps': 50,
        'image_cache_size': 100
    },
    'ANNOTATION': {
        'supported_formats': ['COCO', 'YOLO', 'Pascal VOC', 'Custom JSON'],
        'default_format': 'COCO',
        'auto_backup': True,
        'backup_interval': 600  # seconds
    }
}

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs(SETTINGS['PATHS']['logs_dir'], exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"{SETTINGS['PATHS']['logs_dir']}/app.log"),
            logging.StreamHandler()
        ]
    )

def load_user_settings():
    """Load user settings from file"""
    settings_file = Path('config/user_settings.json')
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                user_settings = json.load(f)
                # Merge with default settings
                SETTINGS.update(user_settings)
        except Exception as e:
            logging.error(f"Failed to load user settings: {e}")

def save_user_settings():
    """Save current settings to file"""
    settings_file = Path('config/user_settings.json')
    try:
        os.makedirs(settings_file.parent, exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(SETTINGS, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save user settings: {e}")

# Initialize
load_user_settings()
