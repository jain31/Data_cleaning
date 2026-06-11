def parse_discount(val):
    if pd.isnull(val) or str(val).strip()=="":
        return pd.NA
    
    val = str(val).strip()
    val = val.replace("%","").replace("_dup","")

    if str(val) == "_dup":
        return pd.NA

    try:
        return float(val)
    except ValueError:
        return val