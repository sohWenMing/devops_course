#!/usr/bin/env python3
"""
aws-cleanup.py -- FlowForge AWS Resource Cleanup Script

Terminates and deletes all AWS resources created for the FlowForge DevOps course.
Handles dependencies and deletion ordering automatically.

Usage:
    python aws-cleanup.py                    # Interactive cleanup
    python aws-cleanup.py --dry-run          # Show what would be deleted
    python aws-cleanup.py --force            # Skip confirmation prompts
    python aws-cleanup.py --region us-east-1 # Specify region

Resources cleaned up:
    - EC2 instances (tagged Project: FlowForge)
    - RDS instances
    - NAT Gateways and Elastic IPs
    - VPC and all sub-resources (subnets, route tables, IGW, security groups, NACLs)
    - S3 buckets (named flowforge-*)
    - ECR repositories (named flowforge/*)
    - IAM users, roles, policies, instance profiles (named flowforge-*)

Safety features:
    - Dry-run mode shows what would be deleted
    - Confirmation prompt before destructive actions
    - Handles already-deleted resources gracefully
    - Retry logic for resources that take time to delete
    - Summary report of all actions taken
"""

import argparse
import sys
import time

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
except ImportError:
    print("ERROR: boto3 is not installed.")
    print("Install it with: pip install boto3")
    print("See: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_TAG = "FlowForge"
TAG_FILTER = [{"Name": "tag:Project", "Values": [PROJECT_TAG]}]
FLOWFORGE_PREFIX = "flowforge"

# ANSI colour helpers (disabled when stdout is not a terminal)
_COLOURS = sys.stdout.isatty()


def _red(text: str) -> str:
    return f"\033[91m{text}\033[0m" if _COLOURS else text


def _yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m" if _COLOURS else text


def _green(text: str) -> str:
    return f"\033[92m{text}\033[0m" if _COLOURS else text


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m" if _COLOURS else text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class CleanupStats:
    """Track what was deleted, skipped, and failed."""

    def __init__(self):
        self.deleted: list[str] = []
        self.skipped: list[str] = []
        self.failed: list[str] = []

    def record_deleted(self, resource: str):
        self.deleted.append(resource)
        print(_red(f"  DELETED: {resource}"))

    def record_skipped(self, resource: str, reason: str = "already gone"):
        self.skipped.append(f"{resource} ({reason})")
        print(_yellow(f"  SKIPPED: {resource} -- {reason}"))

    def record_failed(self, resource: str, error: str):
        self.failed.append(f"{resource}: {error}")
        print(_red(f"  FAILED:  {resource} -- {error}"))

    def print_summary(self):
        print("\n" + "=" * 60)
        print(_bold("CLEANUP SUMMARY"))
        print("=" * 60)
        print(_green(f"  Deleted: {len(self.deleted)} resources"))
        print(_yellow(f"  Skipped: {len(self.skipped)} resources"))
        if self.failed:
            print(_red(f"  Failed:  {len(self.failed)} resources"))
            for f in self.failed:
                print(_red(f"    - {f}"))
        else:
            print(_green("  Failed:  0 resources"))
        print("=" * 60)


def wait_for(describe_fn, check_fn, resource_name: str, timeout: int = 600,
             interval: int = 10):
    """Poll *describe_fn* until *check_fn* returns True or timeout."""
    elapsed = 0
    while elapsed < timeout:
        try:
            result = describe_fn()
            if check_fn(result):
                return True
        except ClientError:
            return True  # resource is gone
        time.sleep(interval)
        elapsed += interval
        print(f"    Waiting for {resource_name}... ({elapsed}s)")
    print(_yellow(f"    Timeout waiting for {resource_name} after {timeout}s"))
    return False


def confirm_deletion(resource_count: int, force: bool) -> bool:
    """Ask the user to confirm deletion unless --force is set."""
    if force:
        return True
    print(f"\n{_bold('WARNING')}: You are about to delete {_red(str(resource_count))} resources.")
    answer = input("Type 'yes' to proceed: ").strip().lower()
    return answer == "yes"


# ---------------------------------------------------------------------------
# Resource discovery (dry-run listing)
# ---------------------------------------------------------------------------

def discover_resources(ec2, rds_client, s3_client, ecr_client, iam_client,
                       region: str) -> dict:
    """Return a dict of resource-type -> list[resource-description]."""
    resources: dict[str, list[str]] = {}

    # EC2 instances
    instances = ec2.describe_instances(Filters=TAG_FILTER).get("Reservations", [])
    instance_ids = []
    for r in instances:
        for i in r["Instances"]:
            if i["State"]["Name"] not in ("terminated", "shutting-down"):
                name = _get_tag(i.get("Tags", []), "Name") or i["InstanceId"]
                instance_ids.append(f'{i["InstanceId"]} ({name})')
    if instance_ids:
        resources["EC2 Instances"] = instance_ids

    # Key pairs
    kps = ec2.describe_key_pairs(
        Filters=[{"Name": "key-name", "Values": [f"{FLOWFORGE_PREFIX}*"]}]
    ).get("KeyPairs", [])
    if kps:
        resources["Key Pairs"] = [kp["KeyName"] for kp in kps]

    # RDS instances
    try:
        dbs = rds_client.describe_db_instances().get("DBInstances", [])
        rds_items = [
            f'{db["DBInstanceIdentifier"]} ({db["DBInstanceStatus"]})'
            for db in dbs
            if db["DBInstanceIdentifier"].startswith(FLOWFORGE_PREFIX)
        ]
        if rds_items:
            resources["RDS Instances"] = rds_items
    except ClientError:
        pass

    # RDS subnet groups
    try:
        sgs = rds_client.describe_db_subnet_groups().get("DBSubnetGroups", [])
        rds_sg = [
            sg["DBSubnetGroupName"]
            for sg in sgs
            if sg["DBSubnetGroupName"].startswith(FLOWFORGE_PREFIX)
        ]
        if rds_sg:
            resources["RDS Subnet Groups"] = rds_sg
    except ClientError:
        pass

    # NAT Gateways
    nats = ec2.describe_nat_gateways(
        Filter=TAG_FILTER
    ).get("NatGateways", [])
    nat_items = [
        f'{n["NatGatewayId"]} ({n["State"]})'
        for n in nats if n["State"] not in ("deleted",)
    ]
    if nat_items:
        resources["NAT Gateways"] = nat_items

    # Elastic IPs
    eips = ec2.describe_addresses(
        Filters=TAG_FILTER
    ).get("Addresses", [])
    if eips:
        resources["Elastic IPs"] = [
            f'{a.get("AllocationId")} ({a.get("PublicIp")})'
            for a in eips
        ]

    # VPCs
    vpcs = ec2.describe_vpcs(Filters=TAG_FILTER).get("Vpcs", [])
    if vpcs:
        resources["VPCs"] = [
            f'{v["VpcId"]} ({_get_tag(v.get("Tags", []), "Name") or "unnamed"})'
            for v in vpcs
        ]

    # Subnets
    subnets = ec2.describe_subnets(Filters=TAG_FILTER).get("Subnets", [])
    if subnets:
        resources["Subnets"] = [
            f'{s["SubnetId"]} ({_get_tag(s.get("Tags", []), "Name") or s["CidrBlock"]})'
            for s in subnets
        ]

    # Internet Gateways
    igws = ec2.describe_internet_gateways(Filters=TAG_FILTER).get(
        "InternetGateways", [])
    if igws:
        resources["Internet Gateways"] = [
            f'{ig["InternetGatewayId"]}' for ig in igws
        ]

    # Security Groups (non-default)
    sgs_ec2 = ec2.describe_security_groups(Filters=TAG_FILTER).get(
        "SecurityGroups", [])
    sg_items = [
        f'{sg["GroupId"]} ({sg["GroupName"]})'
        for sg in sgs_ec2 if sg["GroupName"] != "default"
    ]
    if sg_items:
        resources["Security Groups"] = sg_items

    # S3 buckets
    try:
        buckets = s3_client.list_buckets().get("Buckets", [])
        s3_items = [
            b["Name"] for b in buckets
            if b["Name"].startswith(FLOWFORGE_PREFIX)
        ]
        if s3_items:
            resources["S3 Buckets"] = s3_items
    except ClientError:
        pass

    # ECR repositories
    try:
        repos = ecr_client.describe_repositories().get("repositories", [])
        ecr_items = [
            r["repositoryName"] for r in repos
            if r["repositoryName"].startswith(FLOWFORGE_PREFIX)
               or r["repositoryName"].startswith(f"{FLOWFORGE_PREFIX}/")
        ]
        if ecr_items:
            resources["ECR Repositories"] = ecr_items
    except ClientError:
        pass

    # IAM resources (users, roles, policies, instance profiles)
    _discover_iam(iam_client, resources)

    return resources


def _discover_iam(iam_client, resources: dict):
    """Find IAM resources created for FlowForge."""
    # Users
    try:
        users = iam_client.list_users().get("Users", [])
        iam_users = [
            u["UserName"] for u in users
            if u["UserName"].startswith(FLOWFORGE_PREFIX)
        ]
        if iam_users:
            resources["IAM Users"] = iam_users
    except ClientError:
        pass

    # Roles
    try:
        roles = iam_client.list_roles().get("Roles", [])
        iam_roles = [
            r["RoleName"] for r in roles
            if r["RoleName"].startswith(FLOWFORGE_PREFIX)
        ]
        if iam_roles:
            resources["IAM Roles"] = iam_roles
    except ClientError:
        pass

    # Policies (customer-managed only)
    try:
        policies = iam_client.list_policies(Scope="Local").get("Policies", [])
        iam_policies = [
            f'{p["PolicyName"]} ({p["Arn"]})'
            for p in policies
            if p["PolicyName"].startswith("FlowForge")
               or p["PolicyName"].startswith(FLOWFORGE_PREFIX)
        ]
        if iam_policies:
            resources["IAM Policies"] = iam_policies
    except ClientError:
        pass

    # Instance Profiles
    try:
        profiles = iam_client.list_instance_profiles().get(
            "InstanceProfiles", [])
        iam_ips = [
            ip["InstanceProfileName"] for ip in profiles
            if ip["InstanceProfileName"].startswith(FLOWFORGE_PREFIX)
        ]
        if iam_ips:
            resources["IAM Instance Profiles"] = iam_ips
    except ClientError:
        pass

    # Groups
    try:
        groups = iam_client.list_groups().get("Groups", [])
        iam_groups = [
            g["GroupName"] for g in groups
            if g["GroupName"].startswith(FLOWFORGE_PREFIX)
               or g["GroupName"] in ("deployers", "administrators")
        ]
        if iam_groups:
            resources["IAM Groups"] = iam_groups
    except ClientError:
        pass


def _get_tag(tags: list, key: str) -> str | None:
    for tag in tags:
        if tag["Key"] == key:
            return tag["Value"]
    return None


# ---------------------------------------------------------------------------
# Deletion functions
# ---------------------------------------------------------------------------

def cleanup_ec2_instances(ec2, stats: CleanupStats):
    """Terminate EC2 instances tagged with Project: FlowForge."""
    print("\n" + _bold("--- EC2 Instances ---"))
    reservations = ec2.describe_instances(Filters=TAG_FILTER).get(
        "Reservations", [])
    instance_ids = []
    for r in reservations:
        for i in r["Instances"]:
            if i["State"]["Name"] not in ("terminated", "shutting-down"):
                instance_ids.append(i["InstanceId"])

    if not instance_ids:
        print("  No FlowForge EC2 instances found.")
        return

    try:
        ec2.terminate_instances(InstanceIds=instance_ids)
        for iid in instance_ids:
            stats.record_deleted(f"EC2 instance {iid}")

        # Wait for termination
        print("  Waiting for instances to terminate...")
        waiter = ec2.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=instance_ids,
                    WaiterConfig={"Delay": 10, "MaxAttempts": 60})
        print(_green("  All instances terminated."))
    except ClientError as e:
        for iid in instance_ids:
            stats.record_failed(f"EC2 instance {iid}", str(e))


