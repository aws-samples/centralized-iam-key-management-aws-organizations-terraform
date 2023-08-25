


import time

from config import Config, log
from sts_connection_handler import get_account_session
from force_rotation_handler import check_force_rotate_users
from account_scan import get_actions_for_account
from notification_handler import send_to_notifier
from key_actions import log_actions, execute_actions
import boto3

timestamp = int(round(time.time() * 1000))

config = Config()


def lambda_handler(event, context):
    """Handler for Lambda.

    :param event: Dictionary account object (Account ID and Email) sent to Lambda via 'Account Inventory' Lambda Function
    :param context: Lambda context object
    """

    log.info('Function starting.')
    log.info(event)

    # Error handling - Ensure that the correct object is getting passed
    # to the function
    if "account" not in event and "email" not in event and "name" not in event:
        log.error(
            'The JSON Event Message getting passed to this Lambda Function'
            ' is malformed. Please ensure it has "account", "name" and "email" as'
            ' part of the JSON body.')

    # check for users to be force rotated via test event
    force_rotate_users = check_force_rotate_users(event)

    # check for dryrun flag
    dryrun = str(event.get('dryrun')).lower() == 'true' or config.dryrun

    # Parse event to get Account ID and Email
    aws_account_id = event['account']
    account_name = event['name']
    account_email = event['email']
    log.info(f'Currently evaluating Account ID: {aws_account_id} | Account Name: {account_name}')

    account_session = get_account_session(aws_account_id, config.iamAssumedRoleName)
    central_account_session = get_account_session(Config.orgListAccount, config.orgListRole)
    log.info(config.storeSecretsInCentralAccount)
    if config.storeSecretsInCentralAccount:
        log.info("Secret will be stored in Central Account")
        my_region = account_session.region_name
        if Config.runLambdaInVPC:
            central_account_sm_client = central_account_session.client('secretsmanager', region_name=my_region, endpoint_url="https://secretsmanager." + my_region + ".amazonaws.com")
        else:
            central_account_sm_client = central_account_session.client('secretsmanager', region_name=my_region)
    else:
        log.info("Secret will be stored in tenant  Account")
        central_account_sm_client = None
    action_queue = get_actions_for_account(account_session, force_rotate_users)

    if action_queue:
        log_actions(action_queue, dryrun)

        # Extract subsets of actions for resource owners
        resource_owners = {action.get("resource_owner") for action in action_queue}
        resource_owners.discard(None)
        resource_actions = {}
        for resource_owner in resource_owners:
            resource_actions[resource_owner] = [action for action in action_queue if action.get("resource_owner") == resource_owner]

        # Send notifications
        if dryrun:
            send_to_notifier(context, aws_account_id, account_name, account_email,
                             action_queue, dryrun, config.emailTemplateAudit)
            for resource_owner in resource_owners:
                send_to_notifier(context, aws_account_id, account_name, resource_owner,
                                resource_actions[resource_owner], dryrun, config.emailTemplateAudit)
        else:
            execute_actions(action_queue, account_session, central_account_sm_client)
            send_to_notifier(context, aws_account_id, account_name, account_email,
                             action_queue, dryrun, config.emailTemplateEnforce)
            for resource_owner in resource_owners:
                send_to_notifier(context, aws_account_id, account_name, resource_owner,
                                resource_actions[resource_owner], dryrun, config.emailTemplateEnforce)

    log.info('---------------------------')
    log.info('Function has completed.')
