import json

# HIPAA rules for any GCS bucket that contains ePHI:
#   Rule 1: publicAccessPrevention must be "enforced"
#   Rule 2: encryption.defaultKmsKeyName must be present (a CMEK key)
#
# Important scoping note: these rules only apply to buckets that actually
# contain ePHI. A public, unencrypted bucket that is labeled ephi="false"
# (e.g. static web assets) is out of scope and should NOT be reported.

# 1. Ingest the bucket metadata payload.
with open("buckets.json") as f:
    buckets = json.load(f)

print("GCS Bucket HIPAA Compliance Report")
print("=" * 40)

found_violation = False

# 2. Evaluate each bucket.
for bucket in buckets:
    name = bucket["name"]
    env = bucket["labels"]["env"]
    ephi = bucket["labels"]["ephi"]   # label values come back as strings

    # Non-ePHI buckets are out of scope -- the HIPAA rules don't apply to them.
    if ephi == "false":
        # print("Bucket:      " + name)
        # print("Environment: " + env)
        # print("  Non-ePHI bucket (out of scope) -- skipping HIPAA checks")
        # print("-" * 40)
        continue

    violations = []

    # Rule 1: Public access must be prevented.
    if bucket["publicAccessPrevention"] != "enforced":
        violations.append("publicAccessPrevention is not 'enforced'")

    # Rule 2: Bucket must use a Customer-Managed Encryption Key.
    encryption = bucket["encryption"]
    if encryption is None:
        violations.append("No CMEK key (encryption not configured)")
    elif not encryption["defaultKmsKeyName"]:
        violations.append("No CMEK key (defaultKmsKeyName is empty)")

    # 3. Report only the buckets that failed.
    if violations:
        found_violation = True
        print("Bucket:      " + name)
        print("Environment: " + env)
        for v in violations:
            print("  - " + v)
        print("-" * 40)

if not found_violation:
    print("All ePHI buckets are compliant.")