def parse_quantity(val):
    if pd.isnull(val) or str(val).strip() == "":
        return pd.NA
    val = str(val).strip()
    if str(val).lower() == "nan":
        return pd.NA
    try:
        n_val = float(val)
        return float(abs(n_val))
    except ValueError:
        return val
    