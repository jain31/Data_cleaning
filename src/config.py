# config.py
"""
Centralized Configuration for a Modular, Quarantine-driven ETL Pipeline.
Each column configuration contains specific extraction, cleaning, validation bounds,
and tracking settings required by individual column parser modules.
"""

import os

# =====================================================================
# 1. GLOBAL & METADATA SETTINGS
# =====================================================================
PIPELINE_NAME = "dirty_dataset_etl"
VERSION = "2.1.0"
ENVIRONMENT = "development"

# Global string representations that should be immediately treated as real null values (NaN/None)
GLOBAL_NULL_INDICATORS = {
    "nan", "null", "n/a", "unknown", "inf", "-inf", "", "none", "cust_???", "cust_"
}

# =====================================================================
# 2. FILE PATHS & QUARANTINE DIRECTORIES
# =====================================================================
FILE_PATHS = {
    "source_file": "dirty_dataset.csv",
    "clean_output_file": "cleaned_dataset.csv",
    # Main parent directories for quarantine outputs
    "quarantine_base_dir": "quarantine",
}

# =====================================================================
# 3. INDIVIDUAL COLUMN PARSER DICTIONARIES
# =====================================================================
COLUMN_CONFIGS = {
    "order_id": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_order_id"),
        "strip_whitespace": True,
        "uppercase": True,
        "allow_null": False,  # If missing or unparseable, quarantine row
        "regex_pattern": r"^ORD_\d+$"  # Optional pattern match validation
    },
    
    "customer_id": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_customer_id"),
        "strip_whitespace": True,
        "uppercase": True,
        "allow_null": False,
    },
    
    "product_name": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_product_name"),
        "strip_whitespace": True,
        "title_case": True,
        "allow_null": False,
    },
    
    "order_date": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_date"),
        "date_formats": [
            "%Y-%m-%d",  # 2023-09-26
            "%d/%m/%Y",  # 26/09/2023
            "%d-%m-%Y",  # 17-01-2024
            "%b %d, %Y", # Sep 26, 2023
            "%d-%b-%Y",  # 13-Jun-2024
        ],
        "timezone_offset_hours": 5,
        "timezone_offset_minutes": 30,
        "allow_null": False,
    },
    
    "discount_pct": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_discount"),
        "strip_chars": ["%", " ", "-"],
        "min_value": 0,
        "max_value": 100,
        "allow_null": True,
        "default_on_null": 0.0  # Optional fallback if allowed to be null but needs a number
    },
    
    "unit_price": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_unit_price"),
        "strip_chars": ["Rs.", "$", "#", ",", " "],
        "min_value": 0.0,
        "allow_null": False,
    },
    
    "quantity": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_quantity"),
        "strip_chars": [" ", ","],
        "min_value": 1,
        "max_value": 2000,  # Quarantine extreme outliers like 9999
        "allow_null": False,
    },
    
    "total_amount": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_total_amount"),
        "strip_chars": ["Rs.", "$", ",", " "],
        "min_value": 0.0,
        "allow_null": True,
    },
    
    "status": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_status"),
        "standard_mapping": {
            "p3nding": "Pending", "pending": "Pending", "pending ": "Pending",
            "canc": "Cancelled", "cancelled": "Cancelled",
            "delivered": "Delivered", "ship": "Shipped",
            "returned": "Returned", "returned ": "Returned"
        },
        "allow_null": False,
    },
    
    "category": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_category"),
        "standard_mapping": {
            "electronicss": "Electronics", "electronics": "Electronics", "elec": "Electronics",
            "accessories": "Accessories", "acce": "Accessories",
            "stationery": "Stationery", "stationerys": "Stationery"
        },
        "allow_null": False,
    },
    
    "payment_method": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_payment"),
        "standard_mapping": {
            "credit card": "Credit Card", "debit card": "Debit Card",
            "wallet": "Wallet", "upi": "UPI", "net banking": "Net Banking"
        },
        "allow_null": True,
    },
    
    "rating": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_rating"),
        "strip_chars": ["stars", "star", " "],
        "text_to_numeric_map": {"good": 4.0, "bad": 1.0, "excellent": 5.0}, # Cleans text ratings like "Good"
        "min_value": 0.0,
        "max_value": 5.0,
        "allow_null": True,
    },
    
    "pincode": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_pincode"),
        "regex_extract": r"(\d{5,6})",  # Ensures valid pin code lengths
        "allow_null": True,
    },
    
    "phone": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_phone"),
        "strip_chars": ["-", " ", "+"],
        "valid_lengths": [10, 12],  # Accounts for numbers with or without country codes
        "allow_null": True,
    },
    
    "city": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_city"),
        "strip_chars": [","],  # Drops trailing punctuation
        "title_case": True,
        "allow_null": True,
    },
    
    "state": {
        "quarantine_sub_dir": os.path.join(FILE_PATHS["quarantine_base_dir"], "quarantine_state"),
        "standard_mapping": {
            "tamil nadu": "Tamil Nadu",
            "maharashtra": "Maharashtra", "m@h@r@shtr@": "Maharashtra",
            "karnataka": "Karnataka", "rajasthan": "Rajasthan", "gujarat": "Gujarat"
        },
        "allow_null": True,
    }
}