def cleanup_key_pairs(ec2, stats: CleanupStats):
    """Delete key pairs named flowforge-*."""
    print("\n" + _bold("--- Key Pairs ---"))
    kps = ec2.describe_key_pairs(
        Filters=[{"Name": "key-name", "Values": [f"{FLOWFORGE_PREFIX}*"]}]
    ).get("KeyPairs", [])
    if not kps:
        print("  No FlowForge key pairs found.")
        return
    for kp in kps:
        try:
            ec2.delete_key_pair(KeyName=kp["KeyName"])
            stats.record_deleted(f"Key pair {kp['KeyName']}")
        except ClientError as e:
            stats.record_failed(f"Key pair {kp['KeyName']}", str(e))


def cleanup_rds(rds_client, stats: CleanupStats):
    """Delete RDS instances and subnet groups."""
    print("\n" + _bold("--- RDS Instances ---"))
    try:
        dbs = rds_client.describe_db_instances().get("DBInstances", [])
    except ClientError:
        print("  Could not list RDS instances.")
        return

    ff_dbs = [db for db in dbs
              if db["DBInstanceIdentifier"].startswith(FLOWFORGE_PREFIX)]

    if not ff_dbs:
        print("  No FlowForge RDS instances found.")
    else:
        for db in ff_dbs:
            db_id = db["DBInstanceIdentifier"]
            if db["DBInstanceStatus"] == "deleting":
                stats.record_skipped(f"RDS {db_id}", "already deleting")
                continue
            try:
                rds_client.delete_db_instance(
                    DBInstanceIdentifier=db_id,
                    SkipFinalSnapshot=True,
                    DeleteAutomatedBackups=True,
                )
                stats.record_deleted(f"RDS instance {db_id}")
            except ClientError as e:
                stats.record_failed(f"RDS instance {db_id}", str(e))

        # Wait for RDS deletions
        print("  Waiting for RDS deletions (this may take several minutes)...")
        for db in ff_dbs:
            db_id = db["DBInstanceIdentifier"]
            wait_for(
                lambda _id=db_id: rds_client.describe_db_instances(
                    DBInstanceIdentifier=_id),
                lambda _: False,
                f"RDS {db_id}",
                timeout=900,
                interval=30,
            )

    # Subnet groups
    print("\n" + _bold("--- RDS Subnet Groups ---"))
    try:
        sgs = rds_client.describe_db_subnet_groups().get("DBSubnetGroups", [])
        ff_sgs = [sg for sg in sgs
                  if sg["DBSubnetGroupName"].startswith(FLOWFORGE_PREFIX)]
        if not ff_sgs:
            print("  No FlowForge DB subnet groups found.")
        for sg in ff_sgs:
            try:
                rds_client.delete_db_subnet_group(
                    DBSubnetGroupName=sg["DBSubnetGroupName"])
                stats.record_deleted(f"DB subnet group {sg['DBSubnetGroupName']}")
            except ClientError as e:
                stats.record_failed(
                    f"DB subnet group {sg['DBSubnetGroupName']}", str(e))
    except ClientError:
        pass


