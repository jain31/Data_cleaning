import hashlib
import logging
from pathlib import Path
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()  # Sends logs to the console
    ]
)
logger = logging.getLogger("ingestion")


ROOTDIR = Path(".") 

SRC_DIR = ROOTDIR / "src"
duplicate_dir = ROOTDIR / "archive" / "duplicate"
archive_dir = ROOTDIR / "archive"


def _discover_files() -> list:
    files = sorted(SRC_DIR.glob("*"))
    return files


def _build_alias_lookup(columns_alias_dict: dict) -> dict:
    lookup = {}
    for target_key, aliases in columns_alias_dict.items():
        cleaned_target = target_key.strip()
        lookup[cleaned_target] = cleaned_target
        
        for alias in aliases:
            lookup[alias.strip().lower()] = cleaned_target
            
    return lookup

def validate_columns(df: pd.DataFrame, column_alias: dict) -> dict:
    target_cols = set(column_alias.keys())
    current_cols = set(df.columns)
    
    target_count = len(target_cols)
    current_count = len(df.columns)
    
    # Calculate the differences using set operations
    missing_cols = list(target_cols - current_cols)
    extra_cols = list(current_cols - target_cols)
    
    if current_count < target_count:
        logger.error("Validation failed - The number of columns is less than expected.")
        logger.error(f"Expected count = {target_count} | Found count = {current_count}")
        logger.error(f"Missing cols = {missing_cols}")
        
        return {
            "status": "quarantine",
            "reason": "less_columns",
            "missing_cols": missing_cols
        }
        
    elif current_count > target_count:
        logger.error("The validation has failed because the no. of columns are greater than expected.")
        logger.error(f"Expected count = {target_count} | Found count = {current_count}")
        logger.error(f"Extra columns = {extra_cols}")
        
        return {
            "status": "quarantine",
            "reason": "more_columns",
            "extra_cols": extra_cols
        }
        
    # If the counts match, check if they are the exact identical columns
    if target_cols == current_cols:
        logger.info("Validation successful - Columns are a perfect match.")
        return {
            "status": "success",
            "reason": "perfect match"
        }
    else:
        # Mismatched column names despite equal total count
        logger.error("Validation failed - Mismatched columns (counts equal but names differ).")
        logger.error(f"Missing cols = {missing_cols} | Extra cols = {extra_cols}")
        return {
            "status": "quarantine",
            "reason": "mismatched_columns",
            "missing_cols": missing_cols,
            "extra_cols": extra_cols
        }
    
def _compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA256 hash of a raw file in chunks.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
            
    return sha256.hexdigest()