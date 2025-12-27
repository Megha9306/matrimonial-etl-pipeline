"""
Utility functions for file handling and type detection.
"""

import logging
from pathlib import Path
from typing import Literal

from .config import SUPPORTED_FORMATS

logger = logging.getLogger(__name__)


def get_file_type(file_path: str) -> Literal['pdf', 'image', 'text', 'unknown']:
    """
    Detect file type based on file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File type: 'pdf', 'image', 'text', or 'unknown'
    """
    try:
        path = Path(file_path)
        extension = path.suffix.lower()
        
        for file_type, extensions in SUPPORTED_FORMATS.items():
            if extension in extensions:
                return file_type
        
        logger.warning(f"Unsupported file type: {extension}")
        return 'unknown'
    
    except Exception as e:
        logger.error(f"Error detecting file type: {e}")
        return 'unknown'


def validate_file(file_path: str) -> tuple[bool, str]:
    """
    Validate file existence and accessibility.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            msg = f"File does not exist: {file_path}"
            logger.error(msg)
            return False, msg
        
        if not path.is_file():
            msg = f"Path is not a file: {file_path}"
            logger.error(msg)
            return False, msg
        
        # Check file size
        from .config import MAX_FILE_SIZE
        file_size = path.stat().st_size
        
        if file_size > MAX_FILE_SIZE:
            msg = f"File too large ({file_size} bytes). Max: {MAX_FILE_SIZE} bytes"
            logger.error(msg)
            return False, msg
        
        if file_size == 0:
            msg = f"File is empty: {file_path}"
            logger.error(msg)
            return False, msg
        
        return True, "File is valid"
    
    except Exception as e:
        msg = f"Error validating file: {e}"
        logger.error(msg)
        return False, msg


def is_supported_format(file_path: str) -> bool:
    """
    Check if file format is supported.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if format is supported
    """
    file_type = get_file_type(file_path)
    return file_type != 'unknown'


def sanitize_text(text: str) -> str:
    """
    Clean extracted text by removing excessive whitespace and control characters.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    try:
        # Remove multiple newlines, keep max 2
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    except Exception as e:
        logger.error(f"Error sanitizing text: {e}")
        return text