def cleanup_nat_gateways(ec2, stats: CleanupStats):
    """Delete NAT Gateways."""
    print("\n" + _bold("--- NAT Gateways ---"))
    nats = ec2.describe_nat_gateways(Filter=TAG_FILTER).get("NatGateways", [])
    active_nats = [n for n in nats if n["State"] not in ("deleted", "deleting")]

    if not active_nats:
        print("  No FlowForge NAT Gateways found.")
        return

    for nat in active_nats:
        nat_id = nat["NatGatewayId"]
        try:
            ec2.delete_nat_gateway(NatGatewayId=nat_id)
            stats.record_deleted(f"NAT Gateway {nat_id}")
        except ClientError as e:
            stats.record_failed(f"NAT Gateway {nat_id}", str(e))

    # Wait for NAT gateways to delete
    print("  Waiting for NAT Gateways to delete...")
    for nat in active_nats:
        nat_id = nat["NatGatewayId"]
        wait_for(
            lambda _id=nat_id: ec2.describe_nat_gateways(
                NatGatewayIds=[_id]),
            lambda resp: all(
                n["State"] == "deleted"
                for n in resp.get("NatGateways", [])
            ),
            f"NAT Gateway {nat_id}",
            timeout=300,
            interval=15,
        )


def cleanup_elastic_ips(ec2, stats: CleanupStats):
    """Release Elastic IPs."""
    print("\n" + _bold("--- Elastic IPs ---"))
    eips = ec2.describe_addresses(Filters=TAG_FILTER).get("Addresses", [])
    if not eips:
        print("  No FlowForge Elastic IPs found.")
        return
    for eip in eips:
        alloc_id = eip.get("AllocationId")
        try:
            if eip.get("AssociationId"):
                ec2.disassociate_address(AssociationId=eip["AssociationId"])
            ec2.release_address(AllocationId=alloc_id)
            stats.record_deleted(f"Elastic IP {eip.get('PublicIp')} ({alloc_id})")
        except ClientError as e:
            stats.record_failed(f"Elastic IP {alloc_id}", str(e))


