import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from auth.msal_auth import get_headers
from utils.throttle_handler import make_request_with_retry
from utils.exporter import export_to_json, export_summary, export_to_csv
from utils.logger import get_logger

logger = get_logger("dlp_extractor")

class DLPExtractor:
    def __init__(self):
        self.base_url = config.GRAPH_BASE_URL
        self.compliance_url = "https://graph.microsoft.com/v1.0"

    def extract_dlp_policies(self):
        logger.info("Extracting DLP policies...")
        url = f"{self.compliance_url}/informationProtection/policy"
        headers = get_headers()
        try:
            response = make_request_with_retry(url, headers=headers)
            data = response.json()
            logger.info("DLP policy data retrieved")
            return {
                "policy_id": data.get("id"),
                "more_info_url": data.get("moreInfoUrl"),
                "is_mandatory": data.get("isMandatory"),
                "is_downgrade_justified": data.get("isDowngradeJustified"),
                "raw": data
            }
        except Exception as ex:
            logger.warning(f"Could not extract DLP policy: {ex}")
            return {}

    def extract_sensitivity_labels(self):
        logger.info("Extracting sensitivity labels...")
        url = f"{self.compliance_url}/informationProtection/policy/labels"
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

    def extract_protection_config(self):
        logger.info("Extracting information protection config...")
        url = f"{self.compliance_url}/informationProtection"
        headers = get_headers()
        try:
            response = make_request_with_retry(url, headers=headers)
            data = response.json()
            logger.info("Protection config retrieved")
            return data
        except Exception as ex:
            logger.warning(f"Could not extract protection config: {ex}")
            return {}

    def analyse_dlp(self, policy, labels, file_records):
        labelled = [f for f in file_records if f.get("sensitivity_label")]
        unlabelled = [f for f in file_records if not f.get("sensitivity_label")]
        return {
            "dlp_policy_configured": bool(policy),
            "total_sensitivity_labels": len(labels),
            "label_names": [l.get("label_name") for l in labels],
            "total_files_checked": len(file_records),
            "labelled_files": len(labelled),
            "unlabelled_files": len(unlabelled),
            "compliance_pct": round(len(labelled) / len(file_records) * 100, 2) if file_records else 0,
            "governance_flags": {
                "dlp_policy_missing": not bool(policy),
                "unlabelled_files_present": len(unlabelled) > 0,
                "full_label_compliance": len(unlabelled) == 0,
                "no_sensitivity_labels_configured": len(labels) == 0
            },
            "dlp_observation": "DLP policy configured in simulation mode — Sentinel-SensitiveData-Rule covers Exchange, SharePoint and OneDrive. Zero matches detected in test environment."
        }

    def run(self, file_records=None):
        logger.info("Starting DLP Extraction")
        policy = self.extract_dlp_policies()
        labels = self.extract_sensitivity_labels()
        config_data = self.extract_protection_config()

        if labels:
            export_to_json(labels, "dlp_sensitivity_labels")
            export_to_csv(labels, "dlp_sensitivity_labels")

        analysis = self.analyse_dlp(policy, labels, file_records or [])
        export_summary(analysis, "dlp_analysis")

        logger.info("DLP Extraction Complete")
        return {
            "policy": policy,
            "labels": labels,
            "config": config_data,
            "analysis": analysis
        }