import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from auth.msal_auth import get_headers
from utils.throttle_handler import make_request_with_retry
from utils.exporter import export_to_json, export_summary, export_to_csv
from utils.logger import get_logger
from collections import Counter

logger = get_logger("file_metadata")

class FileMetadataExtractor:
    def __init__(self):
        self.base_url = config.GRAPH_BASE_URL
        self.page_size = config.PAGE_SIZE

    def get_all_sites(self):
        url = f"{self.base_url}/sites"
        return self._paginate(url, {"search": "*", "$top": self.page_size}, "Sites")

    def get_drives_for_site(self, site_id, site_name):
        url = f"{self.base_url}/sites/{site_id}/drives"
        try:
            return self._paginate(url, {"$top": self.page_size}, f"Drives[{site_name}]")
        except Exception as ex:
            logger.warning(f"Skipping drives for site {site_name}: {ex}")
            return []

    def get_files_in_drive(self, drive_id, drive_name):
        return self._get_files_recursive(drive_id, "root", drive_name)

    def _get_files_recursive(self, drive_id, item_id, drive_name):
        url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/children"
        params = {"$top": self.page_size, "$expand": "listItem($expand=fields)"}
        try:
            items = self._paginate(url, params, f"Files[{drive_name}]")
        except Exception as ex:
            logger.warning(f"Skipping folder in drive {drive_name}: {ex}")
            return []
        files = []
        for i in items:
            if "file" in i:
                files.append(i)
            elif "folder" in i:
                files.extend(self._get_files_recursive(drive_id, i["id"], drive_name))
        return files

    def normalise_file_record(self, item, drive_id, drive_name, site_name, site_url):
        fields = item.get("listItem", {}).get("fields", {})
        return {
            "file_id": item.get("id"),
            "file_name": item.get("name"),
            "web_url": item.get("webUrl"),
            "site_name": site_name,
            "site_url": site_url,
            "drive_id": drive_id,
            "drive_name": drive_name,
            "size_bytes": item.get("size"),
            "created_datetime": item.get("createdDateTime"),
            "modified_datetime": item.get("lastModifiedDateTime"),
            "created_by_email": item.get("createdBy", {}).get("user", {}).get("email"),
            "modified_by_email": item.get("lastModifiedBy", {}).get("user", {}).get("email"),
            "sensitivity_label": fields.get("_SensitivityLabel"),
            "retention_label": fields.get("_ComplianceTag"),
            "is_shared": item.get("shared") is not None,
            "shared_scope": item.get("shared", {}).get("scope")
        }

    def get_file_versions(self, drive_id, item_id, file_name):
        url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/versions"
        headers = get_headers()
        try:
            response = make_request_with_retry(url, headers=headers)
            versions = response.json().get("value", [])
            return [
                {
                    "version_id": v.get("id"),
                    "modified_at": v.get("lastModifiedDateTime"),
                    "modified_by": v.get("lastModifiedBy", {}).get("user", {}).get("email"),
                    "size_bytes": v.get("size")
                }
                for v in versions
            ]
        except Exception as ex:
            logger.warning(f"Could not get versions for {file_name}: {ex}")
            return []

    def analyse_file_metadata(self, records):
        total = len(records)
        if total == 0:
            return {"total_files": 0}

        extensions = Counter()
        for r in records:
            name = r.get("file_name", "")
            ext = os.path.splitext(name)[-1].lower() if "." in name else "unknown"
            extensions[ext] += 1

        sizes = [r.get("size_bytes") or 0 for r in records]
        total_size = sum(sizes)
        avg_size = total_size // total if total else 0

        sensitivity_counts = Counter(
            r.get("sensitivity_label") or "Unlabelled" for r in records
        )

        shared = [r for r in records if r.get("is_shared")]

        return {
            "total_files": total,
            "total_size_bytes": total_size,
            "average_size_bytes": avg_size,
            "file_type_breakdown": dict(extensions.most_common(10)),
            "sensitivity_label_breakdown": dict(sensitivity_counts),
            "shared_files_count": len(shared),
            "shared_files_pct": round(len(shared) / total * 100, 2) if total else 0
        }

    def _paginate(self, url, params, label):
        headers = get_headers()
        results = []
        page = 1
        while url:
            logger.info(f"[{label}] Fetching page {page}")
            response = make_request_with_retry(url, headers=headers, params=params if page == 1 else None)
            if response is None:
                break
            data = response.json()
            results.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
            page += 1
        logger.info(f"[{label}] Total records: {len(results)}")
        return results

    def run(self):
        logger.info("Starting File Metadata Extraction")
        all_records = []
        sites = self.get_all_sites()
        for site in sites:
            site_id = site.get("id")
            site_name = site.get("displayName", "Unknown")
            site_url = site.get("webUrl", "")
            drives = self.get_drives_for_site(site_id, site_name)
            for drive in drives:
                drive_id = drive.get("id")
                drive_name = drive.get("name", "Unknown")
                files = self.get_files_in_drive(drive_id, drive_name)
                for f in files:
                    record = self.normalise_file_record(f, drive_id, drive_name, site_name, site_url)
                    versions = self.get_file_versions(drive_id, record["file_id"], record["file_name"])
                    record["version_count"] = len(versions)
                    record["versions"] = versions
                    all_records.append(record)

        export_to_json(all_records, "file_metadata")
        export_to_csv(all_records, "file_metadata")
        summary = self.analyse_file_metadata(all_records)
        export_summary(summary, "file_metadata_summary")
        logger.info("File Metadata Extraction Complete")
        return {"file_records": all_records, "summary": summary}