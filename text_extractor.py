"""
Plain text file extraction.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_from_text_file(file_path: str) -> Optional[str]:
    """
    Read and extract text from a plain text file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Extracted text as string, or None if extraction fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            logger.warning(f"Text file is empty or contains only whitespace: {file_path}")
            return ""
        
        logger.info(f"Successfully extracted text from: {file_path}")
        return text
    
    except UnicodeDecodeError:
        logger.warning(f"UTF-8 decoding failed, trying with latin-1 encoding: {file_path}")
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
            logger.info(f"Successfully extracted text (latin-1) from: {file_path}")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text with latin-1 encoding: {e}")
            return None
    
    except Exception as e:
        logger.error(f"Error extracting text from file: {e}")
        return None
