import logging
from pathlib import Path
from typing import Dict, List, Any

# Extraction layer
from Extraction.extractor import extract_text

# LLM Extraction layer
from LLM_Extraction.llmextractor import extract_profile
from LLM_Extraction.summary_generator import generate_profile_summary

# Normalisation layer
from Normalisation.normalisation import normalize_profile


# -------------------------------------------------------------------
# Logging configuration
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------
def run_pipeline(input_dir: Path) -> Dict[str, List[Any]]:
    """
    Run the end-to-end document processing pipeline.

    Flow:
        File
          -> Extraction (plain text)
          -> LLM Extraction (raw structured dict)
          -> Normalisation (master-driven structured dict)

    Args:
        input_dir (Path): Directory containing input documents.

    Returns:
        dict: {
            "processed": [normalized_record, ...],
            "failed": [{"file": str, "error": str}, ...]
        }
    """
    processed: List[Dict[str, Any]] = []
    failed: List[Dict[str, str]] = []

    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"Invalid input directory: {input_dir}")

    logger.info(f"Starting pipeline on directory: {input_dir}")

    from Extraction.config import SUPPORTED_FORMATS

    allowed_exts = {
        ext for exts in SUPPORTED_FORMATS.values() for ext in exts
        }

    for file_path in input_dir.iterdir():
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in allowed_exts:
            logger.info(f"Skipping unsupported file: {file_path.name}")
            continue

        try:
            logger.info(f"Processing file: {file_path.name}")

            normalized_records = _process_single_file(file_path)
            # Add all records from this file to processed list
            processed.extend(normalized_records)

            logger.info(f"Successfully processed: {file_path.name}")

        except Exception as exc:
            logger.error(f"Failed to process {file_path.name}: {exc}")
            failed.append({
                "file": file_path.name,
                "error": str(exc)
            })

    logger.info(
        f"Pipeline finished | Success: {len(processed)} | Failed: {len(failed)}"
    )

    return {
        "processed": processed,
        "failed": failed
    }


# -------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------
def _process_single_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Process a single document through all pipeline stages.
    
    Handles files with multiple matrimonial records and returns a list of profiles.

    Args:
        file_path (Path): Path to the input document.

    Returns:
        list: List of normalized profile dictionaries (one per record in the document).
    """

    # 1. Document -> plain text
    text: str = extract_text(file_path)

    if not text or not text.strip():
        raise ValueError("No text extracted from document")

    # 2. Plain text -> list of raw structured profiles (LLM)
    raw_profiles: List[Dict[str, Any]] = extract_profile(text)

    if not isinstance(raw_profiles, list):
        raise ValueError("LLM extraction did not return a list of profiles")

    # 3. Raw profiles -> normalized profiles (masters + rules)
    normalized_profiles = []
    for raw_profile in raw_profiles:
        if isinstance(raw_profile, dict):
            normalized_profile: Dict[str, Any] = normalize_profile(raw_profile)
            
            # 4. Generate comprehensive summary using OpenAI
            try:
                logger.info(f"Generating summary for: {normalized_profile.get('full_name', 'Unknown')}")
                summary = generate_profile_summary(normalized_profile)
                if summary:
                    normalized_profile["about_yourself_summary"] = summary
                    logger.info(f"Generated profile summary for {normalized_profile.get('full_name', 'Unknown')}")
                else:
                    logger.warning(f"Failed to generate summary for {normalized_profile.get('full_name', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Error generating summary for {normalized_profile.get('full_name', 'Unknown')}: {e}")
            
            normalized_profiles.append(normalized_profile)

    return normalized_profiles


# -------------------------------------------------------------------
# CLI / module execution
# -------------------------------------------------------------------
from Output.output_writer import write_biodata_output

if __name__ == "__main__":
    input_directory = Path("input")
    results = run_pipeline(input_directory)

    print("\n=== PIPELINE RESULT SUMMARY ===")
    print(f"Processed records: {len(results['processed'])}")
    print(f"Failed files: {len(results['failed'])}")

    print("\n===== DEBUG: RECORDS BEFORE EXCEL WRITE =====")
    print(f"Type of records: {type(results['processed'])}")
    print(f"Number of records: {len(results['processed'])}")

    for i, record in enumerate(results["processed"], start=1):
        print(f"\n--- Record {i} ---")
        if isinstance(record, dict):
            for k, v in record.items():
                # For long strings like about_yourself_summary, truncate for display
                if isinstance(v, str) and len(v) > 100:
                    print(f"{k}: {v[:100]}...")
                else:
                    print(f"{k}: {v}")
        else:
            print(record)

    print("===== END DEBUG =====\n")

    write_biodata_output(
        records=results["processed"],
        output_path=Path("Output/biodata_output.xlsx"),
        schema_path=Path("Data/Biodata_Output.xlsx")
    )

    

