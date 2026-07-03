from pathlib import Path 

from datetime import datetime
import pandas as pd
import hashlib


ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR/"src"
ARCHIVE_DUPLICATE_DIR = ROOT_DIR / "archive" / "duplicate"
ARCHIVE_DIR           = ROOT_DIR / "archive"

# First Helper Function

def _discover_files()->list:
    files = sorted(SRC_DIR.glob("*.csv"))
    return files

def _build_alias_lookup(columns_alias:dict)->dict:
    lookup = {}
    for target_key,aliases in columns_alias.items():
        cleaned_target = target_key.strip().lower()
        lookup[cleaned_target] = cleaned_target
        
        for alias in aliases:
            lookup[alias.strip().lower()] = cleaned_target
    return lookup

def _remap_columns(cols:list,lookup:dict):
    return [lookup.get(str(col).strip().lower(),col) for col in cols]

def _validate_columns(df:pd.DataFrame,column_alias:dict)->dict:
    """
    Here we validate columns of enforced dataframe against target schema keys and 
    identify column count mis-matches,missing columns extra-columns and then check for un-expected or 
    new columns
    """

    target_cols = set(column_alias.keys())
    current_cols = set(df.columns)

    target_count = len(target_cols)
    current_count = len(df.columns.tolist())

    # Now we calculate the difference using set operations

    missing_cols = list(target_cols-current_cols)
    extra_cols = list(current_cols-target_cols)

    if current_count<target_count:
        print(f"validation failed - The number of columns are less than expected ")
        print(f"expected count = {target_count} | found count {current_count}")
        print(f"missing cols = {missing_cols}")

        return {
            "status":"quarantine",
            "reason":"len_columns",
            "missing_cols":missing_cols
        }
    
    elif current_count>target_count:
        print(f"The validation has failed as no. of column are extra ")
        print(f"expected cols : {target_count} | found count = {current_count}")
        print(f"Extra columns : {extra_cols}")
        
        return{
            "status":"quarentine",
            "reason":"more columns",
            "extra_cols":extra_cols
        }
    
    elif current_cols!=target_cols:
        print(
            f"validation failed column count matches = ({current_count} = {target_count})"
        )
        print(f"But the column names do not match")
        print(f"missing cols = {missing_cols}")
        print(f"extra cols = {extra_cols}")

        return {
            "status":"quarantine",
            "reason":"Schema mis- match",
            "missing cols":missing_cols,
            "extra cols":extra_cols
        }
    log.info(f"action=validate_columns | status=success | columns={target_count}")
    return {"status": "success", "reason":"perfect_match"}            
 
# ──────────────────────────────────────────────
# STEP 3 — file-level duplicate check via hash
# ──────────────────────────────────────────────
 
def _compute_file_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    file_hash = sha256.hexdigest
    log.debug(f"action=compute_file_hash | file ={file_path.name} | hash={file_hash{:12}}...")
    return file_hash
 
 
