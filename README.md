# HIPAA GCS Bucket Compliance Monitor
Part I covers a small automation that evaluates Google Cloud Storage bucket metadata against HIPAA controls that apply to any bucket containing ePHI. Part II covers the architecture design for this to run in production, including the collection of evidence, alerting and continuous compliance and monitoring.

## Part I
### Running the script
The script reads `buckets.json` from the current directory and prints a report to the console. No third-party packages are required — only the Python standard library (json). To run the script and get a report:
1. Download the two filesL `buckets.json` and `monitor.py`. Make sure they are in the same directory from where you will be running the script. 
3. Using Python 3 version, type the following in your console: `python3 monitor.py`

## Part II
### Architecture Design
#### 1. Compute
Cloud Run Job triggered by Cloud Scheduler. A cron schedule (e.g. daily or hourly) in Cloud Scheduler invokes a containerized Cloud Run Job that runs `monitor.py` to completion and exits.
- In production the script replaces the mock buckets.json with live calls to the GCS API (`storage.buckets.list` / `storage.buckets.get`), reading `iamConfiguration.publicAccessPrevention` and `encryption.defaultKmsKeyName`.

#### 2. Identity / Auth
A dedicated, least-privilege service account (SA) attached to the Cloud Run Job — no exported keys.
- The SA is granted a custom role with only `storage.buckets.list` and `storage.buckets.get` (granted at the organization or folder level so it can enumerate buckets across all projects). This avoids broad predefined roles like roles/viewer.
- Cloud Run supplies the workload short-lived credentials via the metadata server; the Google client libraries consume them through **Application Default Credentials (ADC)**. This is keyless — there are no long-lived service-account JSON keys to leak or rotate.
- Any outbound secrets (Slack webhook URL, Vanta/Drata API token) are stored in Secret Manager and read at runtime; the SA gets `secretmanager.secretAccessor`.

#### 3. Integration & Alerting
The job has two consumers: humans who need to act, and the compliance platform that needs evidence.
- **Audit evidence:** the full structured JSON report is written to a dedicated evidence GCS bucket with object versioning and a retention policy, giving an immutable, timestamped trail for auditors.
- **Alerting:** non-compliant findings are published to a Pub/Sub topic. A lightweight subscriber (Cloud Function) fans them out to Slack / PagerDuty for the Security/Engineering team and creates Security Command Center custom findings so violations surface in GCP's central posture dashboard.
- **Continuous compliance tooling:** the job POSTs per-control pass/fail results to Vanta/Drata via their custom-test API, so the HIPAA bucket control appears in the compliance dashboard with current status and evidence. (Their native GCP integrations cover generic posture; the API push is for this organization-specific control.)
