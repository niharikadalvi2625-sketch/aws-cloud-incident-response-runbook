
import os
import sys
import unittest
from unittest.mock import patch

os.environ["SECURITY_GROUP_ID"] = "sg-0123456789abcdef0"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "lambda")
)

import remediate_security_group


class SecurityGroupTest(unittest.TestCase):

    @patch.object(remediate_security_group, "ec2")
    def test_revokes_world_open_ssh_and_keeps_https(
        self, mock_ec2
    ):

        mock_ec2.describe_security_groups.return_value = {
            "SecurityGroups": [
                {
                    "IpPermissions": [
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 22,
                            "ToPort": 22,
                            "IpRanges": [
                                {"CidrIp": "0.0.0.0/0"}
                            ]
                        },
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 443,
                            "ToPort": 443,
                            "IpRanges": [
                                {"CidrIp": "0.0.0.0/0"}
                            ]
                        }
                    ]
                }
            ]
        }

        result = remediate_security_group.lambda_handler(
            {
                "detail": {
                    "requestParameters": {
                        "groupId": "sg-0123456789abcdef0"
                    }
                }
            },
            None
        )

        self.assertEqual(result["status"], "remediated")
        self.assertEqual(result["permissions_revoked"], 1)

        mock_ec2.revoke_security_group_ingress.assert_called_once()


if __name__ == "__main__":
    unittest.main()
