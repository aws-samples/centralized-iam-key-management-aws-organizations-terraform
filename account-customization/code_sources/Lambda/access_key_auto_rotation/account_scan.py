
"""Key Actions - Mapping of Action Reasons.

This class provides the mappings to different key
rotation logic actions.
"""

import datetime
import dateutil.tz

from enum import Enum
from config import Config, log
from exemption_handler import validate_exemption_group


class ActionReasons(Enum):
    UNUSED_EXPIRED_KEY = 'Expired key has never been used.'
    EXPIRED_ACTIVE_KEY = 'Active key has expired.'
    FORCED_ROTATION = 'Forced active key rotation.'
    EXPIRED_ACTIVE_KEY_CONFLICT_LRU = 'Expired active key with conflict, ' \
                                      'least recently used.'
    EXPIRED_INACTIVE_KEY_CONFLICT = 'Expired key with conflict, already ' \
                                    'inactive.'
    FORCED_ROTATION_CONFLICT_LRU = 'Forced active key rotation with conflict, ' \
                                   'least recently used.'
    FORCED_INACTIVE_KEY_CONFLICT = 'Forced rotation with conflict, already ' \
                                   'inactive.'
    INSTALL_GRACE_PERIOD_END = 'Installation grace period has ended.'
    RECOVER_GRACE_PERIOD_END = 'Recovery grace period has ended.'
    KEY_PENDING_ROTATION = 'Key will be rotated soon.'
    KEY_PENDING_DEACTIVATION = 'Key will be deactivated soon, ' \
                               'please install new key.'
    KEY_PENDING_DELETION = 'Key will be permanently deleted soon, ' \
                           'please validate new key.'
    KEY_PENDING_EXPIRATION_CONFLICT = 'Key will expire soon, cannot be ' \
                                      'rotated due to presence of other key.'
    KEY_PENDING_DELETION_CONFLICT = 'Key will be permanently deleted soon, ' \
                                    'due to conflict.'
    UNUSED_KEY_PENDING_DELETION = 'Key will be permanently deleted soon, ' \
                                  'key is about to expire and has never' \
                                  ' been used.'


