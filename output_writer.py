from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import time
import os


def write_biodata_output(
    records: List[Dict[str, Any]],
    output_path: Path,
    schema_path: Path | None = None,
    append: bool = True,
) -> None:
    """
    Write normalized biodata records to Biodata_Output.xlsx.

    Args:
        records (List[Dict[str, Any]]):
            List of normalized profile dictionaries produced by the pipeline.

        output_path (Path):
            Path to the output Excel file (e.g. Output/Biodata_Output.xlsx).

        schema_path (Path | None):
            Optional path to Biodata_Output.xlsx template/schema.
            If provided, column order will strictly follow the schema.
    """

    if not records:
        raise ValueError("No records provided to write output")

    df = pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Apply defaults and fill NULL values
    # ------------------------------------------------------------------
    # Fill None/NaN with 'NULL' for all columns
    df = df.fillna('NULL')
    
    # Apply defaults for specific fields if they are still 'NULL'
    if 'MaritialStatus' in df.columns:
        df.loc[df['MaritialStatus'] == 'NULL', 'MaritialStatus'] = 'Unmarried'
    elif 'marital_status' in df.columns:
        df.loc[df['marital_status'] == 'NULL', 'marital_status'] = 'Unmarried'
    
    if 'Country' in df.columns:
        df.loc[df['Country'] == 'NULL', 'Country'] = 'India'
    elif 'country' in df.columns:
        df.loc[df['country'] == 'NULL', 'country'] = 'India'
    
    if 'NativeState' in df.columns:
        df.loc[df['NativeState'] == 'NULL', 'NativeState'] = 'Rajasthan'
    elif 'native_state' in df.columns:
        df.loc[df['native_state'] == 'NULL', 'native_state'] = 'Rajasthan'

    # ------------------------------------------------------------------
    # Enforce schema / column order if schema file is provided
    # ------------------------------------------------------------------
    if schema_path:
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        schema_df = pd.read_excel(schema_path)
        schema_columns = list(schema_df.columns)

        # Create mapping from snake_case (internal) to PascalCase (schema)
        # e.g., full_name -> FullName, mobile_no -> MobileNo
        def snake_to_pascal(snake_str):
            """Convert snake_case to PascalCase"""
            words = snake_str.split('_')
            pascal = ''.join(word.capitalize() for word in words)
            # Handle schema misspellings
            if pascal == "MaritalStatus":
                return "MaritialStatus"  # Schema has unusual spelling with extra 'i'
            return pascal
        
        # Rename columns to match schema
        rename_map = {}
        for internal_col in df.columns:
            pascal_col = snake_to_pascal(internal_col)
            if pascal_col in schema_columns:
                rename_map[internal_col] = pascal_col

        # Special-case mappings where schema uses a different Pascal name
        # e.g., our internal `about_yourself_summary` should map to `AboutYourself`
        if 'about_yourself_summary' in df.columns and 'AboutYourself' in schema_columns:
            rename_map['about_yourself_summary'] = 'AboutYourself'
        
        df = df.rename(columns=rename_map)

        # Add missing columns as None
        for col in schema_columns:
            if col not in df.columns:
                df[col] = None

        # Select only schema columns in schema order
        df = df[schema_columns]

    # ------------------------------------------------------------------
    # Ensure output directory exists
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Write Excel file with retries (append if requested)
    # ------------------------------------------------------------------
    max_retries = 5
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # If append requested and an existing output file is present, read and append new records
            if append and output_path.exists():
                try:
                    existing_df = pd.read_excel(str(output_path), engine='openpyxl')
                    # Ensure columns line up: add any missing columns to either frame
                    for col in existing_df.columns:
                        if col not in df.columns:
                            df[col] = None
                    for col in df.columns:
                        if col not in existing_df.columns:
                            existing_df[col] = None

                    # Reorder columns to the existing file's order
                    cols = list(existing_df.columns)
                    df = df[cols]

                    # Append
                    out_df = pd.concat([existing_df, df], ignore_index=True, sort=False)
                except Exception:
                    # If reading fails for any reason, fall back to writing only new records
                    out_df = df
            else:
                # Either file doesn't exist or append not requested
                out_df = df

            # Write atomically to avoid partial writes (write to temp then replace)
            # Ensure temporary file keeps the same .xlsx extension so the
            # chosen engine (openpyxl) accepts the filename.
            temp_path = output_path.with_name(output_path.stem + ".tmp" + output_path.suffix)
            out_df.to_excel(str(temp_path), index=False, engine='openpyxl')
            os.replace(str(temp_path), str(output_path))
            print(f"[SUCCESS] Biodata output appended to: {output_path}")
            return

        except PermissionError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 8)
                print(f"[WAIT] Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                raise PermissionError(
                    f"Permission denied writing to '{output_path}' after {max_retries} attempts. "
                    "The file may be open in Excel or another application. "
                    "Please close the file and try again."
                ) from last_error
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise
