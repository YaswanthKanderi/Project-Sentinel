import json
import os
import csv
from datetime import datetime, timezone
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

os.makedirs(config.OUTPUT_DIR, exist_ok=True)

def export_to_json(data, module_name, metadata=None):
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{module_name}_{ts}.json"
    filepath = os.path.join(config.OUTPUT_DIR, filename)
    output = {
        "sentinel_export": {
            "schema_version": "1.0",
            "project": "Project Sentinel",
            "module": module_name,
            "extraction_time": datetime.now(timezone.utc).isoformat(),
            "record_count": len(data)
        },
        "metadata": metadata or {},
        "records": data
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    return filepath

def export_to_csv(data, module_name):
    if not data:
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{module_name}_{ts}.csv"
    filepath = os.path.join(config.OUTPUT_DIR, filename)
    # Flatten nested fields for CSV
    flat_data = []
    for record in data:
        flat = {}
        for k, v in record.items():
            if isinstance(v, (dict, list)):
                flat[k] = json.dumps(v, default=str)
            else:
                flat[k] = v
        flat_data.append(flat)
    headers = list(flat_data[0].keys()) if flat_data else []
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(flat_data)
    return filepath

def export_summary(summaries, module_name):
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{module_name}_SUMMARY_{ts}.json"
    filepath = os.path.join(config.OUTPUT_DIR, filename)
    output = {
        "sentinel_summary": {
            "schema_version": "1.0",
            "module": module_name,
            "generated_at": datetime.now(timezone.utc).isoformat()
        },
        "findings": summaries
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    return filepath