"""Serve the React app (frontend/) from the same Heroku app as the API.

The deploy job runs `npm run build`, which writes frontend/dist. Any path that is
not an API route, an install file (routers/pwa.py) or an old /classic page gets
the React app's index.html, and React Router shows the right screen.
"""

from flask import abort, redirect, send_from_directory, url_for

from config import ROOT

DIST = ROOT / "frontend" / "dist"
RESERVED = ("api/", "classic")


def register_spa(app):
    app.add_url_rule("/", endpoint="spa_index", view_func=index, defaults={"path": ""})
    app.add_url_rule("/<path:path>", endpoint="spa_index", view_func=index)


def index(path):
    if path.startswith(RESERVED):
        abort(404)
    built = (DIST / "index.html").is_file()
    if built and path.startswith("assets/") and (DIST / path).is_file():
        # Built files have a content hash in their names, so they can be cached for a year.
        return send_from_directory(DIST, path, max_age=365 * 24 * 3600)
    if built and path and "/" not in path and (DIST / path).is_file():
        return send_from_directory(DIST, path, max_age=3600)  # favicon.svg, icons.svg
    if "." in path.rsplit("/", 1)[-1]:
        abort(404)  # a missing file, not a screen of the app
    if not built:
        # No React build (local development or tests): use the classic pages.
        return redirect(url_for("classic_root"))
    response = send_from_directory(DIST, "index.html", max_age=0)
    response.headers["Cache-Control"] = "no-cache"
    return response
