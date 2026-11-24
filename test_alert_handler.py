
import os
import sys
import unittest
from unittest.mock import patch

os.environ["SNS_TOPIC_ARN"] = (
    "arn:aws:sns:ap-south-1:123456789012:lab-alerts"
)
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "lambda")
)

import alert_handler


class AlertHandlerTest(unittest.TestCase):

    @patch.object(alert_handler, "sns")
    def test_publishes_event(self, mock_sns):

        mock_sns.publish.return_value = {
            "MessageId": "LOCAL-TEST-001"
        }

        event = {
            "source": "aws.s3",
            "detail-type": "AWS API Call via CloudTrail",
            "time": "2026-11-24T10:00:00Z",
            "detail": {
                "eventName": "PutBucketPolicy",
                "awsRegion": "ap-south-1",
                "recipientAccountId": "123456789012",
                "userIdentity": {
                    "arn": "arn:aws:iam::123456789012:user/lab-user"
                },
                "sourceIPAddress": "203.0.113.10"
            }
        }

        result = alert_handler.lambda_handler(event, None)

        self.assertEqual(result["status"], "published")
        self.assertEqual(
            result["messageId"],
            "LOCAL-TEST-001"
        )

        mock_sns.publish.assert_called_once()


if __name__ == "__main__":
    unittest.main()
