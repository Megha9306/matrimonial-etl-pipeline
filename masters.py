"""Master data loader and cache.

Loads master Excel files once and exposes helper getters for canonical values.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

_CACHE: Dict[str, pd.DataFrame] = {}

DEFAULT_MASTER_FILES = {
    "height": "HeightMst.xlsx",
    "occupation": "OccupationMst.xlsx",
    "qualification": "QualificationMst.xlsx",
    "caste": "CasteMst.xlsx",
    "country_state": "CountryStateMst.xlsx",
    "biodata_output": "Biodata_Output.xlsx",
    "marital_status": "MaritalStatusMst.xlsx",
    "manglik": "ManglikMst.xlsx",
}


def _find_file(name: str, master_dir: Optional[Path]) -> Optional[Path]:
    if master_dir:
        p = master_dir / name
        if p.exists():
            return p
    # try relative to this file (project)
    p2 = Path(__file__).resolve().parent.parent / name
    if p2.exists():
        return p2
    return None


def load_master(key: str, master_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load and cache a master file by logical key.

    master_dir: optional directory where master Excel files live.
    Raises FileNotFoundError if master file cannot be located.
    """
    if key in _CACHE:
        return _CACHE[key]
    if key not in DEFAULT_MASTER_FILES:
        raise KeyError(f"Unknown master key: {key}")
    fname = DEFAULT_MASTER_FILES[key]
    path = _find_file(fname, Path(master_dir) if master_dir else None)
    if not path:
        raise FileNotFoundError(f"Master file {fname} not found (looked in {master_dir})")
    df = pd.read_excel(path)
    _CACHE[key] = df
    return df


def get_master_values(key: str, column: Optional[str] = None, master_dir: Optional[Path] = None) -> List[str]:
    """Return a list of canonical values from the master.

    If column is None and the dataframe has a single column, it returns that column.
    If column is None and multiple columns exist, returns the first column.
    """
    df = load_master(key, master_dir=master_dir)
    if column is None:
        column = df.columns[0]
    values = df[column].dropna().astype(str).tolist()
    return values


def load_biodata_output_schema(master_dir: Optional[Path] = None) -> List[str]:
    """Load the Biodata_Output.xlsx headers to derive the required output column order.

    Raises FileNotFoundError if the file is not found.
    """
    path = _find_file(DEFAULT_MASTER_FILES["biodata_output"], Path(master_dir) if master_dir else None)
    if not path:
        raise FileNotFoundError("Biodata_Output.xlsx not found in master locations")
    df = pd.read_excel(path, nrows=0)
    return list(df.columns)
