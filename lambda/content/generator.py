from datetime import date


def generate_newsletter_html() -> str:
    """Builds the newsletter body. Currently a placeholder — real content
    sourced from external APIs will replace this in a later phase. Callers
    should only depend on this function's signature (no args, returns an
    HTML string), not its internals."""
    today = date.today().strftime("%B %d, %Y")
    return f"""\
<html>
  <body>
    <h1>Weekly Newsletter — {today}</h1>
    <p>This is a placeholder issue. Real content sources will be added here.</p>
  </body>
</html>
"""


def generate_newsletter_subject() -> str:
    today = date.today().strftime("%B %d, %Y")
    return f"Weekly Newsletter — {today}"