def get_actions_for_keys(access_key_metadata, account_session,
                         force_rotate):

    config = Config()
    action_queue = []
    keys = []

    iam_client = account_session.client('iam')

    # Cache current time to avoid race conditions
    now = datetime.datetime.now(tz=dateutil.tz.gettz('US/Eastern'))
    warn_period = datetime.timedelta(days=config.pending_action_warn_period)
    installation_grace_period = datetime.timedelta(
                days=config.installation_grace_period)
    recovery_grace_period = datetime.timedelta(
                days=config.recovery_grace_period)

    for key in access_key_metadata:
        # Populate lastused and expiration dates
        try:
            key['LastUsedDate'] = iam_client.get_access_key_last_used(
                AccessKeyId=key['AccessKeyId']
                )['AccessKeyLastUsed']['LastUsedDate']
        except:
            log.info("--Key has not been used before.")
            key['LastUsedDate'] = None
            
        key['ExpireDate'] = key['CreateDate'] + \
            datetime.timedelta(days=config.rotationPeriod)
        
        # TODO: If we stored state in dynamo, we would fetch the RotateDate
        #  and the DeactivateDate here instead of dynamically computing them

        # if the key is expired and has never been used, just delete it
        if key['LastUsedDate'] is None \
                and key['ExpireDate'] <= now:
            reason = ActionReasons.UNUSED_EXPIRED_KEY
            log.info(
                f'ROTATE_AND_DELETE {key["UserName"]}: {key["AccessKeyId"]} '
                f'-- {reason.value}')
            action_queue.append({
                'action': 'ROTATE_AND_DELETE',
                'key': key,
                'reason': reason
            })
            continue

        # if the key is about to expire and has never been used, warn
        if key['LastUsedDate'] is None \
                and key['ExpireDate'] <= now + warn_period:
            reason = ActionReasons.UNUSED_KEY_PENDING_DELETION
            log.info(
                f'WARN {key["UserName"]}: {key["AccessKeyId"]} '
                f'-- {reason.value}')
            action_queue.append({
                'action': 'WARN',
                'action_date': key['ExpireDate'],
                'key': key,
                'reason': reason
            })

        keys.append(key)

    if len(keys) == 0:
        log.info('Skipping, no keys to evaluate.')
        pass

    elif len(keys) == 1:
        key = keys[0]

        if key['Status'] == 'Active':
            log.info('--Key Logic: [Active, Null]')
            # rotate expiring key
            if key['ExpireDate'] <= now:
                reason = ActionReasons.EXPIRED_ACTIVE_KEY
                # key is expired and needs to be rotated
                log.info(
                    f'ROTATE {key["UserName"]}: {key["AccessKeyId"]}'
                    f'-- {reason.value}')
                action_queue.append({
                    'action': 'ROTATE',
                    'key': key,
                    'reason': reason
                })
            # or force rotate key
            elif force_rotate:
                reason = ActionReasons.FORCED_ROTATION
                # key is force rotated
                log.info(
                    f'ROTATE {key["UserName"]}: {key["AccessKeyId"]}'
                    f'-- {reason.value}')
                action_queue.append({
                    'action': 'ROTATE',
                    'key': key,
                    'reason': reason
                })
            # warn if key is about to expire
            elif key['ExpireDate'] <= now + warn_period:
                reason = ActionReasons.KEY_PENDING_ROTATION
                log.info(
                    f'WARN {key["UserName"]}: {key["AccessKeyId"]}'
                    f'-- {reason.value}')
                action_queue.append({
                    'action': 'WARN',
                    'action_date': key['ExpireDate'],
                    'key': key,
                    'reason': reason
                })

        elif key['Status'] != 'Active':
            log.info('--Key Logic: [Inactive, Null]')
            # all we can do here is calculate grace period based on creation
            rotation_date = key['CreateDate']
            delete_date = rotation_date + \
                          installation_grace_period + \
                          recovery_grace_period

            # recovery period has ended
            if delete_date <= now:
                reason = ActionReasons.RECOVER_GRACE_PERIOD_END
                log.info(
                    f'DELETE {key["UserName"]}: '
                    f'{key["AccessKeyId"]} '
                    f'-- {reason.value}')
                action_queue.append({
                    'action': 'DELETE',
                    'key': key,
                    'reason': reason
                })
            # warn of pending deletion
            elif delete_date <= now + warn_period:
                reason = ActionReasons.KEY_PENDING_DELETION
                log.info(
                    f'WARN {key["UserName"]}: {key["AccessKeyId"]}'
                    f'-- {reason.value}')
                action_queue.append({
                    'action': 'WARN',
                    'action_date': delete_date,
                    'key': key,
                    'reason': reason
                })
            # nothing to do, key is valid
            else:
                log.info('Skipping, key is valid.')
                pass

    elif len(keys) == 2:
        num_active = len([k for k in keys if k['Status'] == 'Active'])
        if num_active == 0:
            log.info('--Key Logic: [Inactive,Inactive]')
            num_expired = len([k for k in keys if k['ExpireDate'] <= now])

            if num_expired == 2:
                # both keys are inactive and expired, just delete them
                for key in keys:
                    reason = ActionReasons.RECOVER_GRACE_PERIOD_END
                    log.info(
                        f'DELETE {key["UserName"]}: '
                        f'{key["AccessKeyId"]} '
                        f'-- {reason.value}')
                    action_queue.append({
                        'action': 'DELETE',
                        'key': key,
                        'reason': reason
                    })
            elif num_expired == 1:
                # maybe someone deactivated the new key accidentally?
                # respect the recovery grace period on the inactive key
                inactive_keys_by_create_date = sorted(
                    keys, key=lambda x: x['CreateDate'])
                expired_key = inactive_keys_by_create_date[0]
                unexpired_key = inactive_keys_by_create_date[1]
                # use the creation date of the unexpired key
                # to guess when the expired key was deactivated
                expired_key_rotation_date = unexpired_key['CreateDate']
                expired_key_delete_date = \
                    expired_key_rotation_date + \
                    installation_grace_period + \
                    recovery_grace_period
                unexpired_key_rotation_date = unexpired_key['ExpireDate']

                # delete the expired key if grace period is over
                if expired_key_delete_date <= now:
                    reason = ActionReasons.RECOVER_GRACE_PERIOD_END
                    log.info(
                        f'DELETE {expired_key["UserName"]}: '
                        f'{expired_key["AccessKeyId"]} '
                        f'-- {reason.value}')
                    action_queue.append({
                        'action': 'DELETE',
                        'key': expired_key,
                        'reason': reason
                    })
                    # warn if other key is about to be rotated
                    if unexpired_key_rotation_date <= now + warn_period:
                        rotate_reason = ActionReasons.KEY_PENDING_ROTATION
                        log.info(
                            f'WARN {unexpired_key["UserName"]}: '
                            f'{unexpired_key["AccessKeyId"]}'
                            f'-- {rotate_reason.value}')
                        action_queue.append({
                            'action': 'WARN',
                            'action_date': unexpired_key_rotation_date,
                            'key': unexpired_key,
                            'reason': rotate_reason
                        })

                # also warn if unexpired key is about to expire and be rotated
                # expired will be deleted due to conflict
                elif unexpired_key_rotation_date <= now + warn_period:
                    delete_reason = ActionReasons.KEY_PENDING_DELETION_CONFLICT
                    rotate_reason = ActionReasons.KEY_PENDING_ROTATION
                    log.info(
                        f'WARN {expired_key["UserName"]}: '
                        f'{expired_key["AccessKeyId"]}'
                        f'-- {delete_reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': unexpired_key_rotation_date,
                        'key': expired_key,
                        'reason': delete_reason
                    })
                    log.info(
                        f'WARN {unexpired_key["UserName"]}: '
                        f'{unexpired_key["AccessKeyId"]}'
                        f'-- {rotate_reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': unexpired_key_rotation_date,
                        'key': unexpired_key,
                        'reason': rotate_reason
                    })

                # warn if the grace period is about to end
                elif expired_key_delete_date <= now + warn_period:
                    reason = ActionReasons.KEY_PENDING_DELETION
                    log.info(
                        f'WARN {expired_key["UserName"]}: '
                        f'{expired_key["AccessKeyId"]}'
                        f'-- {reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': expired_key_delete_date,
                        'key': expired_key,
                        'reason': reason
                    })

            else:
                # nothing to do, both keys have not expired
                # pending expirations don't need warnings,
                # nothing will change until end of grace period
                log.info('Skipping, keys are both valid.')

        elif num_active == 1:
            # we have a key in the recycle bin, waiting to be deleted
            log.info('--Key Logic: [Active, Inactive]')
            if keys[0]['Status'] == 'Active':
                active_key = keys[0]
                inactive_key = keys[1]
            else:
                active_key = keys[1]
                inactive_key = keys[0]

            active_key_rotate_date = active_key['ExpireDate']

            if active_key_rotate_date <= now:
                # the edge case where the active key is expired
                # we should only encounter this on first deploy
                # we have to delete the inactive one
                # so we can rotate the active one
                delete_reason = ActionReasons.EXPIRED_INACTIVE_KEY_CONFLICT
                rotate_reason = ActionReasons.EXPIRED_ACTIVE_KEY
                log.info(
                    f'DELETE {inactive_key["UserName"]}: '
                    f'{inactive_key["AccessKeyId"]} '
                    f'-- {delete_reason.value}')
                log.info(
                    f'ROTATE {active_key["UserName"]}: '
                    f'{active_key["AccessKeyId"]} '
                    f'-- {rotate_reason.value}')
                action_queue.append({
                    'action': 'DELETE',
                    'key': inactive_key,
                    'reason': delete_reason
                })
                action_queue.append({
                    'action': 'ROTATE',
                    'key': active_key,
                    'reason': delete_reason
                })

            # force rotate the active key, must delete inactive key
            elif force_rotate:
                delete_reason = ActionReasons.FORCED_INACTIVE_KEY_CONFLICT
                rotate_reason = ActionReasons.FORCED_ROTATION
                log.info(
                    f'DELETE {inactive_key["UserName"]}: '
                    f'{inactive_key["AccessKeyId"]} '
                    f'-- {delete_reason.value}')
                log.info(
                    f'ROTATE {active_key["UserName"]}: '
                    f'{active_key["AccessKeyId"]} '
                    f'-- {rotate_reason.value}')
                action_queue.append({
                    'action': 'DELETE',
                    'key': inactive_key,
                    'reason': delete_reason
                })
                action_queue.append({
                    'action': 'ROTATE',
                    'key': active_key,
                    'reason': delete_reason
                })
            else:
                # check if the recovery grace period on the inactive key has passed
                # the trick here is that we use the creation date of the active key
                # to guess when the inactive key was deactivated
                if inactive_key['LastUsedDate'] is not None:
                    # if the key has a more recent last used date use that instead
                    rotation_date = max([active_key['CreateDate'],
                                         inactive_key['LastUsedDate']])
                else:
                    rotation_date = active_key['CreateDate']
                inactive_key_delete_date = rotation_date + \
                                           installation_grace_period + \
                                           recovery_grace_period

                # delete inactive key if grace period is over
                if inactive_key_delete_date <= now:
                    reason = ActionReasons.RECOVER_GRACE_PERIOD_END
                    log.info(
                        f'DELETE {inactive_key["UserName"]}: '
                        f'{inactive_key["AccessKeyId"]} '
                        f'-- {reason.value}')
                    action_queue.append({
                        'action': 'DELETE',
                        'key': inactive_key,
                        'reason': reason
                    })
                    # warn if active key is about to be rotated
                    if active_key_rotate_date <= now + warn_period:
                        reason = ActionReasons.KEY_PENDING_ROTATION
                        log.info(
                            f'WARN {active_key["UserName"]}: '
                            f'{active_key["AccessKeyId"]}'
                            f'-- {reason.value}')
                        action_queue.append({
                            'action': 'WARN',
                            'action_date': active_key_rotate_date,
                            'key': active_key,
                            'reason': reason
                        })

                # also warn if active key is about to expire
                # inactive key will be deleted due to conflict
                elif active_key_rotate_date <= now + warn_period:
                    delete_reason = ActionReasons.KEY_PENDING_DELETION_CONFLICT
                    rotate_reason = ActionReasons.KEY_PENDING_ROTATION
                    log.info(
                        f'WARN {inactive_key["UserName"]}: '
                        f'{inactive_key["AccessKeyId"]}'
                        f'-- {delete_reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': active_key_rotate_date,
                        'key': inactive_key,
                        'reason': delete_reason
                    })
                    log.info(
                        f'WARN {active_key["UserName"]}: '
                        f'{active_key["AccessKeyId"]}'
                        f'-- {rotate_reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': active_key_rotate_date,
                        'key': active_key,
                        'reason': rotate_reason
                    })

                # warn if inactive key is about to expire
                elif inactive_key_delete_date <= now + warn_period:
                    reason = ActionReasons.KEY_PENDING_DELETION
                    log.info(
                        f'WARN {inactive_key["UserName"]}: '
                        f'{inactive_key["AccessKeyId"]}'
                        f'-- {reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': inactive_key_delete_date,
                        'key': inactive_key,
                        'reason': reason
                    })

        elif num_active == 2:
            log.info('--Key Logic: [Active, Active]')
            # This means that either a key has been rotated and we are in the
            # install period, or it means that the user has two active keys that
            # need to be evaluated

            num_expired = len([k for k in keys if k['ExpireDate'] <= now])

            if num_expired == 2:
                # This is the catch 22, we have to pick one key to deactivate
                # both are expired and both have been used
                # we have no way to track the grace period if both keys are expired
                # we have to delete one and rotate the other

                delete_reason = ActionReasons.EXPIRED_ACTIVE_KEY_CONFLICT_LRU
                rotate_reason = ActionReasons.EXPIRED_ACTIVE_KEY

                # we choose to delete the least recently used key
                if keys[0]['LastUsedDate'] and keys[1]['LastUsedDate']:
                    lru_keys = sorted(keys, key=lambda x: x['LastUsedDate'])
                    key_to_delete = lru_keys[0]
                    key_to_rotate = lru_keys[1]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}]:"
                             f"[{key_to_delete['LastUsedDate']}] was last used "
                             f"before Key [{key_to_rotate['AccessKeyId']}]:"
                             f"[{key_to_rotate['LastUsedDate']}].")
                # or the one that hasn't ever been used
                elif keys[0]['LastUsedDate']:
                    key_to_delete = keys[1]
                    key_to_rotate = keys[0]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}] "
                             f"has never been used.")
                elif keys[1]['LastUsedDate']:
                    key_to_delete = keys[0]
                    key_to_rotate = keys[1]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}] "
                             f"has never been used.")
                # or the one that was created first if none have been used
                elif keys[0]['CreateDate'] <= keys[1]['CreateDate']:
                    key_to_delete = keys[0]
                    key_to_rotate = keys[1]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}]:"
                             f"[{key_to_delete['CreateDate']}] is older "
                             f"than Key [{key_to_rotate['AccessKeyId']}]:"
                             f"[{key_to_rotate['CreateDate']}].")
                else:
                    key_to_delete = keys[1]
                    key_to_rotate = keys[0]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}]:"
                             f"[{key_to_delete['CreateDate']}] is older "
                             f"than Key [{key_to_rotate['AccessKeyId']}]:"
                             f"[{key_to_rotate['CreateDate']}].")

                log.info(
                    f'DELETE {key_to_delete["UserName"]}: '
                    f'{key_to_delete["AccessKeyId"]} '
                    f'-- {delete_reason.value}')
                log.info(
                    f'ROTATE {key_to_rotate["UserName"]}: '
                    f'{key_to_rotate["AccessKeyId"]} '
                    f'-- {rotate_reason.value}')
                action_queue.append({
                    'action': 'DELETE',
                    'key': key_to_delete,
                    'reason': delete_reason
                })
                action_queue.append({
                    'action': 'ROTATE',
                    'key': key_to_rotate,
                    'reason': rotate_reason
                })

            # force rotate, so we need to delete LRU key same as above
            elif force_rotate:
                delete_reason = ActionReasons.FORCED_ROTATION_CONFLICT_LRU
                rotate_reason = ActionReasons.FORCED_ROTATION

                # we choose to delete the least recently used key
                if keys[0]['LastUsedDate'] and keys[1]['LastUsedDate']:
                    lru_keys = sorted(keys, key=lambda x: x['LastUsedDate'])
                    key_to_delete = lru_keys[0]
                    key_to_rotate = lru_keys[1]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}]:"
                             f"[{key_to_delete['LastUsedDate']}] was last used "
                             f"before Key [{key_to_rotate['AccessKeyId']}]:"
                             f"[{key_to_rotate['LastUsedDate']}].")
                # or the one that hasn't ever been used
                elif keys[0]['LastUsedDate']:
                    key_to_delete = keys[1]
                    key_to_rotate = keys[0]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}] "
                             f"has never been used.")
                elif keys[1]['LastUsedDate']:
                    key_to_delete = keys[0]
                    key_to_rotate = keys[1]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}] "
                             f"has never been used.")
                # or the one that was created first if none have been used
                elif keys[0]['CreateDate'] <= keys[1]['CreateDate']:
                    key_to_delete = keys[0]
                    key_to_rotate = keys[1]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}]:"
                             f"[{key_to_delete['CreateDate']}] is older "
                             f"than Key [{key_to_rotate['AccessKeyId']}]:"
                             f"[{key_to_rotate['CreateDate']}].")
                else:
                    key_to_delete = keys[1]
                    key_to_rotate = keys[0]
                    log.info(f"--Key [{key_to_delete['AccessKeyId']}]:"
                             f"[{key_to_delete['CreateDate']}] is older "
                             f"than Key [{key_to_rotate['AccessKeyId']}]:"
                             f"[{key_to_rotate['CreateDate']}].")

                log.info(
                    f'DELETE {key_to_delete["UserName"]}: '
                    f'{key_to_delete["AccessKeyId"]} '
                    f'-- {delete_reason.value}')
                log.info(
                    f'ROTATE {key_to_rotate["UserName"]}: '
                    f'{key_to_rotate["AccessKeyId"]} '
                    f'-- {rotate_reason.value}')
                action_queue.append({
                    'action': 'DELETE',
                    'key': key_to_delete,
                    'reason': delete_reason
                })
                action_queue.append({
                    'action': 'ROTATE',
                    'key': key_to_rotate,
                    'reason': rotate_reason
                })

            elif num_expired == 1:
                # only one expired
                if keys[0]['ExpireDate'] <= now:
                    expired_key = keys[0]
                    unexpired_key = keys[1]
                else:
                    expired_key = keys[1]
                    unexpired_key = keys[0]

                # we assume the creation date of the other key
                # is the date the key was rotated
                expired_key_rotation_date = unexpired_key['CreateDate']
                expired_key_deactivation_date = expired_key_rotation_date + \
                                                installation_grace_period
                unexpired_key_rotation_date = unexpired_key['ExpireDate']

                # deactivate the expired key if the grace period is ended
                if expired_key_deactivation_date <= now:
                    reason = ActionReasons.INSTALL_GRACE_PERIOD_END
                    log.info(
                        f'DEACTIVATE {expired_key["UserName"]}: '
                        f'{expired_key["AccessKeyId"]} '
                        f'-- {reason.value}')
                    action_queue.append({
                        'action': 'DEACTIVATE',
                        'key': expired_key,
                        'reason': reason
                    })
                    # warn if the unexpired key is about to expire
                    if unexpired_key_rotation_date <= now + warn_period:
                        reason = ActionReasons.KEY_PENDING_ROTATION
                        log.info(
                            f'WARN {unexpired_key["UserName"]}: '
                            f'{unexpired_key["AccessKeyId"]}'
                            f'-- {reason.value}')
                        action_queue.append({
                            'action': 'WARN',
                            'action_date': unexpired_key_rotation_date,
                            'key': unexpired_key,
                            'reason': reason
                        })

                # warn if the unexpired key is about to be rotated
                # the expired key will be deleted due to conflict
                elif unexpired_key_rotation_date <= now + warn_period:
                    delete_reason = ActionReasons.KEY_PENDING_DELETION_CONFLICT
                    rotate_reason = ActionReasons.KEY_PENDING_ROTATION
                    log.info(
                        f'WARN {expired_key["UserName"]}: '
                        f'{expired_key["AccessKeyId"]}'
                        f'-- {delete_reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': unexpired_key_rotation_date,
                        'key': expired_key,
                        'reason': delete_reason
                    })
                    log.info(
                        f'WARN {unexpired_key["UserName"]}: '
                        f'{unexpired_key["AccessKeyId"]}'
                        f'-- {rotate_reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': unexpired_key_rotation_date,
                        'key': unexpired_key,
                        'reason': rotate_reason
                    })

                # warn if the expired key is about to be deactivated
                elif expired_key_deactivation_date <= now + warn_period:
                    reason = ActionReasons.KEY_PENDING_DEACTIVATION
                    log.info(
                        f'WARN {expired_key["UserName"]}: '
                        f'{expired_key["AccessKeyId"]}'
                        f'-- {reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': expired_key_deactivation_date,
                        'key': expired_key,
                        'reason': reason
                    })

            elif num_expired == 0:
                log.info('Keys are both valid.')
                # it's harder than it seems to warn of pending actions
                keys_by_expire_date = sorted(
                    keys, key=lambda x: x['ExpireDate'])
                older_key = keys_by_expire_date[0]
                newer_key = keys_by_expire_date[1]
                older_key_expire_date = older_key['ExpireDate']
                newer_key_rotation_date = newer_key['ExpireDate']

                # warn if newer key is about to expire
                # older will be deleted due to conflict
                if newer_key_rotation_date <= now + warn_period:
                    delete_reason = ActionReasons.KEY_PENDING_DELETION_CONFLICT
                    rotate_reason = ActionReasons.KEY_PENDING_ROTATION
                    log.info(
                        f'WARN {older_key["UserName"]}: '
                        f'{older_key["AccessKeyId"]}'
                        f'-- {delete_reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': newer_key_rotation_date,
                        'key': older_key,
                        'reason': delete_reason
                    })
                    log.info(
                        f'WARN {newer_key["UserName"]}: '
                        f'{newer_key["AccessKeyId"]}'
                        f'-- {rotate_reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': newer_key_rotation_date,
                        'key': newer_key,
                        'reason': rotate_reason
                    })

                # warn if first key will expire
                # it can't be rotated due to conflict
                elif older_key_expire_date <= now + warn_period:
                    reason = ActionReasons.KEY_PENDING_EXPIRATION_CONFLICT
                    log.info(
                        f'WARN {older_key["UserName"]}: '
                        f'{older_key["AccessKeyId"]}'
                        f'-- {reason.value}')
                    action_queue.append({
                        'action': 'WARN',
                        'action_date': older_key_expire_date,
                        'key': older_key,
                        'reason': reason
                    })

    # Return compiled list of remediation options
    return action_queue


