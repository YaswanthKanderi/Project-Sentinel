import os
import sys
import shutil
import glob
sys.path.insert(0, os.path.dirname(__file__))
import config
from datetime import datetime, timezone
from auth.msal_auth import authenticator
from extractors.audit_logs import AuditLogExtractor
from extractors.file_metadata import FileMetadataExtractor
from extractors.sharing_permissions import SharingPermissionsExtractor
from extractors.purview_labels import PurviewLabelExtractor
from extractors.dlp_extractor import DLPExtractor
from utils.excel_exporter import (
    export_extraction_history,
    append_file_records,
    append_permission_records,
    append_signin_summary
)
from utils.timeline import export_timeline

def validate_config():
    placeholders = [config.TENANT_ID, config.CLIENT_ID, config.CLIENT_SECRET]
    if any("YOUR_" in str(v) for v in placeholders):
        raise Exception("Fill in credentials in config.py or Azure environment variables")

def sync_to_onedrive():
    onedrive_base = r"C:\Users\vanka\OneDrive - La Trobe\Sentinel-Output"
    folders = {
        "audit": ["audit_logs_signin", "audit_logs_directory", "audit_logs_file_activity"],
        "files": ["file_metadata"],
        "permissions": ["sharing_permissions"],
        "timeline": ["governance_timeline"],
        "dlp": ["dlp_analysis"]
    }
    copied = 0
    for folder, prefixes in folders.items():
        dest = os.path.join(onedrive_base, folder)
        os.makedirs(dest, exist_ok=True)
        for prefix in prefixes:
            for f in glob.glob(os.path.join(config.OUTPUT_DIR, f"{prefix}_*.json")):
                shutil.copy2(f, dest)
                copied += 1
            for f in glob.glob(os.path.join(config.OUTPUT_DIR, f"{prefix}_*.csv")):
                shutil.copy2(f, dest)
                copied += 1
    shutil.copy2(
        os.path.join(config.OUTPUT_DIR, "extraction_history.xlsx"),
        os.path.join(onedrive_base, "extraction_history.xlsx")
    )
    print(f"Synced {copied} files to OneDrive successfully")

def run_all():
    authenticator.get_token()
    results = {}
    run_timestamp = datetime.now(timezone.utc).isoformat()
    run_summary = []

    # Audit logs
    audit_result = AuditLogExtractor().run()
    results["audit"] = audit_result
    run_summary.append({
        "timestamp": run_timestamp,
        "module": "audit_logs_signin",
        "record_count": len(audit_result.get("signin_records", [])),
        "output_file": f"audit_logs_signin_{run_timestamp[:10]}.json",
        "status": "Success"
    })
    run_summary.append({
        "timestamp": run_timestamp,
        "module": "audit_logs_directory",
        "record_count": len(audit_result.get("directory_records", [])),
        "output_file": f"audit_logs_directory_{run_timestamp[:10]}.json",
        "status": "Success"
    })
    run_summary.append({
        "timestamp": run_timestamp,
        "module": "audit_logs_file_activity",
        "record_count": len(audit_result.get("file_activity", [])),
        "output_file": f"audit_logs_file_activity_{run_timestamp[:10]}.json",
        "status": "Success"
    })

    # File metadata
    file_result = FileMetadataExtractor().run()
    results["files"] = file_result
    file_records = file_result.get("file_records", [])
    run_summary.append({
        "timestamp": run_timestamp,
        "module": "file_metadata",
        "record_count": len(file_records),
        "output_file": f"file_metadata_{run_timestamp[:10]}.json",
        "status": "Success"
    })

    # Sharing permissions
    sharing_result = SharingPermissionsExtractor().run(file_records=file_records)
    results["sharing"] = sharing_result
    perm_records = sharing_result.get("permissions", [])
    run_summary.append({
        "timestamp": run_timestamp,
        "module": "sharing_permissions",
        "record_count": len(perm_records),
        "output_file": f"sharing_permissions_{run_timestamp[:10]}.json",
        "status": "Success"
    })

    # Purview labels
    purview_result = PurviewLabelExtractor().run(file_records=file_records)
    results["purview"] = purview_result
    run_summary.append({
        "timestamp": run_timestamp,
        "module": "purview_labels",
        "record_count": len(purview_result.get("labels", [])),
        "output_file": f"purview_labels_{run_timestamp[:10]}.json",
        "status": "Success"
    })

    # DLP extraction
    dlp_result = DLPExtractor().run(file_records=file_records)
    results["dlp"] = dlp_result
    run_summary.append({
        "timestamp": run_timestamp,
        "module": "dlp_analysis",
        "record_count": len(dlp_result.get("labels", [])),
        "output_file": f"dlp_analysis_{run_timestamp[:10]}.json",
        "status": "Success"
    })

    # Export to Excel history
    export_extraction_history(run_summary)
    append_file_records(file_records)
    append_permission_records(perm_records)
    append_signin_summary(audit_result.get("analysis", {}), run_timestamp)

    # Export consolidated timeline
    export_timeline(
        file_records,
        perm_records,
        audit_result.get("signin_records", [])
    )

    # Sync to OneDrive
    sync_to_onedrive()

    print(f"\nExtraction complete. Excel history updated: {config.OUTPUT_DIR}\\extraction_history.xlsx")
    return results

if __name__ == "__main__":
    validate_config()
    run_all()