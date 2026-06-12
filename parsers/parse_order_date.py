import pandas as pd
from datetime import datetime
import os

IST_OFFSET = pd.Timedelta(hours=5, minutes=30)

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%b %d, %Y",
    "%d-%b-%Y",
]

QUARANTINE_DIR = os.path.join("quarantine", "quarantine_date")


def _parse_order_date(val):
    """
    Protected — handles one value only.
    Returns parsed datetime if successful.
    Returns NaT for null/empty.
    Returns val as-is if parsing fails.
    """
    if pd.isnull(val) or str(val).strip() == "":
        return pd.NaT

    val = str(val).strip()

    if val.isdigit():
        return pd.Timestamp(int(val), unit='s') + IST_OFFSET

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue

    return val  # parsing failed — comes back as string


def clean_date(df, original_df):
    """
    1. Parse order_date into order_date_parsed
    2. Identify failed rows — still strings in order_date_parsed
    3. Cut failed rows → quarantine file from original_df
    4. Drop order_date, rename order_date_parsed → order_date
    5. Cast to datetime dtype
    6. Return clean df without index reset
    """

    
    # step 1 — parse into new column
    df['order_date_parsed'] = df['order_date'].apply(_parse_order_date)

    # step 2 — identify failed rows
    unparsed_mask  = df['order_date_parsed'].apply(lambda x: isinstance(x, str))
    failed_indexes = df[unparsed_mask].index.tolist()

    
    # step 3 — quarantine from original_df
    if failed_indexes:
        os.makedirs(QUARANTINE_DIR, exist_ok=True)

        quarantine_rows = original_df.loc[failed_indexes].copy()
        #quarantine_rows['quarantine_reason']    = 'clean_date'
        #quarantine_rows['quarantine_timestamp'] = pd.Timestamp.now()

        quarantine_path = os.path.join(
            QUARANTINE_DIR,
            f"quarantine_date_{pd.Timestamp.now().strftime('%d-%m-%Y')}.csv"
        )
        quarantine_rows.to_csv(quarantine_path, index=False)
        #print(f"clean_date — {len(failed_indexes)} rows quarantined → {quarantine_path}")
    #else:
     #   print("clean_date — no rows quarantined")

    # step 4 — remove failed rows from working df
    clean_df = df.drop(index=failed_indexes)

    # step 5 — drop original order_date column
    #         — rename order_date_parsed → order_date
    clean_df = clean_df.drop(columns=['order_date'])
    clean_df = clean_df.rename(columns={'order_date_parsed': 'order_date'})

    # step 6 — cast to datetime dtype
    clean_df['order_date'] = pd.to_datetime(
        clean_df['order_date'], errors='coerce'
    )

    # no reset_index — caller decides when to reset
    return clean_df, failed_indexes