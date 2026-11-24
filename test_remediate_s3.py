
import os
import sys
import json
import unittest
from unittest.mock import patch

os.environ["LAB_BUCKET_NAME"] = "example-lab-bucket"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "lambda")
)

import remediate_s3


class NoSuchBucketPolicy(Exception):
    pass


class S3RemediationTest(unittest.TestCase):

    @patch.object(remediate_s3, "s3")
    def test_blocks_public_access_and_removes_public_allow(
        self, mock_s3
    ):

        mock_s3.exceptions.NoSuchBucketPolicy = (
            NoSuchBucketPolicy
        )

        mock_s3.get_bucket_policy.return_value = {
            "Policy": json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": (
                            "arn:aws:s3:::example-lab-bucket/*"
                        )
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": (
                                "arn:aws:iam::123456789012:root"
                            )
                        },
                        "Action": "s3:ListBucket",
                        "Resource": (
                            "arn:aws:s3:::example-lab-bucket"
                        )
                    }
                ]
            })
        }

        result = remediate_s3.lambda_handler({}, None)

        self.assertEqual(result["status"], "contained")

        self.assertEqual(
            result["public_policy_statements_removed"],
            1
        )

        mock_s3.put_public_access_block.assert_called_once()
        mock_s3.put_bucket_policy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
