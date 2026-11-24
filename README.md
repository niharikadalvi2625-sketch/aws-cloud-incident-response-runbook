# AWS Cloud Security Incident Response Runbook with Automated Alerting

A lab-ready CloudFormation project demonstrating CloudTrail + EventBridge detection,
SNS alerting, and two Lambda remediation playbooks.

## What it deploys

- A dedicated S3 lab bucket with encryption and versioning enabled, but bucket-level
  S3 Block Public Access disabled to represent a *misconfigured control*. No public
  bucket policy or public object ACL is created, so the template does not intentionally
  expose data.
- A CloudTrail multi-region trail and a dedicated, encrypted-at-rest-by-S3 service log
  bucket with public access blocked.
- EventBridge rules for suspicious S3 and EC2 security-group API calls.
- An alert Lambda that publishes structured event details to SNS.
- An S3 remediation Lambda that enables all four S3 Block Public Access controls and
  removes unconditional public `Allow` statements from the bucket policy.
- A security-group remediation Lambda that revokes IPv4/IPv6 world-open ingress rules
  for a defined set of sensitive ports (and any-protocol rules).

## Files

- `template.yaml` — CloudFormation stack.
- `lambda/alert_handler.py` — SNS alert publisher.
- `lambda/remediate_s3.py` — S3 exposure containment.
- `lambda/remediate_security_group.py` — risky ingress containment.
- `docs/incident-runbook.md` — operational response procedure.
- `docs/manual-intervention.md` — failure and human escalation procedure.
- `docs/validation-and-cleanup.md` — deployment, test, and cleanup steps.

## Deploy

Prerequisites:
- An AWS test account and a role/user permitted to create CloudFormation, CloudTrail,
  EventBridge, Lambda, SNS, IAM, and S3 resources.
- AWS CLI v2 configured for the intended account and region.
- Python 3.12 runtime availability in the target region.

Validate and deploy:

```bash
aws sts get-caller-identity
aws cloudformation validate-template --template-body file://template.yaml

aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name cloud-incident-response-lab \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides AlertEmail=security-team@example.com
```

The SNS email subscription requires the recipient to confirm the subscription.
Leave `AlertEmail` empty to deploy without an email subscription.

Get outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name cloud-incident-response-lab \
  --query "Stacks[0].Outputs"
```

## Safety and operating notes

1. Deploy only in a dedicated non-production lab account.
2. The lab bucket has public-access blocking disabled to model a weak configuration,
   but the template does not make the bucket publicly readable.
3. The security-group remediation logic is intentionally conservative and only
   removes world-open ingress for selected sensitive ports or any-protocol rules.
   Review the allowlist before using it in production.
4. The S3 remediation removes public-principal `Allow` statements without conditions.
   Complex policies, cross-account access, access points, organization-level controls,
   and object-level ACLs still require human review.
5. EventBridge delivery is best-effort and asynchronous. CloudTrail delivery,
   Lambda retries, throttling, and SNS subscription confirmation affect end-to-end time.
6. This is a teaching baseline, not a complete enterprise control plane. Add centralized
   logging, delegated administration, AWS Config/Security Hub, incident ticketing,
   KMS customer-managed keys, permissions boundaries, and tested cross-account
   response roles before production use.

## Architecture

CloudTrail management events -> EventBridge rules -> alert/remediation Lambda functions.
The alert Lambda publishes to SNS. Remediation Lambdas write structured logs to
CloudWatch Logs. Security engineers validate the change and continue the NIST-aligned
incident lifecycle in the runbook.
