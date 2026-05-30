import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from auth.msal_auth import get_headers
from utils.throttle_handler import make_request_with_retry
from utils.exporter import export_to_json, export_summary, export_to_csv
from utils.logger import get_logger

logger = get_logger("purview_labels")

class PurviewLabelExtractor:
    def __init__(self):
        self.base_url = config.GRAPH_BASE_URL
        self.page_size = config.PAGE_SIZE

    def extract_sensitivity_labels(self):
        logger.info("Extracting sensitivity labels from Purview...")
        url = f"{self.base_url}/informationProtection/policy/labels"
        headers = get_headers()
        try:
            response = make_request_with_retry(url, headers=headers)
            data = response.json()
            labels = data.get("value", [])
            logger.info(f"Sensitivity labels found: {len(labels)}")
            return [
                {
                    "label_id": l.get("id"),
                    "label_name": l.get("name"),
                    "description": l.get("description"),
                    "color": l.get("color"),
                    "sensitivity_order": l.get("sensitivityOrder"),
                    "is_active": l.get("isActive"),
                    "tooltip": l.get("tooltip")
                }
                for l in labels
            ]
        except Exception as ex:
            logger.warning(f"Could not extract sensitivity labels: {ex}")
            return []

    def extract_label_policies(self):
        logger.info("Extracting label policies from Purview...")
        url = f"{self.base_url}/informationProtection/policy"
        headers = get_headers()
        try:
            response = make_request_with_retry(url, headers=headers)
            data = response.json()
            return {
                "policy_id": data.get("id"),
                "more_info_url": data.get("moreInfoUrl"),
                "is_mandatory": data.get("isMandatory"),
                "is_downgrade_justified": data.get("isDowngradeJustified")
            }
        except Exception as ex:
            logger.warning(f"Could not extract label policies: {ex}")
            return {}

    def analyse_labels(self, labels, file_records):
        if not labels:
            return {"total_labels_configured": 0}

        labelled_files = [f for f in file_records if f.get("sensitivity_label")]
        unlabelled_files = [f for f in file_records if not f.get("sensitivity_label")]

        return {
            "total_labels_configured": len(labels),
            "label_names": [l.get("label_name") for l in labels],
            "total_files_checked": len(file_records),
            "labelled_files": len(labelled_files),
            "unlabelled_files": len(unlabelled_files),
            "compliance_pct": round(len(labelled_files) / len(file_records) * 100, 2) if file_records else 0,
            "governance_flags": {
                "unlabelled_files_present": len(unlabelled_files) > 0,
                "full_compliance": len(unlabelled_files) == 0
            }
        }

    def run(self, file_records=None):
        logger.info("Starting Purview Label Extraction")
        labels = self.extract_sensitivity_labels()
        policy = self.extract_label_policies()

        if labels:
            export_to_json(labels, "purview_labels")
            export_to_csv(labels, "purview_labels")

        analysis = self.analyse_labels(labels, file_records or [])
        export_summary(analysis, "purview_labels")

        logger.info("Purview Label Extraction Complete")
        return {
            "labels": labels,
            "policy": policy,
            "analysis": analysis
        }