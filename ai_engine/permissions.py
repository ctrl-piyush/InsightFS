import logging

SENSITIVE_KEYWORDS = {
    "password", "secret", "private_key", "confidential", 
    "ssn", "credit_card", "api_key", "token"
}

# Only scan text-based files
SCAN_MIMES = {
    "text/plain", "text/csv", "application/json", "application/xml",
    "application/x-sh", "application/x-python"
}

def check_sensitivity(filepath, mime_type):
    """Scans text-based files for sensitive keywords."""
    if mime_type not in SCAN_MIMES:
        return False
        
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Scan first 100 lines for performance
            for i, line in enumerate(f):
                if i > 100:
                    break
                line_lower = line.lower()
                for keyword in SENSITIVE_KEYWORDS:
                    if keyword in line_lower:
                        logging.info(f"Sensitive keyword '{keyword}' found in {filepath}")
                        return True
        return False
    except FileNotFoundError:
        return False # File might be gone
    except Exception as e:
        logging.warning(f"Error scanning {filepath} for sensitivity: {e}")
        return False
