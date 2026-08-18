from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_ses as ses,
    aws_ssm as ssm,
)
from constructs import Construct


class NewsletterStack(Stack):
    """Weekly newsletter: Lambda (content stub + SES send), triggered by
    EventBridge (on AWS) on a weekly schedule, reading its recipient list from an
    SSM SecureString parameter that this stack does not create or populate
    (CloudFormation cannot manage SecureString values — see README)."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        sender_email: str,
        recipient_emails: list[str],
        recipients_param_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if not sender_email:
            raise ValueError(
                "SENDER_EMAIL must be set (env var) before deploying NewsletterStack."
            )

        # --- SES identities -------------------------------------------------
        # Sandbox mode requires both the sender and every recipient to be
        # verified. Each identity still requires a human to click the
        # confirmation link AWS emails to that address; CDK can only create
        # the identity resource and kick off that verification email.
        ses.EmailIdentity(
            self, "SenderIdentity", identity=ses.Identity.email(sender_email)
        )
        # Recipients that are the same address as the sender (e.g. sending
        # the newsletter to yourself) already get an identity above — SES
        # identities are unique per address, so creating a second one for
        # the same address fails with "already exists in stack".
        other_recipients = [r for r in recipient_emails if r != sender_email]
        for i, recipient in enumerate(other_recipients):
            ses.EmailIdentity(
                self, f"RecipientIdentity{i}", identity=ses.Identity.email(recipient)
            )

        # --- SSM parameter reference -----------------------------------------
        # The actual SecureString value is created/updated out-of-band via a
        # one-time `aws ssm put-parameter` call (see README). This stack only
        # references it by name to grant the Lambda read access.
        recipients_param = ssm.StringParameter.from_secure_string_parameter_attributes(
            self,
            "RecipientsParam",
            parameter_name=recipients_param_name,
        )

        # --- Lambda -------------------------------------------------------
        log_group = logs.LogGroup(
            self,
            "NewsletterFunctionLogs",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )

        fn = _lambda.Function(
            self,
            "NewsletterFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.main",
            code=_lambda.Code.from_asset("../lambda"),
            timeout=Duration.seconds(30),
            memory_size=256,
            log_group=log_group,
            environment={
                "RECIPIENTS_PARAM_NAME": recipients_param_name,
                "SENDER_EMAIL": sender_email,
            },
        )

        recipients_param.grant_read(fn)

        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ses:SendEmail", "ses:SendRawEmail"],
                resources=[
                    f"arn:aws:ses:{self.region}:{self.account}:identity/{sender_email}"
                ],
            )
        )

        # --- Weekly schedule ------------------------------------------------
        # Monday 08:00 ET == 13:00 UTC (standard time; off by one hour during
        # ET daylight saving, acceptable for a weekly newsletter).
        rule = events.Rule(
            self,
            "WeeklyScheduleRule",
            schedule=events.Schedule.cron(week_day="MON", hour="13", minute="0"),
        )
        rule.add_target(targets.LambdaFunction(fn))
