def parse_total_amount(val):
    if pd.isnull(val) or str(val).strip()=="":
        return pd.NA
    val = str(val).strip()
    val = val.replace("Rs","").replace("$","").replace("-","")
    val = val.replace(",","").strip()
    try:
        return float(val)
    except ValueError:
        return val