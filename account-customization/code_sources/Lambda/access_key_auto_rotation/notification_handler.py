

"""Notification Handler.

Function for formatting JSON object and invoking the Notifier Module's Lambda.
"""
import json
import boto3
import datetime
import dateutil.tz

from aws_partitions import get_partition_name
from account_scan import ActionReasons
from config import Config, log

config = Config()


def format_notifier_payload(context, account_id, account_name, recipient_email, action_queue,
                            dryrun, email_template):
    lambdaArn = str(context.invoked_function_arn)
    partition = lambdaArn.split(':')[1]
    partition_name = get_partition_name(partition)
    now = datetime.datetime.now(datetime.timezone.utc)

    # TODO Should this be turned into a CloudFormation variable or
    #  added to script logic?
    subject = "[IMPORTANT] AWS IAM Access Key Security Violation" \
              " Detected in your Account."

    actions_formatted = []
    for action_spec in action_queue:
        action = action_spec['action']
        key_metadata = action_spec['key']
        user_name = key_metadata['UserName']
        access_key_id = key_metadata["AccessKeyId"]
        reason = action_spec['reason']
        message = ''
        if action != 'WARN':
            if dryrun:
                message = f'DRYRUN: {action} key {user_name}:{access_key_id}.' \
                          f'  {reason.value}'
            else:
                message = f'ACTION: {action} key {user_name}:{access_key_id}.' \
                          f'  {reason.value}'
        else:
            action_date = action_spec['action_date']
            delta = action_date - now
            delta_days = round(delta.total_seconds() / 86400)

            if reason == ActionReasons.KEY_PENDING_ROTATION:
                message = f'WARNING: Key {user_name}:{access_key_id} ' \
                          f'will expire in {delta_days} days and will be ' \
                          f'rotated.  Please be ready to install the new key.'
            elif reason == ActionReasons.KEY_PENDING_DEACTIVATION:
                message = f'WARNING: Key {user_name}:{access_key_id} ' \
                          f'installation grace period will end in' \
                          f' {delta_days} days and will be deactivated.' \
                          f'  Please verify the new key is installed.'
            elif reason == ActionReasons.KEY_PENDING_DELETION:
                message = f'WARNING: Key {user_name}:{access_key_id} ' \
                          f'recovery grace period will end in' \
                          f' {delta_days} days and will be permanently ' \
                          f'deleted.  Please verify the new key is ' \
                          f'installed and working.'
            elif reason == ActionReasons.UNUSED_KEY_PENDING_DELETION:
                message = f'WARNING: Key {user_name}:{access_key_id} ' \
                          f'will expire in {delta_days} days and has never ' \
                          f'been used.  Key will be permanently deleted.'
            elif reason == ActionReasons.KEY_PENDING_EXPIRATION_CONFLICT:
                message = f'CRITICAL: Key {user_name}:{access_key_id} ' \
                          f'will expire in {delta_days} days and cannot ' \
                          f'be rotated because another key exists for the ' \
                          f'user!  It will be permanently deleted when the' \
                          f' other key expires or the grace period ends!  ' \
                          f'Please make sure this key is not being used!'
            elif reason == ActionReasons.KEY_PENDING_DELETION_CONFLICT:
                message = f'CRITICAL: Key {user_name}:{access_key_id} ' \
                          f'will be permanently deleted in {delta_days} days' \
                          f' due to a conflict with another key for the ' \
                          f'user!  It may be deactivated sooner if the grace' \
                          f' period ends!  Please make sure this key is not' \
                          f' being used!'

        actions_formatted.append(message)

    # Timestamp for function runtime/invoked date
    now = datetime.datetime.now(tz=dateutil.tz.gettz('UTC'))
    timestamp = now.isoformat()
    template_values = {
        'account_id': account_id,
        'account_name': account_name,
        'timestamp': timestamp,
        'actions': actions_formatted,
        'rotation_period': config.rotationPeriod,
        'installation_grace_period': config.installation_grace_period,
        'recovery_grace_period': config.recovery_grace_period,
        'partition_name': partition_name
    }

    jsonPayload = {
        "email": recipient_email,
        "invoked_by": lambdaArn,
        "subject": subject,
        "email_template": email_template,
        "template_values": template_values
    }

    lambdaPayloadEncoded = json.dumps(jsonPayload).encode('utf-8')

    return lambdaPayloadEncoded


def send_to_notifier(context, account_id, account_name, recipient_email, action_queue, dryrun,
                     email_template):
    lambdaPayloadEncoded = format_notifier_payload(context, account_id, account_name,
                                                   recipient_email, action_queue,
                                                   dryrun, email_template)

    # AWS Lambda Client
    lambda_client = boto3.client('lambda')

    try:
        response = lambda_client.invoke(FunctionName=config.notifierLambdaArn,
                                        InvocationType='Event',
                                        Payload=lambdaPayloadEncoded)
        log.info(
            f"--Invoked Lambda Function={config.notifierLambdaArn},"
            f" InvocationType=Event, Payload={str(lambdaPayloadEncoded)}")
    except lambda_client.exceptions.ClientError as error:
        print(error)
    return response
