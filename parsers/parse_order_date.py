from datetime import datetime
ist_offset = pd.Timedelta(hours = 5,minutes = 30)

def parse_order_date(val):
    date_formats= [
        "%Y-%m-%d", # 2023-09-2026
        "%d/%m/%Y", # 26/09/2023
        "%d-%m-%Y", # 17-01-2024
        "%b %d, %Y",# Sep 20, 2023
        "%d-%b-%Y", # 13-Jun-2024
    ]

    if pd.isnull(val) or str(val).strip()=="":
        return pd.NaT
    
    if val.isdigit():
        return pd.Timestamp(int(val),unit='s') + ist_offset
    
    for fmt in date_formats:
        try:
            return datetime.strptime(val,fmt)
        except ValueError:
            continue
    return val


