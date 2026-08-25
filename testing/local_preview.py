"""Renders the newsletter locally so you can see it before deploying.

Doesn't touch AWS at all (no boto3, no SSM, no SES) — just calls the same
content-generation code the Lambda uses and writes the result to an HTML
file you can open in a browser.

Lives outside lambda/ deliberately: CDK packages the entire lambda/
directory as the deployment asset (see infra/stacks/newsletter_stack.py),
so dev/test-only tooling like this script shouldn't live in there.

Usage (from the testing/ directory):
    NASA_API_KEY=... TMDB_API_KEY=... python local_preview.py
(PowerShell: $env:NASA_API_KEY = "..."; $env:TMDB_API_KEY = "..."; python local_preview.py)

If the API key env vars aren't set, NASA falls back to the shared DEMO_KEY
and the movies section reports "Content unavailable" (matching real
runtime behavior when a key is missing), so the script still runs.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LAMBDA_DIR = REPO_ROOT / "lambda"
sys.path.insert(0, str(LAMBDA_DIR))

from content.generator import generate_newsletter_html  # noqa: E402

OUTPUT_PATH = REPO_ROOT / "newsletter_preview.html"


def main() -> None:
    html_body = generate_newsletter_html()
    OUTPUT_PATH.write_text(html_body, encoding="utf-8")
    print(f"Newsletter preview written to {OUTPUT_PATH}")
    print("Open that file in a browser to see how the email will look.")


if __name__ == "__main__":
    main()
