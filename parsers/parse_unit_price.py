def parse_unit_price(val):
    if pd.isnull(val) or str(val).strip()=="":
        return pd.NA
    val = str(val).strip()
    if val.lower()=='inf':
        return pd.NA
    val = val.replace("Rs.","").replace("$","").strip()
    val = val.replace(",","")
    val = val.rstrip("#").rstrip(".").strip()

    try:
        return float(val)
    except ValueError:
        return val