def cleanup_vpc_resources(ec2, stats: CleanupStats):
    """Delete VPC and all sub-resources in dependency order."""
    vpcs = ec2.describe_vpcs(Filters=TAG_FILTER).get("Vpcs", [])
    if not vpcs:
        print("\n" + _bold("--- VPC ---"))
        print("  No FlowForge VPCs found.")
        return

    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        vpc_name = _get_tag(vpc.get("Tags", []), "Name") or vpc_id
        print(f"\n" + _bold(f"--- VPC: {vpc_name} ({vpc_id}) ---"))

        # 1. Delete security group rules (remove cross-references)
        _cleanup_sg_rules(ec2, vpc_id, stats)

        # 2. Delete non-default security groups
        _cleanup_security_groups(ec2, vpc_id, stats)

        # 3. Delete custom NACLs
        _cleanup_nacls(ec2, vpc_id, stats)

        # 4. Delete route table associations & custom route tables
        _cleanup_route_tables(ec2, vpc_id, stats)

        # 5. Delete subnets
        _cleanup_subnets(ec2, vpc_id, stats)

        # 6. Detach and delete Internet Gateways
        _cleanup_igws(ec2, vpc_id, stats)

        # 7. Delete the VPC
        try:
            ec2.delete_vpc(VpcId=vpc_id)
            stats.record_deleted(f"VPC {vpc_name} ({vpc_id})")
        except ClientError as e:
            stats.record_failed(f"VPC {vpc_id}", str(e))


