import html
from datetime import date

from content.apis import get_apod, get_joke_of_the_day, get_now_playing_movies

# TMDB's API Terms of Use require this exact attribution wherever their data
# is displayed: https://www.themoviedb.org/api-terms-of-use
TMDB_ATTRIBUTION = (
    "This product uses the TMDB API but is not endorsed or certified by TMDB."
)


def _joke_section_html() -> str:
    joke = get_joke_of_the_day()
    if joke is None:
        return "<h2>Joke of the Day</h2><p>Content unavailable this week.</p>"
    setup = html.escape(joke["setup"])
    punchline = html.escape(joke["punchline"])
    return f"<h2>Joke of the Day</h2><p>{setup}</p><p><em>{punchline}</em></p>"


def _apod_section_html() -> str:
    apod = get_apod()
    if apod is None:
        return "<h2>NASA Picture of the Day</h2><p>Content unavailable this week.</p>"
    title = html.escape(apod["title"])
    explanation = html.escape(apod["explanation"])
    if apod["media_type"] == "image":
        media_html = f'<img src="{html.escape(apod["url"])}" alt="{title}" style="max-width: 100%;">'
    else:
        # Some days APOD publishes a video instead of an image; link out
        # rather than trying to embed it.
        media_html = f'<p><a href="{html.escape(apod["url"])}">View today\'s video</a></p>'
    return f"<h2>NASA Picture of the Day</h2><h3>{title}</h3>{media_html}<p>{explanation}</p>"


def _movies_section_html() -> str:
    movies = get_now_playing_movies(limit=5)
    if not movies:
        return "<h2>Movies in Theaters</h2><p>Content unavailable this week.</p>"
    items = "".join(
        f"<li><strong>{html.escape(m['title'])}</strong> "
        f"({html.escape(m['certification'])}) — {html.escape(m['overview'])}</li>"
        for m in movies
    )
    return f"<h2>Movies in Theaters</h2><ul>{items}</ul>"


def generate_newsletter_html() -> str:
    """Builds the newsletter body from three content sources: a daily joke,
    NASA's picture of the day, and movies currently in theaters. Each
    section is fetched and rendered independently, so one source failing
    doesn't prevent the newsletter from sending with the others intact."""
    today = date.today().strftime("%B %d, %Y")
    return f"""\
<html>
  <body>
    <h1>Weekly Newsletter — {today}</h1>
    {_joke_section_html()}
    {_apod_section_html()}
    {_movies_section_html()}
    <hr>
    <p style="font-size: 0.8em; color: #687;">{TMDB_ATTRIBUTION}</p>
  </body>
</html>
"""


def generate_newsletter_subject() -> str:
    today = date.today().strftime("%B %d, %Y")
    return f"Weekly Newsletter — {today}"
