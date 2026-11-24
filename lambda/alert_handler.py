import json
import os
import boto3

sns = boto3.client("sns")


def lambda_handler(event, context):
    """Publish a compact, structured CloudTrail alert to the configured SNS topic."""
    detail = event.get("detail", {})
    identity = detail.get("userIdentity", {})
    message = {
        "alertType": "SuspiciousCloudApiCall",
        "eventName": detail.get("eventName"),
        "eventSource": detail.get("eventSource"),
        "eventTime": detail.get("eventTime"),
        "awsRegion": detail.get("awsRegion"),
        "account": event.get("account"),
        "sourceIp": detail.get("sourceIPAddress"),
        "userAgent": detail.get("userAgent"),
        "principalArn": identity.get("arn"),
        "principalType": identity.get("type"),
        "requestParameters": detail.get("requestParameters", {}),
        "eventId": detail.get("eventID"),
    }
    result = sns.publish(
        TopicArn=os.environ["SNS_TOPIC_ARN"],
        Subject="AWS Security API Alert",
        Message=json.dumps(message, indent=2, default=str),
    )
    return {"status": "published", "messageId": result.get("MessageId")}
