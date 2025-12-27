"""
Main dispatcher for text extraction from various document formats.

This module provides the primary entry point for the extraction layer.
It routes files to appropriate extractors based on file type.
"""

import logging
from typing import Optional

from .config import setup_logger
from .utils import (
    get_file_type,
    validate_file,
    is_supported_format,
    sanitize_text
)
from .text_extractor import extract_from_text_file
from .pdf_extractor import is_text_based_pdf, extract_from_text_based_pdf
from .ocr_extractor import extract_from_scanned_pdf_ocr, extract_from_image_ocr

# Set up module logger
logger = setup_logger(__name__)


def extract_text(file_path: str) -> Optional[str]:
    """
    Main dispatcher function to extract text from any supported document format.
    
    Automatically detects file type and routes to appropriate extractor:
    - Text files (.txt) → direct file reading
    - Text-based PDFs → pdfplumber extraction
    - Scanned PDFs → OCR-based extraction
    - Images (.png, .jpg, .jpeg) → OCR-based extraction
    
    Args:
        file_path: Absolute or relative path to the document file
        
    Returns:
        Extracted text as a string, or None if extraction fails
        
    Raises:
        None - errors are logged and None is returned
        
    Examples:
        >>> text = extract_text("document.pdf")
        >>> text = extract_text("image.png")
        >>> text = extract_text("data.txt")
    """
    logger.info(f"Starting extraction for: {file_path}")
    
    # Step 1: Validate file
    is_valid, validation_msg = validate_file(file_path)
    if not is_valid:
        logger.error(f"File validation failed: {validation_msg}")
        return None
    
    # Step 2: Check if format is supported
    if not is_supported_format(file_path):
        logger.error(f"Unsupported file format: {file_path}")
        return None
    
    # Step 3: Detect file type
    file_type = get_file_type(file_path)
    logger.info(f"File type detected: {file_type}")
    
    # Step 4: Route to appropriate extractor
    extracted_text = None
    
    if file_type == 'text':
        logger.debug("Routing to text extractor")
        extracted_text = extract_from_text_file(file_path)
    
    elif file_type == 'pdf':
        logger.debug("Detected PDF, checking if text-based or scanned")
        
        if is_text_based_pdf(file_path):
            logger.debug("Routing to text-based PDF extractor")
            extracted_text = extract_from_text_based_pdf(file_path)
        else:
            logger.debug("Routing to OCR-based PDF extractor")
            extracted_text = extract_from_scanned_pdf_ocr(file_path)
    
    elif file_type == 'image':
        logger.debug("Routing to image OCR extractor")
        extracted_text = extract_from_image_ocr(file_path)
    
    else:
        logger.error(f"Unknown file type: {file_type}")
        return None
    
    # Step 5: Post-processing
    if extracted_text is None:
        logger.error(f"Extraction returned None: {file_path}")
        return None
    
    # Sanitize and clean text
    cleaned_text = sanitize_text(extracted_text)
    
    if not cleaned_text:
        logger.warning(f"Extracted text is empty after sanitization: {file_path}")
        return ""
    
    logger.info(f"Extraction successful. Extracted {len(cleaned_text)} characters")
    return cleaned_text


def extract_batch(file_paths: list[str]) -> dict[str, Optional[str]]:
    """
    Extract text from multiple files in batch.
    
    Args:
        file_paths: List of file paths to extract text from
        
    Returns:
        Dictionary mapping file paths to extracted text (None if failed)
        
    Examples:
        >>> results = extract_batch(["doc1.pdf", "image.png", "text.txt"])
        >>> for file_path, text in results.items():
        ...     if text:
        ...         print(f"Successfully extracted from {file_path}")
    """
    logger.info(f"Starting batch extraction for {len(file_paths)} files")
    
    results = {}
    for i, file_path in enumerate(file_paths, 1):
        logger.info(f"Processing file {i}/{len(file_paths)}: {file_path}")
        results[file_path] = extract_text(file_path)
    
    successful = sum(1 for text in results.values() if text is not None)
    logger.info(f"Batch extraction complete. Successful: {successful}/{len(file_paths)}")
    
    return results