def _cleanup_sg_rules(ec2, vpc_id: str, stats: CleanupStats):
    """Remove all ingress/egress rules from non-default SGs to break cross-references."""
    sgs = ec2.describe_security_groups(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    ).get("SecurityGroups", [])

    for sg in sgs:
        if sg["GroupName"] == "default":
            continue
        sg_id = sg["GroupId"]
        # Remove ingress rules
        if sg.get("IpPermissions"):
            try:
                ec2.revoke_security_group_ingress(
                    GroupId=sg_id, IpPermissions=sg["IpPermissions"])
            except ClientError:
                pass
        # Remove egress rules
        if sg.get("IpPermissionsEgress"):
            try:
                ec2.revoke_security_group_egress(
                    GroupId=sg_id, IpPermissions=sg["IpPermissionsEgress"])
            except ClientError:
                pass


def _cleanup_security_groups(ec2, vpc_id: str, stats: CleanupStats):
    """Delete non-default security groups."""
    sgs = ec2.describe_security_groups(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    ).get("SecurityGroups", [])

    for sg in sgs:
        if sg["GroupName"] == "default":
            continue
        try:
            ec2.delete_security_group(GroupId=sg["GroupId"])
            stats.record_deleted(f"Security Group {sg['GroupName']} ({sg['GroupId']})")
        except ClientError as e:
            stats.record_failed(f"Security Group {sg['GroupId']}", str(e))


def _cleanup_nacls(ec2, vpc_id: str, stats: CleanupStats):
    """Delete custom (non-default) NACLs."""
    nacls = ec2.describe_network_acls(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    ).get("NetworkAcls", [])

    for nacl in nacls:
        if nacl["IsDefault"]:
            continue
        nacl_id = nacl["NetworkAclId"]
        # Remove subnet associations first (move them back to default NACL)
        for assoc in nacl.get("Associations", []):
            try:
                # Find default NACL
                default_nacl = next(
                    n for n in nacls if n["IsDefault"])
                ec2.replace_network_acl_association(
                    AssociationId=assoc["NetworkAclAssociationId"],
                    NetworkAclId=default_nacl["NetworkAclId"],
                )
            except (ClientError, StopIteration):
                pass
        try:
            ec2.delete_network_acl(NetworkAclId=nacl_id)
            stats.record_deleted(f"NACL {nacl_id}")
        except ClientError as e:
            stats.record_failed(f"NACL {nacl_id}", str(e))


def _cleanup_route_tables(ec2, vpc_id: str, stats: CleanupStats):
    """Delete custom route tables."""
    rts = ec2.describe_route_tables(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    ).get("RouteTables", [])

    for rt in rts:
        rt_id = rt["RouteTableId"]
        # Skip main route table (can't delete it directly)
        is_main = any(a.get("Main", False)
                      for a in rt.get("Associations", []))
        if is_main:
            continue

        # Remove associations
        for assoc in rt.get("Associations", []):
            if not assoc.get("Main", False):
                try:
                    ec2.disassociate_route_table(
                        AssociationId=assoc["RouteTableAssociationId"])
                except ClientError:
                    pass

        try:
            ec2.delete_route_table(RouteTableId=rt_id)
            stats.record_deleted(
                f"Route table {_get_tag(rt.get('Tags', []), 'Name') or rt_id}")
        except ClientError as e:
            stats.record_failed(f"Route table {rt_id}", str(e))


