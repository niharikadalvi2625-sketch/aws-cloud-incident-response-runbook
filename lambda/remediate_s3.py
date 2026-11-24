
import json
import os
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")


def _has_unconditional_public_allow(statement):
    if statement.get("Effect") != "Allow" or statement.get("Condition"):
        return False

    principal = statement.get("Principal")

    if principal == "*":
        return True

    if isinstance(principal, dict):
        return any(
            value == "*" or (isinstance(value, list) and "*" in value)
            for value in principal.values()
        )

    return False


def lambda_handler(event, context):
    """Contain public access for the lab bucket."""

    detail = event.get("detail", {})
    requested_bucket = detail.get("requestParameters", {}).get("bucketName")

    bucket = requested_bucket or os.environ["LAB_BUCKET_NAME"]

    if bucket != os.environ["LAB_BUCKET_NAME"]:
        return {
            "status": "skipped",
            "reason": "bucket outside lab scope"
        }

    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )

    removed = 0

    try:
        policy = json.loads(
            s3.get_bucket_policy(Bucket=bucket)["Policy"]
        )

        statements = policy.get("Statement", [])

        if not isinstance(statements, list):
            statements = [statements]

        retained = [
            item for item in statements
            if not _has_unconditional_public_allow(item)
        ]

        removed = len(statements) - len(retained)

        if removed > 0:
            if retained:
                policy["Statement"] = retained
                s3.put_bucket_policy(
                    Bucket=bucket,
                    Policy=json.dumps(policy)
                )
            else:
                s3.delete_bucket_policy(Bucket=bucket)

    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")

        if code not in (
            "NoSuchBucketPolicy",
            "NoSuchBucketPolicyException"
        ):
            raise

    return {
        "status": "contained",
        "bucket": bucket,
        "public_access_block_enabled": True,
        "public_policy_statements_removed": removed
    }
