

"""Notifier.

Provies core logic for the Notifier Lambda Function.
"""

import logging
import boto3

from botocore.exceptions import ClientError
from config import Config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Notifier:
    def __init__(self, sender_email: str, recipient_email: str,
                 template_s3_bucket: str, template_s3_prefix: str,
                 email_template: str, subject: str) -> None:
        self.sender_email = sender_email
        self.recipient_email = recipient_email
        self.template_s3_bucket = template_s3_bucket
        self.template_s3_prefix = template_s3_prefix
        self.email_template = email_template
        self.subject = subject

    @staticmethod
    def __parse_arn(arn):
        # http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
        elements = arn.split(':', 5)
        result = {
            'arn': elements[0],
            'partition': elements[1],
            'service': elements[2],
            'region': elements[3],
            'account': elements[4],
            'resource': elements[5],
            'resource_type': None
        }
        if '/' in result['resource']:
            result['resource_type'], result['resource'] = \
                result['resource'].split('/', 1)  # NOQA
        elif ':' in result['resource']:
            result['resource_type'], result['resource'] = \
                result['resource'].split(':', 1)  # NOQA
        return result

    def __get_template(self, template_name):
        log.info(f'Getting template {template_name} from S3')
        s3 = boto3.client('s3')

        try:
            obj = s3.get_object(
                Bucket=self.template_s3_bucket,
                Key=f'{self.template_s3_prefix}/Template/{template_name}'
            )

            data = obj['Body'].read()
            template = data.decode('utf-8')
            log.info(f'Successfully retrieved content for {template_name}')
            return template
        except ClientError as err:
            log.error(
                f'Error while getting file contents for {template_name}'
                f' - {err}'
            )

    def __render_email_body(self, template_values: dict):
        subject = self.subject
        # get the appropriate S3 Key for the template
        template_s3_key = self.email_template
        if not template_s3_key:
            log.error(f'Unable to get template for {subject}')
            raise ValueError(f'Unable to get template for {subject}')
        else:
            # stream the template contents from S3
            email = self.__get_template(template_s3_key)

            log.info('Rendering email contents')
            for k, v in template_values.items():
                placeholder = '{{' + f'{k}' + '}}'
                if isinstance(v, list):
                    value = self.__format_html_list(v)
                else:
                    value = str(v)
                email = email.replace(placeholder, value)

            log.info(f'Rendered Email: {email}')

            return email

    @staticmethod
    def __format_html_list(value):
        value_formatted = ''
        for line in value:
            value_formatted += f'&bull; {str(line)}<br>'
        return value_formatted

    def send_email(self, template_values):
        if Config.runLambdaInVPC:
            self.send_smtp_email(template_values)
        else:
            self.send_ses_email(template_values)

    def send_ses_email(self, template_values):
        my_session = boto3.session.Session()
        my_region = my_session.region_name
        ses = my_session.client('ses', region_name=my_region)

        email_body = self.__render_email_body(template_values)

        try:
            log.info(f'Sending email to {self.recipient_email}')
            resp = ses.send_email(
                Source=self.sender_email,
                Destination={
                    'ToAddresses': [
                        self.recipient_email,
                    ]
                },
                Message={
                    'Subject': {
                        'Data': self.subject
                    },
                    'Body': {
                        'Text': {
                            'Data': email_body
                        },
                        'Html': {
                            'Data': email_body
                        }
                    }
                }
            )
            log.info('Email sent successfully - Exiting Gracefully')
            return resp
        except ClientError as err:
            log.error(
                f'Encountered error while attempting to send email - {err}'
            )
            print(err)
            raise err

    def send_smtp_email(self, template_values):
        my_session = boto3.session.Session()
        my_region = my_session.region_name
        port = 465
        email_body = self.__render_email_body(template_values)
        message = MIMEMultipart()
        message['Subject'] = self.subject
        message['From'] = self.sender_email
        message['To'] = self.recipient_email
        message.attach(MIMEText(email_body, "html"))
        msgbody = message.as_string()

        ssm = my_session.client('ssm', region_name=my_region, endpoint_url="https://ssm." + my_region + ".amazonaws.com")
        user = ssm.get_parameter(Name=Config.smtp_user_param, WithDecryption=False)
        password = ssm.get_parameter(Name=Config.smtp_password_param, WithDecryption=True)

        try:
            log.info(f'Sending email to {self.recipient_email}')
            server = smtplib.SMTP_SSL("email-smtp." + my_region + ".amazonaws.com", port)

            server.login(user.get("Parameter").get("Value"), password.get("Parameter").get("Value"))
            server.sendmail(self.sender_email, self.recipient_email, msgbody)
            log.info('Email sent successfully - Exiting Gracefully')
        except ClientError as err:
            log.error(
                f'Encountered error while attempting to send email - {err}'
            )
            print(err)
            raise err