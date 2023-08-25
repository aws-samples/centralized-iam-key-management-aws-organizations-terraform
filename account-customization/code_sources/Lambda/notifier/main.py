

"""Main.py.

This is the main entry point for this application.
"""

import json
import logging
from datetime import datetime

from config import Config
from notifier import Notifier

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def lambda_handler(event: dict = None, context=None):
    """Lambda Handler."""
    config = Config()
    log.info(f'Event: {json.dumps(event, indent=2)}')

    email = event.get('email')
    email_template = event.get('email_template')
    subject = event.get('subject')
    template_values = event.get('template_values')

    # add invocation parameters
    template_values['sender_email'] = config.admin_email

    notifier = Notifier(config.admin_email, email, config.s3_bucket_name,
                        config.s3_bucket_prefix, email_template, subject)
    notifier.send_email(template_values)


def parse_template_values(event, config):
    account_id = event.get('account')
    action_queue = event.get('action_queue')

    # Timestamp for function runtime/invoked date
    now = datetime.now()

    timestamp = now.strftime("%d/%m/%Y %H:%M:%S")
    action_queue = action_queue.replace("}, {", "} <br> {")
    template_values = {
        'account_id': account_id,
        'timestamp': timestamp,
        'actions': action_queue
    }
    return template_values
