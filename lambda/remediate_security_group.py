
import os
import boto3

ec2 = boto3.client("ec2")

SENSITIVE_PORTS = {22, 3389, 3306, 5432, 1433, 27017, 6379}


def is_world_open(permission):
    """Check whether a rule exposes sensitive ports to everyone."""

    protocol = str(permission.get("IpProtocol", ""))

    if protocol == "-1":
        return bool(
            permission.get("IpRanges")
            or permission.get("Ipv6Ranges")
        )

    if protocol not in {"tcp", "udp"}:
        return False

    from_port = permission.get("FromPort")
    to_port = permission.get("ToPort")

    if from_port is None or to_port is None:
        return False

    includes_sensitive_port = any(
        from_port <= port <= to_port
        for port in SENSITIVE_PORTS
    )

    if not includes_sensitive_port:
        return False

    ipv4_open = any(
        item.get("CidrIp") == "0.0.0.0/0"
        for item in permission.get("IpRanges", [])
    )

    ipv6_open = any(
        item.get("CidrIpv6") == "::/0"
        for item in permission.get("Ipv6Ranges", [])
    )

    return ipv4_open or ipv6_open


def lambda_handler(event, context):
    """Remove dangerous public ingress rules from a security group."""

    detail = event.get("detail", {})
    request = detail.get("requestParameters", {})

    group_id = (
        request.get("groupId")
        or os.environ.get("SECURITY_GROUP_ID")
    )

    if not group_id:
        raise ValueError("Security group ID not found")

    response = ec2.describe_security_groups(
        GroupIds=[group_id]
    )

    groups = response.get("SecurityGroups", [])

    if not groups:
        raise ValueError(
            f"Security group not found: {group_id}"
        )

    revoked = []

    for permission in groups[0].get("IpPermissions", []):
        if is_world_open(permission):
            ec2.revoke_security_group_ingress(
                GroupId=group_id,
                IpPermissions=[permission]
            )
            revoked.append(permission)

    return {
        "status": "remediated",
        "security_group_id": group_id,
        "permissions_revoked": len(revoked)
    }
