#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.newsletter_stack import NewsletterStack
from stacks.github_oidc_stack import GithubOidcStack

app = cdk.App()

# Sender/recipient identities are never hardcoded or committed. They are read
# from environment variables that are set locally (one-time manual deploy) or
# injected from GitHub Actions secrets (automated deploys). The real
# recipient mailing list itself lives in SSM Parameter Store, not here — this
# is only the set of addresses SES must verify while the account is in
# sandbox mode.
sender_email = os.environ.get("SENDER_EMAIL", "")
recipient_emails = [
    e.strip() for e in os.environ.get("RECIPIENT_EMAILS", "").split(",") if e.strip()
]
recipients_param_name = os.environ.get(
    "RECIPIENTS_PARAM_NAME", "/newsletter/recipients"
)

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

NewsletterStack(
    app,
    "NewsletterStack",
    sender_email=sender_email,
    recipient_emails=recipient_emails,
    recipients_param_name=recipients_param_name,
    env=env,
)

# TODO: fill in the real GitHub "<OWNER>/<REPO>" before deploying this stack.
# This bootstrap stack is deployed once manually (see README) so that the
# GitHub Actions deploy role exists before any workflow tries to assume it.
github_repo = os.environ.get("GITHUB_REPO", "<OWNER>/<REPO>")

GithubOidcStack(
    app,
    "GithubOidcStack",
    github_repo=github_repo,
    env=env,
)

app.synth()
