"""Fetchers for the three external content sources used in the newsletter.

Each function is self-contained: it makes its own HTTP call(s) via the
stdlib (no third-party dependency, so the Lambda package needs no bundling
step) and never raises on failure. Instead it prints
"Error fetching <API Name>" (visible in CloudWatch Logs) and returns None
(or an empty list), so generator.py can render a fallback for just that
section without the whole newsletter failing to send.
"""

import json
import os
import urllib.request

JOKE_API_URL = "https://official-joke-api.appspot.com/random_joke"
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
TMDB_NOW_PLAYING_URL = "https://api.themoviedb.org/3/movie/now_playing"
TMDB_MOVIE_DETAILS_URL = "https://api.themoviedb.org/3/movie/{movie_id}"

REQUEST_TIMEOUT_SECONDS = 10


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read())


def get_joke_of_the_day() -> dict | None:
    """Returns {"setup": ..., "punchline": ...} or None on failure."""
    try:
        data = _get_json(JOKE_API_URL)
        return {"setup": data["setup"], "punchline": data["punchline"]}
    except Exception:
        print("Error fetching Joke of the Day")
        return None


def get_apod() -> dict | None:
    """Returns {"title", "explanation", "url", "media_type"} or None.

    media_type is usually "image" but can be "video" on some days — the
    caller decides how to render that case (APOD has no image to embed).
    """
    api_key = os.environ.get("NASA_API_KEY", "DEMO_KEY")
    try:
        data = _get_json(f"{NASA_APOD_URL}?api_key={api_key}")
        return {
            "title": data["title"],
            "explanation": data["explanation"],
            "url": data["url"],
            "media_type": data.get("media_type", "image"),
        }
    except Exception:
        print("Error fetching NASA Picture of the Day")
        return None


def _get_us_certification(movie_id: int, api_key: str) -> str:
    """Looks up the US content rating (e.g. PG, PG-13, R) for a movie.

    TMDB's now_playing list doesn't include certifications; this requires a
    separate call per movie. Returns "" if TMDB has no US rating on file.
    """
    url = f"{TMDB_MOVIE_DETAILS_URL.format(movie_id=movie_id)}?api_key={api_key}&append_to_response=release_dates"
    data = _get_json(url)
    for entry in data.get("release_dates", {}).get("results", []):
        if entry.get("iso_3166_1") == "US":
            for release in entry.get("release_dates", []):
                certification = release.get("certification", "")
                if certification:
                    return certification
    return ""


def get_now_playing_movies(limit: int = 5) -> list[dict]:
    """Returns up to `limit` currently-in-theaters movies as
    [{"title", "overview", "certification"}, ...], or [] on failure.
    """
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        print("Error fetching Movies in Theaters")
        return []
    try:
        listing = _get_json(f"{TMDB_NOW_PLAYING_URL}?api_key={api_key}&region=US")
    except Exception:
        print("Error fetching Movies in Theaters")
        return []

    movies = []
    for movie in listing.get("results", [])[:limit]:
        # A single movie's certification lookup failing shouldn't drop the
        # whole list — just fall back to "Not Rated" for that one movie.
        try:
            certification = _get_us_certification(movie["id"], api_key)
        except Exception:
            certification = ""
        movies.append(
            {
                "title": movie["title"],
                "overview": movie.get("overview", ""),
                "certification": certification or "Not Rated",
            }
        )
    return movies
