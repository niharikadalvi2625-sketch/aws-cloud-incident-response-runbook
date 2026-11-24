# Incident Response Runbook: Suspected Public S3 Bucket Exposure

**Scenario:** An unauthorized or accidental API change may have exposed an S3 bucket
or changed its access controls.

**Severity starting point:** High when a bucket policy or ACL grants public access,
or when public access controls are disabled on a bucket containing sensitive data.
Raise to Critical if evidence indicates unauthorized reads, regulated data, credentials,
or material business impact.

## 1. Preparation

Before an incident:
- Maintain an inventory of buckets, owners, data classifications, and business criticality.
- Enable organization-wide CloudTrail management and relevant data-event logging.
- Route EventBridge alerts to a monitored SNS destination and incident-management queue.
- Keep S3 Block Public Access enabled at organization/account and bucket levels.
- Enable versioning where appropriate; use Object Lock where required by retention policy.
- Define an incident commander, cloud platform owner, data owner, privacy/legal contact,
  and communications lead.
- Test remediation in a non-production account and document approved exceptions.

## 2. Detection

**Signals**
- CloudTrail `PutBucketPolicy`, `PutBucketAcl`, `DeletePublicAccessBlock`,
  `PutPublicAccessBlock`, or `PutBucketOwnershipControls`.
- AWS Config `s3-bucket-public-read-prohibited` / `s3-bucket-public-write-prohibited`
  non-compliance (recommended additional integration).
- GuardDuty, Security Hub, or external CSPM finding indicating public exposure.
- Unexpected `GetObject`, `ListBucket`, or data transfer patterns when S3 data events
  are enabled.

**Automated actions**
1. EventBridge matches suspicious management API calls.
2. Alert Lambda sends event name, actor identity, event time, region, source IP,
   request parameters, and event ID to SNS.
3. S3 remediation rule invokes the S3 containment Lambda for selected bucket-control
   changes. The Lambda enables all four bucket-level Block Public Access controls and
   removes unconditional public-principal `Allow` statements from the bucket policy.
4. CloudWatch Logs retain the Lambda execution record.

**Operator checklist**
- Acknowledge the SNS alert and open an incident ticket.
- Record the CloudTrail event ID, AWS account, region, bucket name, principal ARN,
  source IP, user agent, and UTC timestamp.
- Confirm whether the change was authorized (change ticket, deployment pipeline,
  approved exception).
- Preserve evidence before making non-automated changes.

## 3. Analysis

1. Retrieve the full CloudTrail event using the event ID or search CloudTrail Lake.
2. Identify the principal: IAM user, assumed role, federated identity, service role,
   or root. Trace the session issuer and source identity where available.
3. Review the bucket policy, ACL, Block Public Access configuration, ownership controls,
   access-point policies, and account-level Block Public Access settings.
4. Determine the data classification and whether public access was actually possible.
   A disabled Block Public Access setting alone does not prove that data was public.
5. Review S3 data events for `GetObject`, `GetObjectVersion`, `ListBucket`, and
   `PutObject` activity during the exposure window. Data events must have been enabled
   to provide this evidence retrospectively.
6. Correlate source IP, user agent, identity activity, CloudTrail changes, GuardDuty,
   VPC Flow Logs, and application logs.
7. Establish the earliest possible exposure time, last known safe state, affected
   objects/prefixes, and potential exfiltration volume.

**Decision:** If exposure is confirmed or cannot be ruled out quickly, maintain containment
and escalate to the data owner and incident commander.

## 4. Containment

Immediate:
- Confirm the S3 remediation Lambda succeeded. Check its CloudWatch log stream and
  verify `get-public-access-block` reports all four flags as `true`.
- Verify no public `Allow` policy statements remain. Do not assume Block Public Access
  is the only control to inspect.
- If automation failed, manually enable bucket-level Block Public Access using the
  manual intervention guide.
- If the principal is compromised, disable the access key or revoke active sessions
  using the organization's identity-response procedure. Avoid deleting evidence.
- Restrict affected IAM roles/policies and stop the unauthorized deployment pipeline.
- If needed, apply a temporary explicit deny only with approval and a rollback plan;
  an overly broad deny can interrupt production.

Preserve:
- Export CloudTrail events, bucket policy, ACL, public-access-block state, object
  inventory, relevant logs, and incident timestamps to a restricted evidence location.
- Record who collected each artifact, when, and its integrity hash.

## 5. Eradication

1. Remove unauthorized public policy statements and ACL grants.
2. Remove or correct the IAM principal, role trust policy, access key, CI/CD credential,
   or deployment configuration that caused the change.
3. Rotate exposed credentials and secrets; search repositories, build logs, and
   secret stores for reuse.
4. Review bucket ownership controls and migrate away from ACLs where feasible.
5. Correct IaC templates and policy-as-code checks so the insecure configuration
   cannot be reintroduced.
6. Review adjacent buckets, access points, KMS key policies, security groups, and
   roles for the same actor or deployment pattern.
7. If object integrity is in doubt, compare object versions and checksums against
   a trusted baseline.

## 6. Recovery

1. The bucket owner validates the intended access model and required application paths.
2. Re-enable only approved access, preferably through narrowly scoped IAM roles and
   private network paths. Do not re-enable public access as a quick fix.
3. Run application and data-owner tests; confirm expected principals can access only
   required prefixes and actions.
4. Monitor CloudTrail, S3 data events, GuardDuty, and access-denied/error rates closely
   for at least the organization's defined heightened-monitoring period.
5. Confirm backups, version history, and object integrity.
6. Close the incident only after the incident commander and data owner approve recovery.

## 7. Post-incident activity

- Complete a timeline and root-cause analysis.
- Record scope, duration, affected data, confirmed/possible reads, containment time,
  and business impact.
- Notify privacy, legal, regulators, customers, or partners as required by applicable
  law and contractual obligations; do not make notification decisions from this runbook.
- Add detections for the root cause and test them.
- Update IAM boundaries, SCPs, Config rules, CI/CD checks, and training.
- Conduct a tabletop exercise and update this runbook.

## NIST lifecycle mapping

| NIST SP 800-61 Rev. 2 phase | Runbook activity |
|---|---|
| Preparation | Inventory, logging, roles, policies, exercises |
| Detection & Analysis | CloudTrail/EventBridge alerts, identity and data-access review |
| Containment | Block public access, restrict compromised identities |
| Eradication | Remove malicious policy/ACL changes and root cause |
| Recovery | Validate access, restore service, heightened monitoring |
| Post-Incident Activity | Lessons learned, reporting, control improvements |

This assignment uses the classic NIST SP 800-61 Rev. 2 phase model. Organizations should
map it to their currently adopted NIST incident-response guidance and internal policy.
