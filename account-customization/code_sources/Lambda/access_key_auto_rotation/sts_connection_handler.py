

"""STS Connection Handler.

This module provides the functionality to establish connections to 
different AWS accounts.
"""

import boto3

from aws_partitions import get_partition_for_region
from config import Config, log


def get_account_session(aws_account_id, iam_assumed_role_name):
    config = Config()

    my_session = boto3.session.Session()
    my_region = my_session.region_name
    partition = get_partition_for_region(my_region)
    # Call the assume_role method of the STSConnection object and pass the
    # role ARN and a role session name.
    roleArnString = f"arn:{partition}:iam::{aws_account_id}:" \
                    f"role/{iam_assumed_role_name}"
    # Create an STS client object that represents a live connection to the
    # STS service
    if Config.runLambdaInVPC:
        base_sts_client = my_session.client('sts', region_name=my_region, endpoint_url="https://sts." + my_region + ".amazonaws.com")
    else:
        base_sts_client = my_session.client('sts')
    try:
        credentials = base_sts_client.assume_role(
            RoleArn=roleArnString,
            RoleSessionName=config.roleSessionName
        )['Credentials']
    except base_sts_client.exceptions.ClientError as error:
        log.error(
            f'Check that AccountID: [{aws_account_id}] has the correct IAM'
            f' Assume Role deployed to it via the CloudFormation StackSet'
            f' Template. Raw Error: {error}')
        raise

    # From the response that contains the assumed role, get the temporary
    # credentials that can be used to make subsequent API calls
    assumed_session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    return assumed_session
