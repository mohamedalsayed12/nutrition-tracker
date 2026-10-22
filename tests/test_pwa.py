def test_manifest_describes_an_installable_app(client):
    response = client.get("/manifest.webmanifest")
    assert response.status_code == 200
    assert response.mimetype == "application/manifest+json"
    manifest = response.get_json()
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "/homepage"
    sizes = {icon["sizes"] for icon in manifest["icons"]}
    assert {"192x192", "512x512"} <= sizes


def test_icons_and_service_worker_are_served(client):
    for path in ("/icon-192.png", "/icon-512.png", "/icon-maskable-512.png", "/apple-touch-icon.png"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.mimetype == "image/png"
    worker = client.get("/sw.js")
    assert worker.status_code == 200
    assert "javascript" in worker.mimetype
    assert worker.headers["Cache-Control"] == "no-cache"
    assert client.get("/offline").status_code == 200


def test_pages_have_phone_viewport_and_manifest_link(client):
    for path in ("/login", "/register"):
        html = client.get(path).get_data(as_text=True)
        assert 'name="viewport"' in html, path
        assert 'rel="manifest"' in html, path
        assert "apple-touch-icon" in html, path
