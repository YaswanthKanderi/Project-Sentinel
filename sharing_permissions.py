import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from auth.msal_auth import get_headers
from utils.throttle_handler import make_request_with_retry
from utils.exporter import export_to_json, export_summary, export_to_csv
from utils.logger import get_logger
from collections import Counter

logger = get_logger("sharing_permissions")

class SharingPermissionsExtractor:
    def __init__(self):
        self.base_url = config.GRAPH_BASE_URL
        self.page_size = config.PAGE_SIZE

    def get_file_permissions(self, drive_id, item_id, file_name):
        url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/permissions"
        headers = get_headers()
        try:
            r = make_request_with_retry(url, headers)
            perms = r.json().get("value", [])
            return [self._normalise(p, drive_id, item_id, file_name) for p in perms]
        except Exception as ex:
            logger.warning(f"Could not get permissions for {file_name}: {ex}")
            return []

    def _normalise(self, perm, drive_id, item_id, file_name):
        link = perm.get("link", {})
        granted = perm.get("grantedTo", {})
        granted_identities = perm.get("grantedToIdentities", [])

        email = granted.get("user", {}).get("email")
        if not email and granted_identities:
            email = granted_identities[0].get("user", {}).get("email")

        scope = link.get("scope")
        is_anon = scope == "anonymous"

        return {
            "permission_id": perm.get("id"),
            "file_id": item_id,
            "drive_id": drive_id,
            "file_name": file_name,
            "link_scope": scope,
            "link_type": link.get("type"),
            "link_url": link.get("webUrl"),
            "granted_to_email": email,
            "roles": perm.get("roles", []),
            "is_anonymous": is_anon,
            "expiry": perm.get("expirationDateTime"),
            "has_password": link.get("preventsDownload") is not None,
            "identity_count": len(granted_identities)
        }

    def analyse_permissions(self, perms):
        if not perms: return {}
        anonymous = [p for p in perms if p.get("is_anonymous")]
        external = [p for p in perms if p.get("granted_to_email") and "#EXT#" in str(p.get("granted_to_email"))]
        return {
            "total_permissions": len(perms),
            "anonymous_links": len(anonymous),
            "external_users": len(external),
            "governance_flags": {
                "anonymous_links_present": len(anonymous) > 0,
                "high_external_exposure": len(external) > 10
            }
        }

    def run(self, file_records=None):
        if not file_records:
            logger.warning("No file records provided.")
            return {}
        all_perms = []
        for f in file_records:
            drive_id = f.get("drive_id")
            item_id = f.get("file_id")
            name = f.get("file_name", "Unknown")
            if not drive_id or not item_id:
                continue
            perms = self.get_file_permissions(drive_id, item_id, name)
            all_perms.extend(perms)

        if all_perms:
            export_to_json(all_perms, "sharing_permissions")
            export_to_csv(all_perms, "sharing_permissions")

        analysis = self.analyse_permissions(all_perms)
        if analysis:
            export_summary(analysis, "sharing_permissions")

        return {"permissions": all_perms, "analysis": analysis}