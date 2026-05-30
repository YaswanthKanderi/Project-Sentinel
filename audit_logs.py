import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from auth.msal_auth import get_headers
from utils.throttle_handler import make_request_with_retry
from utils.exporter import export_to_json, export_summary, export_to_csv
from utils.logger import get_logger
from collections import Counter

logger = get_logger("audit_logs")

class AuditLogExtractor:
    def __init__(self):
        self.base_url = config.GRAPH_BASE_URL
        self.page_size = config.PAGE_SIZE

    def extract_signin_logs(self):
        logger.info("Extracting sign-in logs...")
        url = f"{self.base_url}/auditLogs/signIns"
        params = {"$top": self.page_size, "$filter": f"createdDateTime ge {config.AUDIT_START_DATE} and createdDateTime le {config.AUDIT_END_DATE}"}
        return self._paginate(url, params, "SignIns")

    def extract_directory_audits(self):
        logger.info("Extracting directory audits...")
        url = f"{self.base_url}/auditLogs/directoryAudits"
        params = {"$top": self.page_size}
        return self._paginate(url, params, "DirectoryAudits")

    def extract_sharepoint_file_activity(self):
        logger.info("Extracting SharePoint file activity from directory audits...")
        url = f"{self.base_url}/auditLogs/directoryAudits"
        params = {"$top": self.page_size}
        try:
            records = self._paginate(url, params, "SharePointActivity")
        except Exception as ex:
            logger.warning(f"Could not extract SharePoint activity: {ex}")
            return []

        file_keywords = ["file", "document", "sharepoint", "upload", "download", "edit", "modify"]
        file_events = []
        for r in records:
            operation = (r.get("activityDisplayName") or "").lower()
            service = (r.get("loggedByService") or "").lower()
            if any(k in operation for k in file_keywords) or "sharepoint" in service:
                targets = r.get("targetResources") or []
                target = targets[0] if targets else {}
                initiated_by = r.get("initiatedBy") or {}
                user = initiated_by.get("user") or {}
                file_events.append({
                    "activity_time": r.get("activityDateTime"),
                    "operation": r.get("activityDisplayName"),
                    "service": r.get("loggedByService"),
                    "user_email": user.get("userPrincipalName"),
                    "file_name": target.get("displayName"),
                    "file_id": target.get("id"),
                    "result": r.get("result")
                })
        logger.info(f"SharePoint file events found: {len(file_events)}")
        return file_events

    def _paginate(self, url, params, label):
        headers = get_headers()
        all_records = []
        page = 1
        current_url = url
        current_params = params
        while current_url:
            logger.info(f"{label} page {page}...")
            r = make_request_with_retry(current_url, headers, current_params if page == 1 else None)
            data = r.json()
            records = data.get("value", [])
            all_records.extend(records)
            logger.info(f"Page {page}: {len(records)} records")
            current_url = data.get("@odata.nextLink")
            page += 1
        return all_records

    def analyse_signin_logs(self, records):
        if not records: return {}
        statuses = Counter(r.get("status", {}).get("errorCode", "unknown") for r in records)
        success = statuses.get(0, 0)
        failed = sum(v for k,v in statuses.items() if k != 0)
        risky = [r for r in records if r.get("riskLevelDuringSignIn") in ("medium","high")]
        return {
            "total_records": len(records),
            "successful_logins": success,
            "failed_logins": failed,
            "risky_signins": len(risky),
            "governance_flags": {
                "high_failure_rate": failed/len(records) > 0.3 if records else False,
                "risky_signin_present": len(risky) > 0
            }
        }

    def analyse_file_activity(self, records):
        if not records: return {}
        operations = Counter(r.get("operation") for r in records)
        users = Counter(r.get("user_email") for r in records if r.get("user_email"))
        return {
            "total_file_events": len(records),
            "operations_breakdown": dict(operations.most_common(10)),
            "most_active_users": dict(users.most_common(5))
        }

    def run(self):
        signin = self.extract_signin_logs()
        directory = self.extract_directory_audits()
        file_activity = self.extract_sharepoint_file_activity()

        if signin:
            export_to_json(signin, "audit_logs_signin")
            export_to_csv(signin, "audit_logs_signin")
        if directory:
            export_to_json(directory, "audit_logs_directory")
            export_to_csv(directory, "audit_logs_directory")
        if file_activity:
            export_to_json(file_activity, "audit_logs_file_activity")
            export_to_csv(file_activity, "audit_logs_file_activity")

        analysis = self.analyse_signin_logs(signin)
        file_analysis = self.analyse_file_activity(file_activity)

        if analysis:
            export_summary(analysis, "audit_logs_signin")
        if file_analysis:
            export_summary(file_analysis, "audit_logs_file_activity")

        return {
            "signin_records": signin,
            "directory_records": directory,
            "file_activity": file_activity,
            "analysis": analysis,
            "file_analysis": file_analysis
        }