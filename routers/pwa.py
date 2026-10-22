"""Files that let phones install the site as an app (a Progressive Web App)."""

from flask import jsonify, render_template, send_from_directory

from config import ROOT

PWA_DIR = ROOT / "pwa"
ICONS = {"icon.svg", "icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"}

MANIFEST = {
    "name": "health4everyone",
    "short_name": "health4everyone",
    "description": "Log meals and track calories, macros and micronutrients.",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#f3f5f1",
    "theme_color": "#1b7a43",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"},
    ],
}


def register_pwa(app):
    app.add_url_rule("/manifest.webmanifest", endpoint="pwa_manifest", view_func=manifest)
    app.add_url_rule("/sw.js", endpoint="pwa_service_worker", view_func=service_worker)
    app.add_url_rule("/offline", endpoint="pwa_offline", view_func=offline)
    app.add_url_rule("/<any(" + ", ".join(f'"{name}"' for name in sorted(ICONS)) + "):name>", endpoint="pwa_icon", view_func=icon)


def manifest():
    response = jsonify(MANIFEST)
    response.mimetype = "application/manifest+json"
    return response


def service_worker():
    response = send_from_directory(PWA_DIR, "sw.js", mimetype="text/javascript", max_age=0)
    response.headers["Cache-Control"] = "no-cache"
    return response


def offline():
    return render_template("offline.html")


def icon(name):
    return send_from_directory(PWA_DIR, name, max_age=7 * 24 * 3600)
