"""
Configuration and logging setup for the Extraction layer.
"""

import logging
from pathlib import Path

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding multiple handlers
    if logger.handlers:
        return logger
    
    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# ============================================================================
# FILE EXTENSIONS AND MIME TYPES
# ============================================================================

SUPPORTED_FORMATS = {
    'pdf': ['.pdf'],
    'image': ['.png', '.jpg', '.jpeg', '.bmp', '.tiff'],
    'text': ['.txt']
}

# Maximum file size (in bytes) - 100 MB
MAX_FILE_SIZE = 100 * 1024 * 1024

# OCR-related settings
OCR_CONFIG = {
    'timeout_seconds': 60,
    'tesseract_cmd': None,  # Set to full path if Tesseract is not in PATH
    'language': 'eng',
    'quality_threshold': 0.3  # Minimum confidence threshold for OCR results
}

# PDF-related settings
PDF_CONFIG = {
    'max_pages_for_text_detection': 5,  # Sample first N pages to detect if text-based
    'min_text_threshold': 0.1  # If text content > 10%, treat as text-based PDF
}
