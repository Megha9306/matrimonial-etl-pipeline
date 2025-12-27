# Extraction Layer Documentation

## Overview

The Extraction layer converts unstructured documents into plain text. It automatically detects document types and routes them to the appropriate extractor.

## Supported Document Types

- **Text-based PDFs** - Direct text extraction using `pdfplumber`
- **Scanned PDFs** - OCR-based extraction using Tesseract
- **Images** (.png, .jpg, .jpeg, .bmp, .tiff) - OCR-based extraction
- **Plain text files** (.txt) - Direct file reading

## Architecture

```
extract_text() [Main Dispatcher]
├── Text File → extract_from_text_file()
├── PDF (Text-based) → extract_from_text_based_pdf()
├── PDF (Scanned) → extract_from_scanned_pdf_ocr()
└── Image → extract_from_image_ocr()
```

## Module Structure

| Module | Purpose |
|--------|---------|
| `extractor.py` | Main dispatcher and batch extraction functions |
| `config.py` | Configuration, logging setup, and constants |
| `utils.py` | File validation, type detection, text sanitization |
| `text_extractor.py` | Plain text file extraction |
| `pdf_extractor.py` | Text-based and scanned PDF detection |
| `ocr_extractor.py` | OCR-based extraction for images and scanned PDFs |

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Run the installer (use default installation path)
- Or set custom path in `config.py`:

```python
OCR_CONFIG['tesseract_cmd'] = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

## Usage

### Basic Usage

```python
from Extraction import extract_text

# Extract from any supported document
text = extract_text('documents/resume.pdf')
if text:
    print(text)
else:
    print("Extraction failed")
```

### Batch Processing

```python
from Extraction import extract_batch

files = [
    'documents/doc1.pdf',
    'documents/doc2.png',
    'documents/doc3.txt'
]

results = extract_batch(files)
for file_path, extracted_text in results.items():
    if extracted_text:
        print(f"✓ {file_path}: {len(extracted_text)} characters")
    else:
        print(f"✗ {file_path}: Extraction failed")
```

### Logging

Logging is automatically configured. To adjust log levels:

```python
import logging

# Set to DEBUG for more detailed output
logging.getLogger('Extraction').setLevel(logging.DEBUG)
```

## Configuration

Edit `config.py` to customize:

```python
# Maximum file size (bytes)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# OCR settings
OCR_CONFIG = {
    'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    'language': 'eng',
    'timeout_seconds': 60,
    'quality_threshold': 0.3
}

# PDF detection settings
PDF_CONFIG = {
    'max_pages_for_text_detection': 5,
    'min_text_threshold': 0.1  # If > 10% text, treat as text-based
}
```

## Error Handling

All errors are gracefully handled:
- Invalid files return `None`
- Empty files return empty string `""`
- Errors are logged with meaningful messages
- OCR fallback is automatic for PDFs

## Performance Notes

- Text-based PDF extraction: Fast (milliseconds to seconds)
- Scanned PDF/Image OCR: Slower (seconds to minutes depending on page count)
- Batch processing respects system resources
- Large PDFs (100+ pages) may take several minutes

## Return Values

| Scenario | Return |
|----------|--------|
| Successful extraction | String with extracted text |
| File not found | `None` (logged as error) |
| Empty document | Empty string `""` (logged as warning) |
| Unsupported format | `None` (logged as error) |
| OCR unavailable | `None` (logged as error) |

## Limitations

- OCR accuracy depends on document quality
- Handwritten text is not well-recognized by default Tesseract
- Very large files (>100MB) may be slow
- PDF detection relies on text sampling (first 5 pages)

## Next Steps in Pipeline

The extracted text output is ready for:
- **Normalization Layer**: Clean and standardize extracted data
- **LLM Extraction Layer**: Apply LLM-based entity extraction
- **Storage Layer**: Store processed documents

## Troubleshooting

**"Tesseract not found"**
- Install Tesseract OCR
- Set correct path in `config.py`

**"pdfplumber import error"**
- Run: `pip install pdfplumber`

**"Empty text extraction from PDFs"**
- Verify it's not a scanned PDF
- Check file is not corrupted
- Try with OCR extraction manually

**Memory issues with large PDFs**
- Process in smaller batches
- Reduce `max_pages_for_text_detection`
