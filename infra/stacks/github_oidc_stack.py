from aws_cdk import Stack, aws_iam as iam
from constructs import Construct


class GithubOidcStack(Stack):
    """One-time bootstrap: lets GitHub Actions deploy this app via OIDC
    federation instead of long-lived AWS access keys. Deployed manually,
    once, before the GitHub Actions workflow can run (the workflow needs
    this role to already exist in order to assume it)."""

    def __init__(
        self, scope: Construct, construct_id: str, *, github_repo: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if github_repo == "<OWNER>/<REPO>":
            raise ValueError(
                "Set the GITHUB_REPO env var to '<owner>/<repo>' before "
                "deploying GithubOidcStack (see README)."
            )

        provider = iam.OpenIdConnectProvider(
            self,
            "GithubOidcProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        # Scoped to this exact repo's main branch only, so no other repo or
        # branch/PR workflow can assume this role even though it lives in a
        # public repo.
        deploy_role = iam.Role(
            self,
            "GithubActionsDeployRole",
            assumed_by=iam.WebIdentityPrincipal(
                provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{github_repo}:ref:refs/heads/main"
                    },
                },
            ),
            description="Assumed by GitHub Actions to deploy the newsletter CDK app.",
        )

        # CDK deploys need to manage CloudFormation stacks and the resources
        # within them (Lambda, IAM, EventBridge, SES, SSM param references,
        # plus the CDK bootstrap staging bucket/roles). Scoping this further
        # requires permission boundaries out of scope for this initial
        # build; documented as an accepted tradeoff, mitigated by the OIDC
        # trust policy above restricting *who* can assume this role.
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["cloudformation:*"],
                resources=["*"],
            )
        )
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:*"],
                resources=["arn:aws:s3:::cdk-*"],
            )
        )
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[f"arn:aws:iam::{self.account}:role/cdk-*"],
            )
        )
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                resources=[f"arn:aws:iam::{self.account}:role/cdk-*"],
            )
        )
