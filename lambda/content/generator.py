import html
from datetime import date

from content.apis import get_apod, get_joke_of_the_day, get_now_playing_movies
from content.template import (
    COLOR_ACCENT,
    COLOR_ACCENT_BG,
    COLOR_BODY_TEXT,
    COLOR_HEADING,
    COLOR_MUTED_TEXT,
    FONT_FAMILY,
    INNER_WIDTH,
    render_card_row,
    render_email_shell,
    truncate,
)

# TMDB's API Terms of Use require this exact attribution wherever their data
# is displayed: https://www.themoviedb.org/api-terms-of-use
TMDB_ATTRIBUTION = (
    "This product uses the TMDB API but is not endorsed or certified by TMDB."
)

_SECTION_HEADING_STYLE = (
    f"margin:0 0 12px; font-size:18px; color:{COLOR_HEADING}; font-family:{FONT_FAMILY};"
)
_UNAVAILABLE_STYLE = (
    f"margin:0; font-size:14px; font-style:italic; color:{COLOR_MUTED_TEXT}; font-family:{FONT_FAMILY};"
)


def _joke_section_html() -> str:
    joke = get_joke_of_the_day()
    if joke is None:
        return render_card_row(
            f'<h2 style="{_SECTION_HEADING_STYLE}">😂 Joke of the Day</h2>'
            f'<p style="{_UNAVAILABLE_STYLE}">Content unavailable this week.</p>'
        )
    setup = html.escape(joke["setup"])
    punchline = html.escape(joke["punchline"])
    return render_card_row(f"""\
        <h2 style="{_SECTION_HEADING_STYLE}">😂 Joke of the Day</h2>
        <p style="margin:0 0 12px; font-size:15px; line-height:1.5; color:{COLOR_BODY_TEXT}; font-family:{FONT_FAMILY};">{setup}</p>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="background-color:{COLOR_ACCENT_BG}; border-left:4px solid {COLOR_ACCENT}; border-radius:4px; padding:12px 16px;">
              <p style="margin:0; font-size:15px; font-style:italic; color:{COLOR_HEADING}; font-family:{FONT_FAMILY};">{punchline}</p>
            </td>
          </tr>
        </table>""")


def _apod_section_html() -> str:
    apod = get_apod()
    if apod is None:
        return render_card_row(
            f'<h2 style="{_SECTION_HEADING_STYLE}">🔭 NASA Picture of the Day</h2>'
            f'<p style="{_UNAVAILABLE_STYLE}">Content unavailable this week.</p>'
        )
    title = html.escape(apod["title"])
    explanation = html.escape(apod["explanation"])
    if apod["media_type"] == "image":
        media_html = (
            f'<img src="{html.escape(apod["url"])}" alt="{title}" width="{INNER_WIDTH}" '
            f'style="width:100%; max-width:{INNER_WIDTH}px; height:auto; display:block; '
            f'border-radius:6px; margin:0 0 12px;">'
        )
    else:
        # Some days APOD publishes a video instead of an image; a styled
        # button-style link reads better than a bare embed attempt.
        media_html = f"""\
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 12px;">
          <tr>
            <td style="background-color:{COLOR_ACCENT}; border-radius:4px;">
              <a href="{html.escape(apod["url"])}" style="display:inline-block; padding:10px 18px; font-size:14px; font-weight:bold; color:#ffffff; font-family:{FONT_FAMILY}; text-decoration:none;">View Today's Video</a>
            </td>
          </tr>
        </table>"""
    return render_card_row(f"""\
        <h2 style="{_SECTION_HEADING_STYLE}">🔭 NASA Picture of the Day</h2>
        <h3 style="margin:0 0 12px; font-size:15px; font-weight:bold; color:{COLOR_HEADING}; font-family:{FONT_FAMILY};">{title}</h3>
        {media_html}
        <p style="margin:0; font-size:14px; line-height:1.6; color:{COLOR_BODY_TEXT}; font-family:{FONT_FAMILY};">{explanation}</p>""")


def _movie_card_html(movie: dict) -> str:
    title = html.escape(movie["title"])
    certification = html.escape(movie["certification"])
    overview = html.escape(truncate(movie["overview"], 200))
    return f"""\
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 12px;">
          <tr>
            <td style="border:1px solid {COLOR_ACCENT_BG}; border-radius:6px; padding:14px 16px;">
              <p style="margin:0 0 6px;">
                <span style="font-size:15px; font-weight:bold; color:{COLOR_HEADING}; font-family:{FONT_FAMILY};">{title}</span>
                <span style="display:inline-block; margin-left:6px; padding:2px 8px; border-radius:10px; background-color:{COLOR_ACCENT_BG}; color:{COLOR_ACCENT}; font-size:11px; font-weight:bold; font-family:{FONT_FAMILY};">{certification}</span>
              </p>
              <p style="margin:0; font-size:13px; line-height:1.5; color:{COLOR_MUTED_TEXT}; font-family:{FONT_FAMILY};">{overview}</p>
            </td>
          </tr>
        </table>"""


def _movies_section_html() -> str:
    movies = get_now_playing_movies(limit=5)
    if not movies:
        return render_card_row(
            f'<h2 style="{_SECTION_HEADING_STYLE}">🎬 Movies in Theaters</h2>'
            f'<p style="{_UNAVAILABLE_STYLE}">Content unavailable this week.</p>'
        )
    cards = "".join(_movie_card_html(m) for m in movies)
    return render_card_row(
        f'<h2 style="{_SECTION_HEADING_STYLE}">🎬 Movies in Theaters</h2>{cards}'
    )


def generate_newsletter_html() -> str:
    """Builds the newsletter body from three content sources: a daily joke,
    NASA's picture of the day, and movies currently in theaters. Each
    section is fetched and rendered independently, so one source failing
    doesn't prevent the newsletter from sending with the others intact."""
    today = date.today().strftime("%B %d, %Y")
    sections_html = (
        _joke_section_html() + _movies_section_html() + _apod_section_html()
    )
    return render_email_shell(sections_html, today, TMDB_ATTRIBUTION)


def generate_newsletter_subject() -> str:
    today = date.today().strftime("%B %d, %Y")
    return f"Weekly Newsletter — {today}"