def _cleanup_subnets(ec2, vpc_id: str, stats: CleanupStats):
    """Delete subnets."""
    subnets = ec2.describe_subnets(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    ).get("Subnets", [])

    for subnet in subnets:
        subnet_id = subnet["SubnetId"]
        name = _get_tag(subnet.get("Tags", []), "Name") or subnet["CidrBlock"]
        try:
            ec2.delete_subnet(SubnetId=subnet_id)
            stats.record_deleted(f"Subnet {name} ({subnet_id})")
        except ClientError as e:
            stats.record_failed(f"Subnet {subnet_id}", str(e))


def _cleanup_igws(ec2, vpc_id: str, stats: CleanupStats):
    """Detach and delete Internet Gateways."""
    igws = ec2.describe_internet_gateways(
        Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
    ).get("InternetGateways", [])

    for igw in igws:
        igw_id = igw["InternetGatewayId"]
        try:
            ec2.detach_internet_gateway(
                InternetGatewayId=igw_id, VpcId=vpc_id)
            ec2.delete_internet_gateway(InternetGatewayId=igw_id)
            stats.record_deleted(f"Internet Gateway {igw_id}")
        except ClientError as e:
            stats.record_failed(f"Internet Gateway {igw_id}", str(e))


def cleanup_s3(s3_client, stats: CleanupStats):
    """Empty and delete FlowForge S3 buckets."""
    print("\n" + _bold("--- S3 Buckets ---"))
    try:
        buckets = s3_client.list_buckets().get("Buckets", [])
    except ClientError:
        print("  Could not list S3 buckets.")
        return

    ff_buckets = [b for b in buckets
                  if b["Name"].startswith(FLOWFORGE_PREFIX)]

    if not ff_buckets:
        print("  No FlowForge S3 buckets found.")
        return

    s3_resource = boto3.resource("s3")
    for bucket_info in ff_buckets:
        name = bucket_info["Name"]
        try:
            bucket = s3_resource.Bucket(name)
            # Delete all objects (including versions)
            bucket.object_versions.all().delete()
            bucket.objects.all().delete()
            # Delete the bucket
            s3_client.delete_bucket(Bucket=name)
            stats.record_deleted(f"S3 bucket {name}")
        except ClientError as e:
            stats.record_failed(f"S3 bucket {name}", str(e))


def cleanup_ecr(ecr_client, stats: CleanupStats):
    """Delete FlowForge ECR repositories."""
    print("\n" + _bold("--- ECR Repositories ---"))
    try:
        repos = ecr_client.describe_repositories().get("repositories", [])
    except ClientError:
        print("  Could not list ECR repositories.")
        return

    ff_repos = [r for r in repos
                if r["repositoryName"].startswith(FLOWFORGE_PREFIX)
                or r["repositoryName"].startswith(f"{FLOWFORGE_PREFIX}/")]

    if not ff_repos:
        print("  No FlowForge ECR repositories found.")
        return

    for repo in ff_repos:
        repo_name = repo["repositoryName"]
        try:
            ecr_client.delete_repository(
                repositoryName=repo_name, force=True)
            stats.record_deleted(f"ECR repository {repo_name}")
        except ClientError as e:
            stats.record_failed(f"ECR repository {repo_name}", str(e))


