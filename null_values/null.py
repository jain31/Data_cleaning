"""
null.py - null_values/null.py
Null- value imputation and validation for the data-cleaning pipeline.
All activity logs to logs/null.log (+Airflow StreamHandler via StreamHandler).

PUBLIC API
_____
    handle_nulls(df, original_filename,date_cols,continuous_cols,categorical_cols)
       -> (clean_df, quarantine_df,report_dict)
PIPELINE PER COLUMN
________________
1. If Null%>25% for a column -> those rows are quarntined immediately.
    The remaining rows (null%<=25%) go forward to imputation.
2. Date columns->forward-fill first,then backward-fill.
3. Continuous columns -> skewness check:
                        |skew| <= 0.5 -> mean imputation
                        |skew| > 0.5 -> median imputation
4. Categorial columns -> mode imputation.

VALIDATION AFTER IMPUTATION
____________
* Continuous ->Welch two sample t-test (original non-null vs impiuted values)
* categorial -> Chi-square goodness-of-fit test (pre vss post distribution)

QUARNTINE
__________________

Rows quarantined because null% >25% are written to:
    quarantine/null_quarantine/<uuid>_null_<YYYY-MM-DD>_<original_filename>.csv

where <original_filename> is derived from the file that produced the dataframe.
    """

import uuid
import os
from datetime import datetime
from pathlib import Path
from scipy import stats

from logger_file.logger import null_logger as log
#_______paths_________
_ROOT   = Path(__file__).resolve().parent.parent
QUARANTINE_DIR =_ROOT/"quarantine"/"null_quarantine"
QUARANTINE_DIR.mkdir(parents=True, exist_ok= True)

#_____thresholds_____________
NULL_QUARANTINE_THERSHOLD = 0.25    #NULL%>25% GOTO QUARNATINE
SKEW_THERSHOLD = 0.5                #|SKEW|>0.5 ->MEDIAN ELSE MEAN
P_VALUE_THERSHOLD = 0.05            #VALIDATION:P<0.05 RAISES A WARNING

#PRIVATE HELPERS

def _null_pct(series: pd.Series)->float:
    return series.isna().sum() / len(series) if len(series) > 0 else 0.0

def _quarantine_rows(df: pd.DataFrame, mask : pd.Series,col:str, original_filename:str)->pd.DataFrame:
    quarantine_df = df[mask].copy()
    if quarantine_df.empty:
        return quarantine_df
    date_str=datetime.now().strftime("%Y_%m-%d")
    uid = uuid.uuid4().hex[:8]
    stem = Path(original_filename).stem
    filename = f"{uid}_null_{date_str}_{stem}.csv"
    dest = QUARANTINE_DIR/filename

    quarantine_df.to_csv(dest,index=False)
    log.warning(
        f"action=quarntine_rows | col={col}"
        f"| rows_quarantined = {len(quarantine_df)}"
        f"| null_pct={mask.mean():.1%}>{NULL_QUARANTINE_THERSHOLD:.0%} threshold"
        f"| dest={dest}"
    )
    return quarantine_df

# IMPUTATION FUNCTIONS

