"""
Package initialization for the Extraction layer.
"""

from .config import setup_logger
from .extractor import extract_text, extract_batch

# Set up logging for the package
logger = setup_logger(__name__)

__all__ = [
    'extract_text',
    'extract_batch',
    'logger'
]
