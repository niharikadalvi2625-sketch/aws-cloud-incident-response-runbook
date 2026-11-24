# Validation, Test, and Cleanup

## 1. Validate the template

```bash
aws cloudformation validate-template --template-body file://template.yaml
```

For deeper static checks, use `cfn-lint` and a policy scanner such as `cfn-guard`.
Review IAM actions and resource scopes before deployment.

## 2. Deploy

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name cloud-incident-response-lab \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides AlertEmail=""
```

If using email alerts, provide an address and confirm the SNS subscription email.

## 3. Verify stack resources

```bash
aws cloudformation describe-stacks \
  --stack-name cloud-incident-response-lab \
  --query "Stacks[0].Outputs"
```

Check CloudTrail status:

```bash
aws cloudtrail get-trail-status --name cloud-incident-response-lab-trail
```

Check the lab bucket's intentionally weak setting:

```bash
aws s3api get-public-access-block --bucket <LabBucketName>
```

The four flags should initially be false. The bucket has no public policy and no public
objects are created by this template.

## 4. Test alerting

From a test identity with permission to change the lab bucket, issue a harmless
configuration API call:

```bash
aws s3api put-public-access-block \
  --bucket <LabBucketName> \
  --public-access-block-configuration \
  BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false
```

Expected:
- CloudTrail records `PutPublicAccessBlock`.
- EventBridge matches the API event.
- SNS receives an alert.
- The S3 remediation Lambda turns all four controls back on.

Because event delivery is asynchronous, allow a few minutes and inspect EventBridge
and Lambda metrics/logs. Do not treat a missing email alone as proof of failed detection;
check SNS subscription confirmation and topic metrics.

## 5. Test security-group remediation

The template does not create an internet-exposed security group. In a dedicated lab VPC,
create or identify a disposable test security group, then add a world-open SSH ingress
rule using a test administrator identity. The security-group rule invokes the remediation
Lambda, which revokes world-open ingress on configured sensitive ports.

Do not test against a production security group. Confirm the final rule set with
`describe-security-groups`.

## 6. Cleanup

Empty the CloudTrail log bucket before deleting the stack. First obtain its name from
the stack resources/outputs, then:

```bash
aws s3 rm s3://<CloudTrailLogBucketName> --recursive
aws cloudformation delete-stack --stack-name cloud-incident-response-lab
aws cloudformation wait stack-delete-complete --stack-name cloud-incident-response-lab
```

The lab bucket must also be empty before stack deletion. If test objects were added,
remove them first. Verify no residual CloudTrail trails, EventBridge rules, SNS topics,
or IAM roles remain.

## 7. Known limitations

- S3 data events are not enabled by default in this template; enable them for buckets
  that require object-level access investigations. Data-event volume can incur charges.
- The S3 remediation handles bucket policies and bucket-level public-access controls,
  not access-point policies, object ACL inventory, replication destinations, or every
  form of conditional public access.
- The security-group playbook targets sensitive ports and any-protocol world-open rules.
  Adjust the port list to match organizational policy.
- Add dead-letter queues, reserved concurrency, cross-account role assumptions,
  idempotency controls, centralized audit storage, and approval gates for production.