def _check_file_duplicate(conn, raw_content_hash: str) -> tuple
    sql = """
        SELECT file_uuid FROM bronze_raw
        WHERE raw_content_hash = %s
          AND is_duplicate = 0
          AND bronze_status = 'success'
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(sql, (raw_content_hash,))
        row = cur.fetchone()
 
    if row:
        print(f"duplicate file detected - matches existing file_uuid = {row[0]}")
        return True, row[0]
 
    print(f"file hash is unique - no duplicate found in bronze_raw")
    return False, None
 
 
# ──────────────────────────────────────────────
# STEP 4 — row-level incremental load check
# ──────────────────────────────────────────────
 
def _check_incremental_rows(df: pd.DataFrame, conn) -> pd.DataFrame:
    """
    Checks the gold table for order_ids that already exist.
    Returns only the rows from df whose order_id is NOT already in gold --
    these are the genuinely new rows that need to go through silver processing.
 
    The complete original file is always archived regardless of this result.
    Only this filtered dataframe is passed downstream to the silver stage.
    """
    incoming_order_ids = df["order_id"].dropna().unique().tolist()
 
    if not incoming_order_ids:
        print(f"no order_ids found in incoming file - returning empty dataframe")
        return df.iloc[0:0]   # empty df, same columns, no rows
 
    # build a placeholder string for the SQL IN clause -- one %s per id
    placeholders = ", ".join(["%s"] * len(incoming_order_ids))
 
    sql = f"""
        SELECT order_id FROM gold_processed
        WHERE order_id IN ({placeholders})
    """
    with conn.cursor() as cur:
        cur.execute(sql, incoming_order_ids)
        existing_rows = cur.fetchall()
 
    existing_order_ids = set(row[0] for row in existing_rows)
 
    incremental_df = df[~df["order_id"].isin(existing_order_ids)].copy()
 
    total_incoming    = len(df)
    total_existing    = len(existing_order_ids)
    total_incremental = len(incremental_df)
 
    print(f"incoming rows    = {total_incoming}")
    print(f"already in gold  = {total_existing}")
    print(f"new rows to load = {total_incremental}")
 
    return incremental_df
 
 
# ──────────────────────────────────────────────
# STEP 5 — archive the file
# ──────────────────────────────────────────────
 
def _archive_file(file_path: Path, is_duplicate: bool) -> Path:
    """
    Moves the complete raw file to the correct archive folder.
    This always happens on the full original file -- the incremental
    filtering in step 4 only affects what goes downstream, not what
    gets archived.
    """
    today = datetime.now().strftime("%Y%m%d")
 
    if is_duplicate:
        dest_dir = ARCHIVE_DUPLICATE_DIR / today
    else:
        dest_dir = ARCHIVE_DIR / today
 
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file_path.name
    file_path.rename(dest_path)
 
    print(f"file archived to -> {dest_path}")
    return dest_path
 
 
# ──────────────────────────────────────────────
# ORCHESTRATOR — ties all steps together
# ──────────────────────────────────────────────
 
def process_file(file_path: Path, column_alias: dict, conn) -> pd.DataFrame | None:
    """
    Runs one file through the full ingestion pipeline.
    Returns the incremental dataframe (new rows only) if the file passes
    all checks -- this is what gets passed to the silver stage.
    Returns None if the file fails schema validation or is a duplicate.
    """
    print(f"\n{'='*55}")
    print(f"processing : {file_path.name}")
    print(f"{'='*55}")
 
    # STEP 2 -- schema enforcement
    df     = pd.read_csv(file_path)
    lookup = _build_alias_lookup(column_alias)
    df.columns = _remap_columns(list(df.columns), lookup)
 
    validation_result = _validate_columns(df, column_alias)
    if validation_result["status"] != "success":
        print(f"file routed to quarantine - reason: {validation_result['reason']}")
        return None
 
    # STEP 3 -- file-level duplicate check
    raw_content_hash          = _compute_file_hash(file_path)
    is_duplicate, original_id = _check_file_duplicate(conn, raw_content_hash)
 
    # STEP 4 -- row-level incremental check (only if file is not a duplicate)
    if is_duplicate:
        _archive_file(file_path, is_duplicate=True)
        return None
 
    incremental_df = _check_incremental_rows(df, conn)
 
    # STEP 5 -- archive the complete original file
    _archive_file(file_path, is_duplicate=False)
 
    if incremental_df.empty:
        print(f"no new rows to load - all order_ids already exist in gold")
        return None
 
    print(f"returning {len(incremental_df)} new rows to silver stage")
    return incremental_df


print(ROOT_DIR)




# def _check_file_duplicate(conn, etag_data: str) -> tuple
#     sql = """
#         SELECT file_uuid FROM bronze_raw
#         WHERE etag_data = %s
#           AND is_duplicate = 0
#           AND bronze_status = 'success'
#         LIMIT 1
#     """
#     with conn.cursor() as cur:
#         cur.execute(sql, (etag_data,))
#         row = cur.fetchone()
 
#     if row:
#       log.warning = (f"action=check_file_duplicate | status=duplicate | matches_uuid={row[0]}")
#       return True, row[0]
# log.info("action=check_file_duplicate | status=unique")
# return False,None

def _check_incremental_rows(df: pd.DataFrame, conn) -> pd.DataFrame:
    incoming_ids = df["order_id"].dropna().unique().tolist()
 
    if not incoming_ids:
       log.warning("action=check_increment_rows | statu=empty | no_order_idea_found")
       return df.iloc[0:0]   # empty df, same columns, no rows
 
    # build a placeholder string for the SQL IN clause -- one %s per id
    placeholders = ", ".join(["%s"] * len(incoming_ids))
 
    sql = f"""
        SELECT order_id FROM orders_clean
        WHERE order_id IN ({placeholders})
    """
    with conn.cursor() as cur:
        cur.execute(sql, incoming_ids)
        existing_ids= {row[0] for row in cur.fetchall()}
        
    incremental_df = df[~df["order_id"].isin(existing_ids)].copy()

    log.info(
        f"action=check_increment_rows"
        f"| incoming={len(df)} | already_loaded={len(existing_ids)}"
        f"| new_rows={len(incremental_df)}"
    )
    return incremental_df

#step5
def _archive_file(file_path: Path,is_duplicate: bool)-> Path:
    today = datetime.now().strftime("%y%m%d")
    dest_dir = (ARCHIVE_DUPLICATE_DIR if is_duplicate else ARCHIVE_DIR) / today
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir/file_path.name
    file_path.rename(dest_path)
    lod.info(
        f"action=archive_file | file={file_path.name}"
        f"| is_duplicate={is_duplicate} | dest={dest_path}"
    )
    return dest_path