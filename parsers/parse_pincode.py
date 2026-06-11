def parse_pincode(val):
    if pd.isnull(val) or str(val).strip() == "":
        return pd.NA
    val = str(val).strip()
    val = val.replace("_dup","")
    if str(val).lower() == "duplicate":
        return pd.NA
    try:
        return int(val)
    except ValueError:
        return val