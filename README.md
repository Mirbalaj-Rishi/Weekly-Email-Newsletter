# Weekly Email Newsletter

A weekly newsletter sent via Amazon SES, built and deployed entirely with AWS CDK (Python). A Lambda function generates the newsletter body and sends it; an EventBridge rule triggers it every Monday at 8am ET; the recipient list lives in SSM Parameter Store, never in this repo.

This repository is currently private, but is designed to be safe to make public later. **No real email addresses, account IDs, or credentials are ever committed.** Config values are passed in via environment variables (local one-time steps) or GitHub Actions secrets (automated deploys).

## Architecture

- **Lambda** (`lambda/handler.py`) — reads the recipient list from SSM, builds the email via `lambda/content/generator.py` (currently a placeholder; real content-source APIs come in a later phase), sends via SES.
- **EventBridge Rule** — cron trigger, Monday 13:00 UTC (8am ET).
- **SSM Parameter Store** (`SecureString`, Standard tier — free) — holds the actual recipient email list.
- **SES** — sandbox mode (see "SES sandbox mode" below): sender and every recipient must be individually verified via a confirmation-link email.
- **GitHub Actions** — deploys the `NewsletterStack` automatically on push to `main`, authenticated via GitHub OIDC (no long-lived AWS keys).

Ongoing deploys require **zero manual AWS console/terminal steps** — you just push to `main`. The exceptions below are one-time setup steps, not part of the regular workflow.

## One-time manual setup

These steps exist because of hard AWS/CloudFormation limitations (documented inline), not because of a design shortcut.

### 1. Create the virtual environment and bootstrap your AWS account for CDK

This project uses a Python virtual environment (`.venv/`, gitignored) so dependencies stay isolated from your system Python.

```
python -m venv .venv

# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (Git Bash)
source .venv/Scripts/activate

pip install -r infra/requirements-dev.txt   # includes pytest for local testing
cd infra
cdk bootstrap aws://<ACCOUNT_ID>/<REGION>
```

Re-activate the virtual environment (the `source .venv/...` / `Activate.ps1` line) in every new terminal session before running `cdk` or `pytest`.

### 2. Deploy the GitHub OIDC role (once, before any GitHub Actions run)

CloudFormation can't be deployed by a GitHub Actions workflow that doesn't have permission to assume a role yet — so this bootstrap stack must be deployed manually first.

Bash / Git Bash:
```
export GITHUB_REPO=<owner>/<repo>        # your actual GitHub repo, once created
export CDK_DEFAULT_ACCOUNT=<ACCOUNT_ID>
export CDK_DEFAULT_REGION=<REGION_NAME>
cdk deploy GithubOidcStack
```

PowerShell:
```powershell
$env:GITHUB_REPO = "<owner>/<repo>"      # your actual GitHub repo, once created
$env:CDK_DEFAULT_ACCOUNT = "<ACCOUNT_ID>"
$env:CDK_DEFAULT_REGION = "<REGION_NAME>"
cdk deploy GithubOidcStack
```

Note the deployed role's ARN (CDK prints it as a stack output) — you'll add it as a GitHub Actions secret in step 5.

### 3. Set the recipient list in SSM (SecureString)

CloudFormation's `AWS::SSM::Parameter` resource does **not** support `SecureString` — this is a hard AWS limitation, so the CDK stack only *references* this parameter; it can't create or populate it. Set it once, manually:

Bash / Git Bash:
```
aws ssm put-parameter \
  --name /newsletter/recipients \
  --type SecureString \
  --value "you@example.com,friend@example.com" \
  --overwrite
```

PowerShell (no `\` line continuation — use backtick, or keep it on one line):
```powershell
aws ssm put-parameter --name /newsletter/recipients --type SecureString --value "you@example.com,friend@example.com" --overwrite
```

Update this value the same way any time the list changes — it's the one piece of ongoing "terminal configuration," and it's unavoidable because the data is private and this repo is public.

### 4. Deploy the newsletter stack and verify SES identities

Bash / Git Bash:
```
export SENDER_EMAIL=you@example.com
export RECIPIENT_EMAILS=you@example.com,friend@example.com   # sandbox mode only
cdk deploy NewsletterStack
```

PowerShell:
```powershell
$env:SENDER_EMAIL = "you@example.com"
$env:RECIPIENT_EMAILS = "you@example.com,friend@example.com"   # sandbox mode only
cdk deploy NewsletterStack
```

SES will email a confirmation link to the sender address and (while in sandbox mode) every recipient address. Each person must click their link before they can send/receive. This can't be automated — it's AWS's proof of address ownership.

**SES sandbox mode**: new AWS accounts start in SES's sandbox, which caps sending to ~200 emails/24h and requires every recipient (not just the sender) to be verified this way. That's fine for a small personal list. Later, requesting AWS "production access" (a manual, AWS-reviewed support request — not something CDK can do) removes the per-recipient verification requirement and the volume cap; pairs well with switching to a verified domain identity instead of individual email identities.

### 5. Add GitHub Actions secrets

In the GitHub repo's Settings → Secrets and variables → Actions, add:

| Secret | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | ARN output by `GithubOidcStack` in step 2 |
| `AWS_ACCOUNT_ID` | your AWS account ID |
| `AWS_REGION` | e.g. `us-east-1` |
| `SENDER_EMAIL` | the verified sender address |
| `RECIPIENT_EMAILS` | comma-separated list (sandbox mode only) |

After this, every push to `main` automatically runs `cdk synth` + `cdk deploy` for `NewsletterStack` via `.github/workflows/deploy.yml` — no further terminal steps.

## Local development

```
source .venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux, .venv\Scripts\Activate.ps1 on PowerShell
cd infra
pytest tests/
cdk synth
```

## Cost

Designed to cost money only when the newsletter is actually built and sent:

- Lambda: 1 invocation/week — free tier.
- EventBridge: free at this volume.
- SES: $0.10 per 1,000 emails.
- SSM Standard parameter: free.
- CloudWatch Logs: capped at 30-day retention.

No always-on compute (no EC2/Fargate/RDS).

## Future work

- Replace the placeholder in `lambda/content/generator.py` with real content pulled from external APIs.
- Move to a verified domain SES identity + request SES production access to leave sandbox mode.
