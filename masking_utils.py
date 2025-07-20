import re
import json

def load_patterns(json_path="sensitive_patterns.json"):
    with open(json_path, "r") as f:
        return json.load(f)

def mask_sensitive(text, patterns):
    for label, pattern in patterns.items():
        text = re.sub(pattern, f"***{label.upper()}***", text)
    return text