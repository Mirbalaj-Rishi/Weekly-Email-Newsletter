import os

import boto3

from content.generator import generate_newsletter_html, generate_newsletter_subject

# Created once at module scope (not inside main()) so Lambda can reuse these
# clients across invocations on a warm execution environment, rather than
# re-establishing them on every run.
ssm = boto3.client("ssm")
ses = boto3.client("ses")


def _get_recipients() -> list[str]:
    """Fetch and decrypt the recipient list from SSM Parameter Store.

    The parameter is a SecureString maintained outside of CDK (see the
    README) since CloudFormation cannot manage SecureString values. Its
    value is a single comma-separated string of email addresses.
    """
    param_name = os.environ["RECIPIENTS_PARAM_NAME"]
    response = ssm.get_parameter(Name=param_name, WithDecryption=True)
    raw = response["Parameter"]["Value"]
    return [addr.strip() for addr in raw.split(",") if addr.strip()]


def main(event, context):
    """Lambda entry point: build this week's newsletter and send it via SES.

    Invoked on the weekly EventBridge schedule (see newsletter_stack.py),
    with no meaningful event payload — event/context are accepted only
    because Lambda's runtime contract requires them.
    """
    sender = os.environ["SENDER_EMAIL"]
    recipients = _get_recipients()

    # Fail loudly rather than silently sending to nobody — an empty
    # recipient list almost always means the SSM parameter was never set
    # (or was cleared), which is worth surfacing as an error in CloudWatch
    # Logs rather than a quiet no-op.
    if not recipients:
        raise ValueError("No recipients found in SSM parameter; nothing to send.")

    html_body = generate_newsletter_html()
    subject = generate_newsletter_subject()

    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": recipients},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {"Html": {"Data": html_body, "Charset": "UTF-8"}},
        },
    )

    return {"status": "sent", "recipient_count": len(recipients)}
