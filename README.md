# LLM Extraction Module

Converts plain extracted text (from Extraction layer) into structured JSON biodata for matrimonial profiles.

## Architecture

```
Input (Plain Text)
       ↓
  extract_profile()
       ↓
  LLMExtractor
       ├─ Prompt Template
       ├─ LLM Call (OpenAI, etc.)
       └─ Response Validation
       ↓
Output (Structured JSON Dict)
```

## Usage

### Basic Usage

```python
from llmextraction import extract_profile

text = """
Name: John Doe
Age: 28
Profession: Software Engineer
Religion: Hindu
Caste: Brahmin
Location: Delhi
"""

profile = extract_profile(text)
print(profile)
# {
#     'full_name': 'John Doe',
#     'age': 28,
#     'date_of_birth': None,
#     ...
# }
```

### With Custom API Key or Model

```python
profile = extract_profile(
    text,
    api_key="sk-...",
    model="gpt-4"
)
```

### Using LLMExtractor Class

```python
from llmextraction import LLMExtractor

extractor = LLMExtractor(api_key="sk-...", model="gpt-4o-mini")

# Extract multiple texts
profiles = [
    extractor.extract(text1),
    extractor.extract(text2),
    extractor.extract(text3),
]
```

## Configuration

Edit `config.py` to adjust:
- **Model**: `gemini-2.0-flash` (default) or any Google Gemini model
- **Temperature**: 0.1 (low, for deterministic extraction)
- **Max Tokens**: 1024 (adjust based on text length)
- **Extraction Schema**: Fields to extract

## Schema

The module extracts the following fields:

| Field | Type | Notes |
|-------|------|-------|
| full_name | str \| None | Person's full name |
| age | int \| None | Age in years |
| date_of_birth | str \| None | YYYY-MM-DD format |
| height | str \| None | With unit (e.g., "5.8 ft") |
| gender | str \| None | Male, Female, Other |
| marital_status | str \| None | Single, Married, etc. |
| profession | str \| None | Occupation |
| education | str \| None | Qualification |
| religion | str \| None | Religion |
| caste | str \| None | Caste/Community |
| location | str \| None | City/Region |

**All missing fields are returned as `None`.**

## Design Principles

1. **Extraction Only**: Converts text → JSON, no normalization
2. **Strict Schema**: Always returns the exact schema, missing fields are null
3. **Deterministic**: Low temperature for consistent extraction
4. **Error Handling**: Gracefully returns schema with nulls on error
5. **LLM Agnostic**: Can be adapted for OpenAI, Azure, Anthropic, etc.
6. **No Side Effects**: No file I/O, no database writes
7. **Type Safe**: Full type hints for IDE support
8. **Production Ready**: Proper error handling, docstrings, logging

## Module Structure

| File | Purpose |
|------|---------|
| `__init__.py` | Public API exports |
| `extractor.py` | Core LLMExtractor class and extract_profile() |
| `config.py` | LLM settings and extraction schema |
| `prompt_template.py` | Prompt engineering logic |
| `validators.py` | JSON parsing and validation |

## Error Handling

If the LLM call fails or returns malformed JSON:
- Logs the error
- Returns schema with all fields as `None`
- Pipeline continues without crashing

## Dependencies

```
openai>=1.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Environment Variables

The module reads API key from `GOOGLE_API_KEY`:

```bash
export GOOGLE_API_KEY="your-google-api-key"
python your_script.py
```

Or pass directly:
```python
extract_profile(text, api_key="your-google-api-key")
```

## Integration with Pipeline

```python
from Extraction.text_extractor import extract_text  # from Extraction layer
from llmextraction import extract_profile  # this module

# Step 1: Extract text from documents
raw_text = extract_text("document.pdf")

# Step 2: Extract structured profile
profile = extract_profile(raw_text)

# Step 3: Send to Normalisation layer
# (Normalisation layer will clean, validate, and normalize the data)
```

## Future Enhancements

- [ ] Support for OpenAI (swap providers)
- [ ] Support for Anthropic Claude
- [ ] Batch extraction for multiple texts
- [ ] Caching of responses
- [ ] Metrics and monitoring
- [ ] Custom schema support
