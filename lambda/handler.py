import os

import boto3

from content.generator import generate_newsletter_html, generate_newsletter_subject

ssm = boto3.client("ssm")
ses = boto3.client("ses")


def _get_recipients() -> list[str]:
    param_name = os.environ["RECIPIENTS_PARAM_NAME"]
    response = ssm.get_parameter(Name=param_name, WithDecryption=True)
    raw = response["Parameter"]["Value"]
    return [addr.strip() for addr in raw.split(",") if addr.strip()]


def main(event, context):
    sender = os.environ["SENDER_EMAIL"]
    recipients = _get_recipients()

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
