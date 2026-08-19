"""Renders the newsletter locally so you can see it before deploying.

Doesn't touch AWS at all (no boto3, no SSM, no SES) — just calls the same
content-generation code the Lambda uses and writes the result to an HTML
file you can open in a browser.

Usage (from the lambda/ directory):
    NASA_API_KEY=... TMDB_API_KEY=... python local_preview.py
(PowerShell: $env:NASA_API_KEY = "..."; $env:TMDB_API_KEY = "..."; python local_preview.py)

If the API key env vars aren't set, NASA falls back to the shared DEMO_KEY
and the movies section reports "Content unavailable" (matching real
runtime behavior when a key is missing), so the script still runs.
"""

from pathlib import Path

from content.generator import generate_newsletter_html

OUTPUT_PATH = Path(__file__).parent.parent / "newsletter_preview.html"


def main() -> None:
    html_body = generate_newsletter_html()
    OUTPUT_PATH.write_text(html_body, encoding="utf-8")
    print(f"Newsletter preview written to {OUTPUT_PATH}")
    print("Open that file in a browser to see how the email will look.")


if __name__ == "__main__":
    main()
