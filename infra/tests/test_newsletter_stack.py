import aws_cdk as cdk
from aws_cdk.assertions import Template

from stacks.newsletter_stack import NewsletterStack


def _synth_template() -> Template:
    app = cdk.App()
    stack = NewsletterStack(
        app,
        "TestNewsletterStack",
        sender_email="sender@example.com",
        recipient_emails=["recipient@example.com"],
        recipients_param_name="/newsletter/recipients",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    return Template.from_stack(stack)


def test_lambda_function_created():
    template = _synth_template()
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Handler": "handler.main", "Runtime": "python3.12"},
    )


def test_weekly_schedule_rule_created():
    template = _synth_template()
    template.has_resource_properties(
        "AWS::Events::Rule",
        {"ScheduleExpression": "cron(0 13 ? * MON *)"},
    )


def test_ses_identities_created_for_sender_and_recipients():
    template = _synth_template()
    template.resource_count_is("AWS::SES::EmailIdentity", 2)


def test_log_group_has_bounded_retention():
    template = _synth_template()
    template.has_resource_properties(
        "AWS::Logs::LogGroup", {"RetentionInDays": 30}
    )
