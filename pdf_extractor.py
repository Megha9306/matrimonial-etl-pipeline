"""
PDF extraction with automatic detection of text-based vs scanned PDFs.
"""

import logging
from typing import Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from .config import PDF_CONFIG

logger = logging.getLogger(__name__)


def is_text_based_pdf(file_path: str) -> bool:
    """
    Detect if a PDF contains extractable text (text-based) or is scanned.
    
    Samples the first few pages to determine if significant text content exists.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        True if PDF is text-based, False if it's scanned/image-based
    """
    if pdfplumber is None:
        logger.warning("pdfplumber not installed. Cannot detect PDF type, assuming text-based.")
        return True
    
    try:
        with pdfplumber.open(file_path) as pdf:
            max_pages = min(PDF_CONFIG['max_pages_for_text_detection'], len(pdf.pages))
            total_text_length = 0
            total_chars_sampled = 0
            
            # Sample first N pages
            for i in range(max_pages):
                page = pdf.pages[i]
                extracted_text = page.extract_text() or ""
                total_text_length += len(extracted_text.strip())
                
                # Estimate total characters (rough estimate)
                # A standard page might have ~2000-3000 characters
                total_chars_sampled += 2500
            
            # Calculate text ratio
            text_ratio = total_text_length / total_chars_sampled if total_chars_sampled > 0 else 0
            
            logger.debug(f"PDF text detection: {text_ratio:.2%} text ratio")
            
            # If text ratio exceeds threshold, it's text-based
            if text_ratio >= PDF_CONFIG['min_text_threshold']:
                logger.info(f"PDF detected as text-based (ratio: {text_ratio:.2%})")
                return True
            else:
                logger.info(f"PDF detected as scanned/image-based (ratio: {text_ratio:.2%})")
                return False
    
    except Exception as e:
        logger.error(f"Error detecting PDF type: {e}. Assuming text-based.")
        return True


def extract_from_text_based_pdf(file_path: str) -> Optional[str]:
    """
    Extract text from a text-based PDF using direct text extraction.
    
    Args:
        file_path: Path to the text-based PDF file
        
    Returns:
        Extracted text as string, or None if extraction fails
    """
    if pdfplumber is None:
        logger.error("pdfplumber is not installed. Cannot extract text from PDF.")
        return None
    
    try:
        extracted_text = []
        
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"Extracting text from {total_pages} pages...")
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    text = page.extract_text() or ""
                    if text.strip():
                        extracted_text.append(f"--- Page {page_num} ---\n{text}")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
                    continue
        
        if not extracted_text:
            logger.warning("No text extracted from PDF")
            return ""
        
        full_text = "\n\n".join(extracted_text)
        logger.info(f"Successfully extracted text from PDF: {file_path} ({len(full_text)} characters)")
        return full_text
    
    except Exception as e:
        logger.error(f"Error extracting text-based PDF: {e}")
        return None
