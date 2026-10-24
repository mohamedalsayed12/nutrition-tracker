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
        return send_from_directory(DIST, path, max_age=365 * 24 * 3600)
    if built and path and "/" not in path and (DIST / path).is_file():
        return send_from_directory(DIST, path, max_age=3600)
    if "." in path.rsplit("/", 1)[-1]:
        abort(404)
    if not built:
        return redirect(url_for("classic_root"))
    response = send_from_directory(DIST, "index.html", max_age=0)
    response.headers["Cache-Control"] = "no-cache"
    return response