def cleanup_iam(iam_client, stats: CleanupStats):
    """Delete FlowForge IAM resources in dependency order."""
    print("\n" + _bold("--- IAM Resources ---"))

    # Instance Profiles
    try:
        profiles = iam_client.list_instance_profiles().get(
            "InstanceProfiles", [])
        ff_profiles = [ip for ip in profiles
                       if ip["InstanceProfileName"].startswith(FLOWFORGE_PREFIX)]
        for ip in ff_profiles:
            ip_name = ip["InstanceProfileName"]
            # Remove roles from instance profile
            for role in ip.get("Roles", []):
                try:
                    iam_client.remove_role_from_instance_profile(
                        InstanceProfileName=ip_name,
                        RoleName=role["RoleName"],
                    )
                except ClientError:
                    pass
            try:
                iam_client.delete_instance_profile(
                    InstanceProfileName=ip_name)
                stats.record_deleted(f"Instance profile {ip_name}")
            except ClientError as e:
                stats.record_failed(f"Instance profile {ip_name}", str(e))
    except ClientError:
        pass

    # Roles
    try:
        roles = iam_client.list_roles().get("Roles", [])
        ff_roles = [r for r in roles
                    if r["RoleName"].startswith(FLOWFORGE_PREFIX)]
        for role in ff_roles:
            role_name = role["RoleName"]
            # Detach managed policies
            attached = iam_client.list_attached_role_policies(
                RoleName=role_name).get("AttachedPolicies", [])
            for pol in attached:
                iam_client.detach_role_policy(
                    RoleName=role_name, PolicyArn=pol["PolicyArn"])
            # Delete inline policies
            inline = iam_client.list_role_policies(
                RoleName=role_name).get("PolicyNames", [])
            for pol_name in inline:
                iam_client.delete_role_policy(
                    RoleName=role_name, PolicyName=pol_name)
            try:
                iam_client.delete_role(RoleName=role_name)
                stats.record_deleted(f"IAM role {role_name}")
            except ClientError as e:
                stats.record_failed(f"IAM role {role_name}", str(e))
    except ClientError:
        pass

    # Users
    try:
        users = iam_client.list_users().get("Users", [])
        ff_users = [u for u in users
                    if u["UserName"].startswith(FLOWFORGE_PREFIX)]
        for user in ff_users:
            uname = user["UserName"]
            # Remove from groups
            groups = iam_client.list_groups_for_user(
                UserName=uname).get("Groups", [])
            for g in groups:
                iam_client.remove_user_from_group(
                    GroupName=g["GroupName"], UserName=uname)
            # Delete access keys
            keys = iam_client.list_access_keys(
                UserName=uname).get("AccessKeyMetadata", [])
            for key in keys:
                iam_client.delete_access_key(
                    UserName=uname, AccessKeyId=key["AccessKeyId"])
            # Detach managed policies
            attached = iam_client.list_attached_user_policies(
                UserName=uname).get("AttachedPolicies", [])
            for pol in attached:
                iam_client.detach_user_policy(
                    UserName=uname, PolicyArn=pol["PolicyArn"])
            # Delete inline policies
            inline = iam_client.list_user_policies(
                UserName=uname).get("PolicyNames", [])
            for pol_name in inline:
                iam_client.delete_user_policy(
                    UserName=uname, PolicyName=pol_name)
            # Delete login profile if exists
            try:
                iam_client.delete_login_profile(UserName=uname)
            except ClientError:
                pass
            # Delete MFA devices
            try:
                mfas = iam_client.list_mfa_devices(
                    UserName=uname).get("MFADevices", [])
                for mfa in mfas:
                    iam_client.deactivate_mfa_device(
                        UserName=uname,
                        SerialNumber=mfa["SerialNumber"])
                    iam_client.delete_virtual_mfa_device(
                        SerialNumber=mfa["SerialNumber"])
            except ClientError:
                pass
            try:
                iam_client.delete_user(UserName=uname)
                stats.record_deleted(f"IAM user {uname}")
            except ClientError as e:
                stats.record_failed(f"IAM user {uname}", str(e))
    except ClientError:
        pass

    # Groups
    try:
        groups = iam_client.list_groups().get("Groups", [])
        ff_groups = [g for g in groups
                     if g["GroupName"].startswith(FLOWFORGE_PREFIX)
                     or g["GroupName"] in ("deployers", "administrators")]
        for group in ff_groups:
            gname = group["GroupName"]
            # Remove remaining users
            members = iam_client.get_group(
                GroupName=gname).get("Users", [])
            for m in members:
                try:
                    iam_client.remove_user_from_group(
                        GroupName=gname, UserName=m["UserName"])
                except ClientError:
                    pass
            # Detach policies
            attached = iam_client.list_attached_group_policies(
                GroupName=gname).get("AttachedPolicies", [])
            for pol in attached:
                iam_client.detach_group_policy(
                    GroupName=gname, PolicyArn=pol["PolicyArn"])
            # Delete inline policies
            inline = iam_client.list_group_policies(
                GroupName=gname).get("PolicyNames", [])
            for pol_name in inline:
                iam_client.delete_group_policy(
                    GroupName=gname, PolicyName=pol_name)
            try:
                iam_client.delete_group(GroupName=gname)
                stats.record_deleted(f"IAM group {gname}")
            except ClientError as e:
                stats.record_failed(f"IAM group {gname}", str(e))
    except ClientError:
        pass

    # Policies (customer-managed)
    try:
        policies = iam_client.list_policies(Scope="Local").get("Policies", [])
        ff_policies = [p for p in policies
                       if p["PolicyName"].startswith("FlowForge")
                       or p["PolicyName"].startswith(FLOWFORGE_PREFIX)]
        for pol in ff_policies:
            arn = pol["Arn"]
            # Delete non-default versions
            versions = iam_client.list_policy_versions(
                PolicyArn=arn).get("Versions", [])
            for v in versions:
                if not v["IsDefaultVersion"]:
                    iam_client.delete_policy_version(
                        PolicyArn=arn, VersionId=v["VersionId"])
            try:
                iam_client.delete_policy(PolicyArn=arn)
                stats.record_deleted(f"IAM policy {pol['PolicyName']}")
            except ClientError as e:
                stats.record_failed(f"IAM policy {pol['PolicyName']}", str(e))
    except ClientError:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Clean up all FlowForge AWS resources created during the DevOps course.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting anything",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts",
    )
    args = parser.parse_args()

    # Create AWS clients
    try:
        session = boto3.Session(region_name=args.region)
        ec2 = session.client("ec2")
        rds_client = session.client("rds")
        s3_client = session.client("s3")
        ecr_client = session.client("ecr")
        iam_client = session.client("iam")

        # Quick connectivity test
        ec2.describe_regions(RegionNames=[args.region])
    except NoCredentialsError:
        print(_red("ERROR: AWS credentials not configured."))
        print("Configure credentials using one of:")
        print("  1. aws configure")
        print("  2. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        print("  3. Use an IAM instance profile (if running on EC2)")
        print("\nSee: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html")
        sys.exit(1)
    except EndpointConnectionError:
        print(_red(f"ERROR: Cannot connect to AWS in region {args.region}."))
        print("Check your internet connection and region name.")
        sys.exit(1)
    except ClientError as e:
        print(_red(f"ERROR: AWS API error: {e}"))
        sys.exit(1)

    print(_bold(f"\nFlowForge AWS Cleanup -- Region: {args.region}"))
    print("=" * 60)

    # Discover resources
    print("\nDiscovering FlowForge resources...")
    resources = discover_resources(
        ec2, rds_client, s3_client, ecr_client, iam_client, args.region)

    if not resources:
        print(_green("\nNo FlowForge resources found. Nothing to clean up."))
        sys.exit(0)

    # Display discovered resources
    total_count = sum(len(v) for v in resources.values())
    print(f"\nFound {_bold(str(total_count))} resources across "
          f"{len(resources)} categories:\n")
    for category, items in resources.items():
        print(f"  {_bold(category)} ({len(items)}):")
        for item in items:
            print(f"    - {item}")

    # Dry-run mode
    if args.dry_run:
        print(_yellow(f"\nDRY RUN: No resources were deleted."))
        print("Remove --dry-run to perform actual cleanup.")
        sys.exit(0)

    # Confirm
    if not confirm_deletion(total_count, args.force):
        print(_yellow("\nCancelled. No resources were deleted."))
        sys.exit(0)

    # Execute cleanup in dependency order
    stats = CleanupStats()

    cleanup_ec2_instances(ec2, stats)
    cleanup_key_pairs(ec2, stats)
    cleanup_rds(rds_client, stats)
    cleanup_nat_gateways(ec2, stats)
    cleanup_elastic_ips(ec2, stats)
    cleanup_vpc_resources(ec2, stats)
    cleanup_s3(s3_client, stats)
    cleanup_ecr(ecr_client, stats)
    cleanup_iam(iam_client, stats)

    stats.print_summary()

    if stats.failed:
        print(_yellow("\nSome resources failed to delete. Re-run the script to retry."))
        sys.exit(1)
    else:
        print(_green("\nAll FlowForge resources cleaned up successfully!"))
        print("Verify in the AWS Console: https://console.aws.amazon.com/")
        sys.exit(0)


if __name__ == "__main__":
    main()
