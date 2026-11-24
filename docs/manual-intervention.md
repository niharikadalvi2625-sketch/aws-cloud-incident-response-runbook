# Manual Intervention and Automation-Failure Guide

Use this guide when a Lambda remediation did not run, timed out, lacked permissions,
returned an error, or could cause unacceptable service impact.

## A. First response to failed automation

1. Acknowledge the alert and assign an incident owner.
2. Check EventBridge rule metrics (`MatchedEvents`, `Invocations`, `FailedInvocations`)
   and Lambda metrics (`Errors`, `Throttles`, `Duration`, `Invocations`).
3. Open the Lambda CloudWatch log group and inspect the invocation request ID.
4. Confirm the EventBridge target has permission to invoke the function.
5. Check the Lambda execution role for `AccessDenied` and resource-scope mismatches.
6. Do not repeatedly replay an event until the action is understood; remediation should
   be treated as potentially non-idempotent when policies or dependencies are complex.
7. Perform the approved manual containment steps below and record all commands/results.

## B. Manually contain S3 public exposure

Set variables for the affected bucket:

```bash
BUCKET="replace-with-affected-bucket"
```

Inspect before changing:

```bash
aws s3api get-public-access-block --bucket "$BUCKET"
aws s3api get-bucket-policy-status --bucket "$BUCKET"
aws s3api get-bucket-policy --bucket "$BUCKET"
aws s3api get-bucket-acl --bucket "$BUCKET"
aws s3api get-bucket-ownership-controls --bucket "$BUCKET"
```

Enable all four Block Public Access controls:

```bash
aws s3api put-public-access-block \
  --bucket "$BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

Re-check:

```bash
aws s3api get-public-access-block --bucket "$BUCKET"
aws s3api get-bucket-policy-status --bucket "$BUCKET"
```

If an unauthorized bucket policy remains, preserve a copy first:

```bash
aws s3api get-bucket-policy --bucket "$BUCKET" \
  --query Policy --output text > "${BUCKET}-policy-evidence.json"
```

Then have the bucket owner/security lead review and remove only the unauthorized
statement(s). If the entire policy is malicious and removal is approved:

```bash
aws s3api delete-bucket-policy --bucket "$BUCKET"
```

Do not delete a policy blindly; it may contain required service or application access.
If public ACL grants are present, keep `IgnorePublicAcls` and `BlockPublicAcls` enabled,
then have the owner plan ACL cleanup and Bucket owner enforced ownership controls.

## C. Manually remediate a security group

Inspect the group and its ingress rules:

```bash
SG_ID="sg-0123456789abcdef0"
aws ec2 describe-security-groups --group-ids "$SG_ID"
```

For each unauthorized world-open rule, revoke the exact permission. Example for SSH:

```bash
aws ec2 revoke-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0
```

IPv6 example:

```bash
aws ec2 revoke-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp \
  --port 22 \
  --cidr ::/0
```

Use the exact protocol, port/range, and CIDR returned by `describe-security-groups`.
For rules created with security-group rule IDs, consider
`revoke-security-group-ingress --group-id ... --security-group-rule-ids ...`.
Do not remove public HTTP/HTTPS rules automatically without service-owner approval.

## D. If the alert Lambda or SNS notification fails

- Check Lambda environment variable `ALERT_TOPIC_ARN`, execution role `sns:Publish`,
  SNS topic policy, subscription status, and CloudWatch logs.
- Check the email recipient's SNS confirmation. Unconfirmed subscriptions do not receive
  email notifications.
- Use CloudTrail Event History or the organization's central SIEM to investigate the
  event while alerting is restored.
- Create an incident ticket manually and notify the on-call team using the approved
  secondary channel.

## E. Escalation conditions

Escalate immediately to the incident commander and cloud platform owner if:
- Sensitive or regulated data may have been exposed.
- The actor is root, a privileged role, or a compromised CI/CD identity.
- Automation repeatedly fails or the same change recurs.
- Containment could cause material service disruption.
- There is evidence of data reads, exfiltration, destructive activity, or log tampering.

## F. Change control and evidence

Record the operator, approval, UTC time, commands, command output, affected resource,
before/after configuration, ticket ID, and rollback plan. Preserve evidence in a
restricted, immutable location according to retention policy.
