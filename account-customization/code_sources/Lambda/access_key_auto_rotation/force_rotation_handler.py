

"""Force AWS IAM Key Rotation Handler.

This module provides the functionality necessary to run unit
tests against this lambda function. By passing 
"ForceRotate": "USERNAME" in the test event, you can simulate
the functions rotation logic.
"""

from config import log


def check_forced_rotate_flag(event, noUsers, log):
    # Initialize Values
    force_rotate = None
    force_rotate_user_name = None

    log.info('Checking if ForceRotate flag exists.')

    # Check if the message sent to the Lambda contained the value 'ForceRotate'
    # Note: This currently only supports one username at a time for testing
    if "ForceRotate" in event and not noUsers:
        force_rotate_user_name = event['ForceRotate']
        force_rotate = True
        log.info(f'ForceRotate flag exists for [{force_rotate_user_name}].')
    elif "ForceRotate" not in event and not noUsers:
        force_rotate = False
        log.info(
            'ForceRotate flag does not exist and '
            'there are users in this account.')
    elif "ForceRotate" not in event and not noUsers:
        log.info(
            f'ForceRotate flag exists for [{force_rotate_user_name}]'
            f' but there are no users in this account.')
        force_rotate = True
    else:
        log.error('Undetected type. Listing noUsers(boolean) and users(array)')
        force_rotate = False

    return force_rotate, force_rotate_user_name


def check_force_rotate_users(event):
    # Check if ForceRotate flag exists in event -- function from
    # force_rotation_handler.py
    force_rotate_array = check_forced_rotate_flag(event, False, log)
    force_rotate = force_rotate_array[0]
    force_rotate_user_name = force_rotate_array[1]

    if force_rotate and force_rotate_user_name:
        force_rotate_users = [force_rotate_user_name]
    else:
        force_rotate_users = []

    return force_rotate_users
