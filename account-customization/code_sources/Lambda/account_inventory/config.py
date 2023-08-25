

"""Config.

Provides configuration for the application.
"""

import os
from dataclasses import dataclass

# Logging configuration
import logging
log = logging.getLogger()
log.setLevel(logging.INFO)


@dataclass
class Config:
    """Configuration for the application."""

    # The account used to list accounts in the Organization
    orgListAccount = os.getenv('OrgListAccount')

    # The role used to list accounts in the Organization
    orgListRole = os.getenv('OrgListRole')

    # The IAM Role Session Name
    roleSessionName = os.getenv('RoleSessionName')

    # Flag- If lambda is running  in VPC
    runLambdaInVPC = str(os.getenv('RunLambdaInVPC')).lower() == 'true'
