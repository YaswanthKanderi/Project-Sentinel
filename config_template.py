import os

TENANT_ID       = os.environ.get("TENANT_ID",       "YOUR_TENANT_ID")
CLIENT_ID       = os.environ.get("CLIENT_ID",       "YOUR_CLIENT_ID")
CLIENT_SECRET   = os.environ.get("CLIENT_SECRET",   "YOUR_CLIENT_SECRET")
SHAREPOINT_HOST = os.environ.get("SHAREPOINT_HOST", "YOUR_SHAREPOINT_HOST")

GRAPH_BASE_URL   = "https://graph.microsoft.com/v1.0"
PAGE_SIZE        = 100
MAX_RETRIES      = 5
RETRY_BACKOFF    = 60
OUTPUT_DIR       = "output"
LOG_DIR          = "logs"
AUDIT_START_DATE = "2025-01-01T00:00:00Z"
AUDIT_END_DATE   = "2026-12-31T23:59:59Z"