def get_actions_for_account(account_session, force_rotate_users):
    config = Config()

    # Initialize values
    list_of_exempted_users = None
    force_rotate_user = None

    iam_client = account_session.client('iam')

    action_queue = []

    # Get all Users in AWS Account
    users = iam_client.list_users()['Users']
    if not users:
        log.info('There are no users in this account.')
    else:
        # Check to see if an IAM Exemption Group exists in CloudFormation
        # and within the Account.
        exemption_group, list_of_exempted_users = validate_exemption_group(
            config.iamExemptionGroup, iam_client, log)

        total_users = len(users)

        log.info(
            f'Starting user loop. There are {total_users}'
            f' users to evaluate in this account.')
        log.info('---------------------------')

        for user in users:
            user_name = user['UserName']

            # handle exemptions
            if user_name in list_of_exempted_users:
                log.info(
                    f'--User [{user_name} is exempt.'
                    f' Skipping validation check.')
                continue
            else:
                log.info(f'--User [{user_name}] is not exempt.')
            # If the force rotate flag exists, check to see if user is tagged.
            if user_name in force_rotate_users:
                force_rotate_user = True
                log.info(
                    f'--Force Rotate user = [{user_name}],'
                    f' which matches current user [{user_name}].'
                    f' Force Rotate User = True.')
            elif force_rotate_users:
                force_rotate_user = False
                log.info(
                    f'--Force Rotate user = [{force_rotate_users[0]}]'
                    f' does NOT match current user [{user_name}].'
                    f' Force Rotate User = False.')
            else:
                force_rotate_user = False
                
            access_key_metadata = iam_client.list_access_keys(
                UserName=user["UserName"])['AccessKeyMetadata']

            user_actions = get_actions_for_keys(
                access_key_metadata, account_session,
                force_rotate_user)

            # Update actions with resource owner email from tag
            if config.resourceOwnerTag is not '':
                user_tag_list = iam_client.list_user_tags(UserName=user_name)["Tags"]
                user_tags = {tag["Key"]: tag["Value"] for tag in user_tag_list}

                if config.resourceOwnerTag in user_tags:
                    resource_owner_email = user_tags.get(config.resourceOwnerTag)
                    log.info(
                        f'--User [{user_name}] is tagged with owner [{resource_owner_email}].'
                    )
                    for action in user_actions:
                        action.update({"resource_email": resource_owner_email})
                else:
                    log.info(
                        f'--User [{user_name}] is missing a [{config.resourceOwnerTag}] tag.'
                    )

            action_queue += user_actions

    # TODO: clean up secrets for IAM users that no longer exist...

    return action_queue
