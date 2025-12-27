"""
OCR-based text extraction for scanned PDFs and image files.
"""

import logging
from typing import Optional
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

try:
    import pdf2image
except ImportError:
    pdf2image = None

from .config import OCR_CONFIG

logger = logging.getLogger(__name__)


def _validate_ocr_setup() -> bool:
    """
    Validate that Tesseract OCR is properly installed and configured.
    
    Returns:
        True if OCR is available, False otherwise
    """
    if pytesseract is None or Image is None:
        logger.error("pytesseract or Pillow is not installed")
        return False
    
    try:
        # Try to get Tesseract version
        version = pytesseract.get_tesseract_version()
        logger.debug(f"Tesseract OCR version: {version}")
        return True
    except Exception as e:
        logger.error(f"Tesseract OCR not found or not configured: {e}")
        return False


def extract_from_image_ocr(file_path: str) -> Optional[str]:
    """
    Extract text from an image file using OCR.
    
    Args:
        file_path: Path to the image file (.png, .jpg, .jpeg, etc.)
        
    Returns:
        Extracted text as string, or None if extraction fails
    """
    if not _validate_ocr_setup():
        return None
    
    try:
        logger.info(f"Performing OCR on image: {file_path}")
        
        # Open image
        image = Image.open(file_path)
        
        # Configure Tesseract if custom path is provided
        config = OCR_CONFIG.copy()
        if config['tesseract_cmd']:
            pytesseract.pytesseract.pytesseract_cmd = config['tesseract_cmd']
        
        # Run OCR with language and configuration
        custom_config = f"--psm 6 -l {config['language']}"
        extracted_text = pytesseract.image_to_string(image, config=custom_config)
        
        if not extracted_text.strip():
            logger.warning(f"No text found in image via OCR: {file_path}")
            return ""
        
        logger.info(f"Successfully extracted text from image: {file_path}")
        return extracted_text
    
    except Exception as e:
        logger.error(f"Error performing OCR on image: {e}")
        return None


def extract_from_scanned_pdf_ocr(file_path: str) -> Optional[str]:
    """
    Extract text from a scanned PDF using OCR.
    
    First converts PDF pages to images, then applies OCR.
    
    Args:
        file_path: Path to the scanned PDF file
        
    Returns:
        Extracted text as string, or None if extraction fails
    """
    if not _validate_ocr_setup():
        return None
    
    if pdf2image is None:
        logger.error("pdf2image is not installed. Cannot convert PDF to images for OCR.")
        return None
    
    try:
        logger.info(f"Performing OCR on scanned PDF: {file_path}")
        
        # Configure Tesseract if custom path is provided
        config = OCR_CONFIG.copy()
        if config['tesseract_cmd']:
            pytesseract.pytesseract.pytesseract_cmd = config['tesseract_cmd']
        
        # Convert PDF to images
        images = pdf2image.convert_from_path(file_path, timeout=config['timeout_seconds'])
        
        if not images:
            logger.error(f"Could not convert PDF to images: {file_path}")
            return None
        
        logger.info(f"Converted PDF to {len(images)} images")
        
        # Extract text from each image using OCR
        extracted_text = []
        custom_config = f"--psm 6 -l {config['language']}"
        
        for page_num, image in enumerate(images, 1):
            try:
                text = pytesseract.image_to_string(image, config=custom_config)
                if text.strip():
                    extracted_text.append(f"--- Page {page_num} ---\n{text}")
                else:
                    logger.warning(f"No text found on page {page_num}")
            except Exception as e:
                logger.warning(f"Error performing OCR on page {page_num}: {e}")
                continue
        
        if not extracted_text:
            logger.warning("No text extracted from any page in PDF")
            return ""
        
        full_text = "\n\n".join(extracted_text)
        logger.info(f"Successfully extracted text from scanned PDF: {file_path} ({len(full_text)} characters)")
        return full_text
    
    except Exception as e:
        logger.error(f"Error performing OCR on scanned PDF: {e}")
        return None
