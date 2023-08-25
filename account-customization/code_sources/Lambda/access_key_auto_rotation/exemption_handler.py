

"""Exemption Handler.

This module provides the functionality necessary to exclude users
from key rotation based on user defined IAM Group.
"""

from config import log


def get_exemption_group(groupName, iam_client):
    """
    Gets the current list of exempt user accounts.

    :return The current list of exempt user accounts.
    """
    exemption_group_users = []

    try:
        exemption_group_response = iam_client.get_group(GroupName=groupName)
        exemption_group = exemption_group_response['Users']

        for users in exemption_group:
            user_name = users['UserName']
            exemption_group_users.append(user_name)

        if not exemption_group_users:
            log.info(f'The exempted users list [{groupName}] is empty.')
        else:
            log.info(
                f'The exempted users list [{groupName}] has active '
                f'exemptions.')

    except iam_client.exceptions.ClientError as error:
        log.info(
            f'The IAM Group [{groupName}] does not exist in this account. '
            f'Skipping exemptions check.')

    return exemption_group_users


def validate_exemption_group(iamExemptionGroup, iam_client, log):
    # Initialize Values
    exemption_group = None

    # Check to see if user entered an IAM Exemption Group
    # (check to see if iamExemptionGroup is not blank).
    if iamExemptionGroup:
        log.info(
            f'The following IAM Exemption Group was configured via '
            f'CloudFormation Template [{iamExemptionGroup}]')

        # If IAM Exemption Group was added, check to see if the IAM Group
        # exists within the account's IAM Service.
        try:
            exempt_list = get_exemption_group(
                iamExemptionGroup, iam_client)
            exemption_group = True
        except iam_client.exceptions.ClientError as error:
            log.error(
                f'An IAM Exemption Group name was added to the CloudFormation'
                f' Template but the IAM Group does not exist in this account. '
                f'Please double check that the Assumed Role CloudFormation '
                f'StackSet was deployed successfully to this account. '
                f'Raw Error: {error}')
            exempt_list = []
            exemption_group = False
    else:
        log.info(
            'An IAM Exemption Group name was not added to the CloudFormation '
            'Template. Please double check your CloudFormation deployment.')
        exempt_list = []
        exemption_group = False

    return exemption_group, exempt_list
