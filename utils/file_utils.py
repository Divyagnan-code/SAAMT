# utils/file_utils.py
import logging
import os
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

def get_supported_image_files(directory: str) -> List[str]:
    """Get list of supported image files in directory"""
    logger.debug(f"Getting supported image files from {directory}")
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp'}
    try:
        return [str(file) for file in Path(directory).iterdir() 
                if file.suffix.lower() in supported_formats]
    except Exception as e:
        logger.error(f"Error getting image files: {str(e)}")
        return []

def create_directory(directory: str):
    """Create directory if it doesn't exist"""
    logger.debug(f"Creating directory: {directory}")
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory created: {directory}")
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {str(e)}")
        raise

def file_exists(file_path: str) -> bool:
    """Check if file exists"""
    logger.debug(f"Checking if file exists: {file_path}")
    return Path(file_path).exists()