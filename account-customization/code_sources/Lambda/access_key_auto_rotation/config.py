
"""Config.

Provides configuration for the application.
"""

import os
from dataclasses import dataclass
import datetime

# Logging configuration
import logging
log = logging.getLogger()
log.setLevel(logging.INFO)


@dataclass
class Config:
    """Configuration for the application."""

    # Email Template for Enforce Mode
    emailTemplateEnforce = os.getenv('EmailTemplateEnforce')

    # Email Template for Audit Mode
    emailTemplateAudit = os.getenv('EmailTemplateAudit')

    # The IAM Group being used to exclue users from this IAM key rotation
    # script
    iamExemptionGroup = os.getenv('IAMExemptionGroup')

    # The tag key used to indicate the owner of an IAM user resource
    resourceOwnerTag = os.getenv('ResourceOwnerTag')

    # The Arn of the Lambda Function used for Notification
    notifierLambdaArn = os.getenv('NotifierArn')

    # The IAM Assumed Role
    iamAssumedRoleName = os.getenv('IAMAssumedRoleName')

    # The IAM Role Session Name
    roleSessionName = os.getenv('RoleSessionName')

    # The Secret Manager
    storeSecretsInCentralAccount = str(os.getenv('StoreSecretsInCentralAccount')).lower() == 'true'

    # Flag- If lambda is running  in VPC
    runLambdaInVPC = str(os.getenv('RunLambdaInVPC')).lower() == 'true'

    # Replication Regions
    replicationRegionsStr = os.getenv('CredentialReplicationRegions')
    if len(replicationRegionsStr) > 0:
        replicationRegions = replicationRegionsStr.split(",")
    else:
        replicationRegions = []
    # The number of days after which a key should be rotated
    # Default = 90 days
    rotationPeriod = int(os.getenv('RotationPeriod', 90))

    # Installation being time between rotation and deactivation
    installation_grace_period = int(os.getenv('InstallationGracePeriod', 7))

    # Recovery between deactivation and deletion
    recovery_grace_period = int(os.getenv('RecoveryGracePeriod', 7))

    # how many days ahead of time to warn users of pending actions
    pending_action_warn_period = int(os.getenv('PendingActionWarnPeriod', 7))

    # Functionality flag that Enables/Disables key rotation functionality. 
    # 'True' only sends notifications to end users (Audit Mode).
    # 'False' preforms key rotation and sends notifications to end users (Remediation Mode)."
    dryrun = str(os.getenv('DryRunFlag')).lower() == 'true'

    # Format for name of ASM secrets
    secretNameFormat = 'Account_{}_User_{}_AccessKey'

    # Format for ARN of ASM secrets
    secretArnFormat = 'arn:{partition}:secretsmanager:{region_name}:' \
                      '{account_id}:secret:{secret_name}'
    # The account used to list accounts in the Organization
    orgListAccount = os.getenv('OrgListAccount')

    # The role used to list accounts in the Organization
    orgListRole = os.getenv('OrgListRole')

    # Format for Secret Manager Resource Policy
    secretPolicyFormat = """{{
        "Version": "2012-10-17",
        "Statement": [
            {{
                "Effect": "Allow",
                "Principal": {{
                    "AWS": "{user_arn}"
                }},
                "Action": [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:ListSecretVersionIds",
                    "secretsmanager:ListSecrets"
                ],
                "Resource": "*"
            }}
        ]
    }}
    """

    iamPolicyFormat = """{{
        "Version": "2012-10-17",
        "Statement": [
            {{
                "Sid": "RetrieveSecretValue",
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:ListSecretVersionIds"
                ],
                "Resource": "{secret_arn}"
            }},
            {{
                "Sid": "ListSecret",
                "Effect": "Allow",
                "Action": "secretsmanager:ListSecrets",
                "Resource": "*"
            }}
        ]
    }}
    """
