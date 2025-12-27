"""
Example usage of the Extraction layer.

Run this file to see the extraction layer in action.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Extraction.extractor import extract_text, extract_batch
from Extraction.config import setup_logger

# Set up logger
logger = setup_logger(__name__)


def example_single_file_extraction():
    """Example: Extract text from a single file."""
    logger.info("=" * 60)
    logger.info("Example 1: Single File Extraction")
    logger.info("=" * 60)
    
    # You would replace these with actual file paths
    sample_files = [
        'input/sample.txt',
        'input/sample.pdf',
        'input/image.png'
    ]
    
    for file_path in sample_files:
        logger.info(f"\nExtracting from: {file_path}")
        
        text = extract_text(file_path)
        
        if text is not None:
            preview = text[:200] + "..." if len(text) > 200 else text
            logger.info(f"Success! Extracted text ({len(text)} chars):")
            logger.info(f"Preview: {preview}")
        else:
            logger.error(f"Failed to extract from: {file_path}")


def example_batch_extraction():
    """Example: Extract text from multiple files in batch."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 2: Batch Extraction")
    logger.info("=" * 60)
    
    # You would replace these with actual file paths
    files_to_process = [
        'input/sample1.txt',
        'input/sample2.pdf',
        'input/sample3.png'
    ]
    
    logger.info(f"Processing {len(files_to_process)} files...")
    results = extract_batch(files_to_process)
    
    # Summarize results
    logger.info("\nBatch Results Summary:")
    successful = 0
    failed = 0
    
    for file_path, extracted_text in results.items():
        if extracted_text is not None:
            successful += 1
            logger.info(f"  ✓ {file_path}: {len(extracted_text)} characters")
        else:
            failed += 1
            logger.error(f"  ✗ {file_path}: Failed")
    
    logger.info(f"\nTotal: {successful} successful, {failed} failed")


def example_text_file_extraction():
    """Example: Extract from plain text file."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 3: Text File Extraction")
    logger.info("=" * 60)
    
    # Sample text file path
    text_file = 'input/resume.txt'
    
    logger.info(f"Extracting from text file: {text_file}")
    text = extract_text(text_file)
    
    if text:
        logger.info(f"Successfully extracted {len(text)} characters")
        logger.info("First 100 characters:")
        logger.info(text[:100])
    else:
        logger.error(f"Failed to extract from: {text_file}")


def example_pdf_extraction():
    """Example: Extract from PDF (auto-detects if text-based or scanned)."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 4: PDF Extraction (Auto-detect)")
    logger.info("=" * 60)
    
    pdf_file = 'input/document.pdf'
    
    logger.info(f"Extracting from PDF: {pdf_file}")
    logger.info("(Automatically detecting if text-based or scanned)")
    
    text = extract_text(pdf_file)
    
    if text:
        logger.info(f"Successfully extracted {len(text)} characters")
        logger.info("First 150 characters:")
        logger.info(text[:150])
    else:
        logger.error(f"Failed to extract from: {pdf_file}")


def example_image_extraction():
    """Example: Extract text from image using OCR."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 5: Image OCR Extraction")
    logger.info("=" * 60)
    
    image_file = 'input/document_image.png'
    
    logger.info(f"Extracting from image: {image_file}")
    logger.info("(Using Tesseract OCR)")
    
    text = extract_text(image_file)
    
    if text:
        logger.info(f"Successfully extracted {len(text)} characters")
        logger.info("Extracted text:")
        logger.info(text)
    else:
        logger.error(f"Failed to extract from: {image_file}")


def example_error_handling():
    """Example: Demonstrate error handling."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 6: Error Handling")
    logger.info("=" * 60)
    
    # Non-existent file
    logger.info("\nTest 1: Non-existent file")
    text = extract_text('input/does_not_exist.txt')
    if text is None:
        logger.info("Correctly returned None for missing file")
    
    # Unsupported file type
    logger.info("\nTest 2: Unsupported file type")
    text = extract_text('input/file.xyz')
    if text is None:
        logger.info("Correctly returned None for unsupported format")
    
    # Empty file
    logger.info("\nTest 3: Empty file")
    text = extract_text('input/empty.txt')
    if text == "":
        logger.info("Correctly returned empty string for empty file")


if __name__ == "__main__":
    logger.info("Starting Extraction Layer Examples")
    logger.info("Note: Replace file paths with actual documents in your input/ folder")
    
    # Run examples (comment out as needed)
    # example_single_file_extraction()
    # example_batch_extraction()
    example_text_file_extraction()
    # example_pdf_extraction()
    # example_image_extraction()
    # example_error_handling()
    
    logger.info("\n" + "=" * 60)
    logger.info("Examples completed!")
    logger.info("=" * 60)
