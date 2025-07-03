# utils/cleaner.py
def clean_data(data):
    """Clean vendor result data by trimming whitespace and removing any PII fields."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            # If value is string, trim whitespace
            if isinstance(v, str):
                v = v.strip()
            # Remove PII fields (simple check for common keys)
            if k.lower() in ("email", "phone", "ssn"):
                cleaned[k] = None  # redacted
            else:
                cleaned[k] = clean_data(v)  # recurse for nested structures
        return cleaned
    elif isinstance(data, list):
        return [clean_data(item) for item in data]
    else:
        # Primitive (int, float, etc.) or unknown type, return as is
        return data
