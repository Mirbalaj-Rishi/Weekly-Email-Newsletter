"""Shared visual building blocks for the newsletter's HTML email.

Email clients (Outlook desktop especially, which renders using Microsoft
Word's engine) don't support external stylesheets, <script> tags, CSS
classes, or modern layout like flexbox/grid. So instead of a CSS framework
like Tailwind, this uses the industry-standard "fluid-hybrid" email coding
pattern: a table-based layout with inline styles for universal support,
plus a <style> block with @media queries as progressive enhancement for
clients that do support them (Gmail, Apple Mail, mobile mail apps, etc).
"""

import html

FONT_FAMILY = "Arial, Helvetica, sans-serif"

COLOR_HEADER_BG = "#1e293b"
COLOR_HEADER_TEXT = "#ffffff"
COLOR_HEADER_SUBTEXT = "#94a3b8"
COLOR_PAGE_BG = "#f4f4f7"
COLOR_CARD_BG = "#ffffff"
COLOR_HEADING = "#1e293b"
COLOR_BODY_TEXT = "#334155"
COLOR_MUTED_TEXT = "#64748b"
COLOR_ACCENT = "#2563eb"
COLOR_ACCENT_BG = "#eff6ff"
COLOR_BORDER = "#e2e8f0"

CONTENT_WIDTH = 600
# Inner width available inside a content row after its own padding
INNER_WIDTH = CONTENT_WIDTH - 2 * 24


def truncate(text: str, max_len: int = 200) -> str:
    """Shortens text to max_len characters (on a word boundary where
    possible), appending an ellipsis, so cards stay scannable."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0]
    return f"{cut}…"


def render_card_row(inner_html: str) -> str:
    """Wraps a section's content in a table row with consistent padding
    and a bottom divider, so each section in generator.py doesn't repeat
    this boilerplate."""
    return f"""\
      <tr>
        <td class="email-padding" style="padding: 24px; border-bottom: 1px solid {COLOR_BORDER};">
          {inner_html}
        </td>
      </tr>"""


def render_email_shell(sections_html: str, today: str, tmdb_attribution: str) -> str:
    """The outer HTML document: head with the email-safe CSS reset and
    responsive breakpoint, a centered fixed/fluid container table, a
    styled header, the section rows, and a footer with the TMDB
    attribution required by their API Terms of Use."""
    return f"""\
<!doctype html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>Weekly Newsletter</title>
  <!--[if mso]>
  <style type="text/css">
    table {{ border-collapse: collapse; }}
  </style>
  <![endif]-->
  <style>
    body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    img {{ -ms-interpolation-mode: bicubic; border: 0; height: auto; line-height: 100%; outline: none; text-decoration: none; }}
    body {{ margin: 0; padding: 0; width: 100% !important; background-color: {COLOR_PAGE_BG}; }}
    @media only screen and (max-width: 600px) {{
      .email-container {{ width: 100% !important; }}
      .email-padding {{ padding-left: 16px !important; padding-right: 16px !important; }}
    }}
  </style>
</head>
<body style="margin:0; padding:0; background-color:{COLOR_PAGE_BG};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{COLOR_PAGE_BG};">
    <tr>
      <td align="center" style="padding: 24px 12px;">
        <table role="presentation" class="email-container" width="{CONTENT_WIDTH}" cellpadding="0" cellspacing="0" style="width:{CONTENT_WIDTH}px; max-width:{CONTENT_WIDTH}px; background-color:{COLOR_CARD_BG}; border-radius:8px; overflow:hidden; font-family:{FONT_FAMILY};">
          <tr>
            <td class="email-padding" style="background-color:{COLOR_HEADER_BG}; padding:32px 24px; text-align:center;">
              <h1 style="margin:0; color:{COLOR_HEADER_TEXT}; font-size:24px; font-family:{FONT_FAMILY};">Weekly Newsletter</h1>
              <p style="margin:8px 0 0; color:{COLOR_HEADER_SUBTEXT}; font-size:14px; font-family:{FONT_FAMILY};">{html.escape(today)}</p>
            </td>
          </tr>
          {sections_html}
          <tr>
            <td class="email-padding" style="padding:20px 24px; text-align:center; background-color:{COLOR_PAGE_BG};">
              <p style="margin:0; font-size:12px; color:{COLOR_MUTED_TEXT}; font-family:{FONT_FAMILY};">{html.escape(tmdb_attribution)}</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
