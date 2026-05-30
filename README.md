# Project-Sentinel
# Project Sentinel
### Microsoft 365 Data Extraction and Governance Intelligence Framework

Capstone Industry Project | La Trobe University | Team Shadow Stacks
Industry Partner: SECMON1 (Christopher McNaughton, Managing Director)

---

## Overview

Project Sentinel is a structured, secure, and repeatable framework for extracting, normalising, and analysing Microsoft 365 governance and audit data across SharePoint, OneDrive, Microsoft Teams, and Microsoft Purview.

The framework addresses a core challenge faced by organisations using Microsoft 365: governance and security data exists across multiple fragmented services with no consolidated methodology to extract and analyse it in a defensible, repeatable way.

Project Sentinel provides:
- A documented extraction framework covering all major M365 governance data domains
- Automated reference tooling using Microsoft Graph API and certificate-based authentication
- A structured analytical layer that identifies governance risks, exposure patterns, and behavioural signals
- Structured JSON and CSV output suitable for downstream ingestion into security workflows and the ShadowSight SaaS platform

---

## Team Shadow Stacks

| Name | Role | Student ID |
|---|---|---|
| Raj Kumar Mustyala | Project Manager | 22234543 |
| Vanka Manjunath | API Developer | 22197477 |
| Yaswanth Kanderi | Backend Developer | 22519671 |
| Jaswanthi Palleti | Security Analyst | 22115229 |
| Raghav Murru | Dashboard Developer | 22003177 |
| Lahari Borra | Documentation Specialist | 22134698 |

---

## Tech Stack

| Category | Technology |
|---|---|
| Authentication | Microsoft MSAL, Certificate-based auth, Azure App Registration |
| Extraction | Microsoft Graph API v1.0, SharePoint REST API, Purview Compliance API |
| Language | Python 3.x |
| Output Format | JSON, CSV, Excel |
| Dashboard | Power BI |
| Governance Platform | Microsoft Purview |
| Identity | Microsoft Entra ID |
| Environment | Microsoft 365 Business Premium (Sentinals tenant) |

---

## Repository Structure

```
Project-Sentinel/
├── main.py
├── config_template.py
├── host.json
├── requirements.txt
├── README.md
├── .gitignore
├── auth/
│   ├── __init__.py
│   └── msal_auth.py
├── extractors/
│   ├── __init__.py
│   ├── audit_logs.py
│   ├── dlp_extractor.py
│   ├── file_metadata.py
│   ├── purview_labels.py
│   └── sharing_permissions.py
└── utils/
    ├── __init__.py
    ├── excel_exporter.py
    ├── exporter.py
    ├── logger.py
    ├── throttle_handler.py
    └── timeline.py
```

---

## Prerequisites

- Python 3.8 or higher
- Microsoft 365 tenant with Global Admin access
- Azure App Registration with required API permissions
- Microsoft Graph API access

## Required Python Libraries

```
pip install msal requests openpyxl azure-functions
```

---

## Configuration

Copy config_template.py to config.py and fill in your tenant details:

```
TENANT_ID = "YOUR_TENANT_ID"
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
SHAREPOINT_HOST = "YOUR_SHAREPOINT_HOST"
```

Never commit config.py to GitHub. It is listed in .gitignore.

---

## How to Run

Step 1 - Install dependencies:
```
pip install -r requirements.txt
```

Step 2 - Configure credentials in config.py

Step 3 - Run full extraction:
```
python main.py
```

This will run all extractors in sequence:
- Audit log extraction
- File metadata extraction
- Sharing permissions extraction
- Purview label extraction
- DLP extraction
- Excel export
- Governance timeline export
- OneDrive sync

---

## What Gets Extracted

| Module | Data Extracted |
|---|---|
| audit_logs.py | Sign-in logs, directory audits, SharePoint file activity |
| file_metadata.py | File name, size, creator, modifier, versions, sensitivity label |
| sharing_permissions.py | Permission scope, roles, anonymous links, external users |
| purview_labels.py | Sensitivity label names, policies, compliance percentage |
| dlp_extractor.py | DLP policy config, sensitivity labels, compliance analysis |
| excel_exporter.py | Consolidated Excel workbook with all extraction results |
| timeline.py | Chronological governance event timeline |

---

## Output Files

All outputs are saved to the output/ folder:

| File | Description |
|---|---|
| audit_logs_signin_DATE.json | Sign-in audit records |
| audit_logs_directory_DATE.json | Directory audit records |
| file_metadata_DATE.json | File metadata records |
| sharing_permissions_DATE.json | Permission records |
| purview_labels_DATE.json | Sensitivity label records |
| dlp_analysis_DATE.json | DLP analysis results |
| governance_timeline_DATE.json | Consolidated event timeline |
| extraction_history.xlsx | Full Excel workbook with all sheets |

---

## Sprint 4 Extraction Results

Live extraction from sentinals.sharepoint.com:

| Metric | Value |
|---|---|
| Total files extracted | 18 |
| Total audit events | 183 |
| Successful logins | 165 |
| Failed logins | 18 |
| Risky sign-ins | 0 |
| Total permissions | 72 |
| External sharing links | 0 |
| Anonymous links | 0 |
| Sensitivity labels applied | 0 (resolved in Sprint 5) |

---

## Governance Risk Findings

| Risk | Severity | Status |
|---|---|---|
| 0 sensitivity labels on 18 files | High | Resolved in Sprint 5 |
| No DLP policy active | High | Resolved in Sprint 5 |
| No retention policy | Medium | Resolved in Sprint 5 |
| 18 failed login attempts | Medium | Monitoring |
| 100% files shared internally | Medium | Under review |

---

## Security Notes

- All extraction uses non-interactive certificate-based authentication
- No credentials are stored in code
- Extraction runs in read-only mode
- All activity is logged for audit traceability
- Only officially supported Microsoft APIs are used
- No production data accessed

---

## Limitations

| Limitation | Details |
|---|---|
| Advanced Audit retention | Requires Microsoft 365 E5 |
| Groups and Sites labeling | Requires E3/E5 licensing |
| eDiscovery Advanced | Requires E5 licensing |
| Audit log retention | 90 days on Business Premium |

---

## Intellectual Property

All methodologies, frameworks, documentation, architectural designs, extraction workflows, schema definitions, and supporting materials are assigned to SECMON1 upon project completion, in accordance with La Trobe University industry project agreements.

Team members are permitted to reference this project in portfolios and resumes for academic and professional purposes.

---

## Acknowledgements

- Industry Partner: Christopher McNaughton, Managing Director, SECMON1
- University: La Trobe University, Melbourne
- Subject: Capstone Industry Project, Master of Cyber Security

---

Project Sentinel | Team Shadow Stacks | La Trobe University | 2026
