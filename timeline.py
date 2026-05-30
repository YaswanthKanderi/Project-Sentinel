import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.exporter import export_to_json, export_to_csv
from utils.logger import get_logger

logger = get_logger("timeline")

def build_timeline(file_records, perm_records, audit_records):
    logger.info("Building consolidated timeline...")
    events = []

    # File creation and modification events
    for f in file_records:
        if f.get("created_datetime"):
            events.append({
                "timestamp": f.get("created_datetime"),
                "event_type": "FILE_CREATED",
                "actor": f.get("created_by_email"),
                "target": f.get("file_name"),
                "site": f.get("site_name"),
                "detail": f"File created in {f.get('drive_name')}",
                "sensitivity_label": f.get("sensitivity_label") or "Unlabelled",
                "is_shared": f.get("is_shared")
            })
        if f.get("modified_datetime") and f.get("modified_datetime") != f.get("created_datetime"):
            events.append({
                "timestamp": f.get("modified_datetime"),
                "event_type": "FILE_MODIFIED",
                "actor": f.get("modified_by_email"),
                "target": f.get("file_name"),
                "site": f.get("site_name"),
                "detail": f"File modified — version {f.get('version_count', 1)}",
                "sensitivity_label": f.get("sensitivity_label") or "Unlabelled",
                "is_shared": f.get("is_shared")
            })
        # Version history events
        for v in f.get("versions", []):
            if v.get("version_id") and v.get("version_id") != "1.0":
                events.append({
                    "timestamp": v.get("modified_at"),
                    "event_type": "VERSION_CREATED",
                    "actor": v.get("modified_by"),
                    "target": f.get("file_name"),
                    "site": f.get("site_name"),
                    "detail": f"Version {v.get('version_id')} created — size {v.get('size_bytes')} bytes",
                    "sensitivity_label": f.get("sensitivity_label") or "Unlabelled",
                    "is_shared": f.get("is_shared")
                })

    # Permission events
    for p in perm_records:
        if p.get("granted_to_email"):
            events.append({
                "timestamp": None,
                "event_type": "PERMISSION_GRANTED",
                "actor": "System",
                "target": p.get("file_name"),
                "site": None,
                "detail": f"Access granted to {p.get('granted_to_email')} — role: {p.get('roles')}",
                "sensitivity_label": None,
                "is_shared": p.get("is_anonymous")
            })

    # Audit signin events
    for a in audit_records:
        events.append({
            "timestamp": a.get("createdDateTime"),
            "event_type": "USER_SIGNIN",
            "actor": a.get("userPrincipalName"),
            "target": None,
            "site": None,
            "detail": f"Sign-in via {a.get('appDisplayName')} — result: {a.get('status', {}).get('errorCode', 'unknown')}",
            "sensitivity_label": None,
            "is_shared": None
        })

    # Sort by timestamp
    events = [e for e in events if e.get("timestamp")]
    events.sort(key=lambda x: x["timestamp"])

    logger.info(f"Timeline built — {len(events)} events")
    return events

def export_timeline(file_records, perm_records, audit_records):
    events = build_timeline(file_records, perm_records, audit_records)
    if events:
        export_to_json(events, "governance_timeline")
        export_to_csv(events, "governance_timeline")
    return events