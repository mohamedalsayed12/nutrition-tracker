from routers import spa


def test_root_uses_classic_pages_when_react_is_not_built(client, monkeypatch, tmp_path):
    monkeypatch.setattr(spa, "DIST", tmp_path)
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/classic")


def test_react_routes_get_index_html_and_assets_are_served(client, monkeypatch, tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text('<div id="root"></div>')
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log(1)")
    (tmp_path / "favicon.svg").write_text("<svg/>")
    monkeypatch.setattr(spa, "DIST", tmp_path)

    for path in ("/", "/login", "/add", "/weekly", "/settings", "/onboarding"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert b'id="root"' in response.data
        assert response.headers["Cache-Control"] == "no-cache"
    asset = client.get("/assets/index-abc123.js")
    assert asset.status_code == 200
    assert "max-age=31536000" in asset.headers["Cache-Control"]
    assert client.get("/favicon.svg").status_code == 200


def test_api_and_classic_paths_are_not_swallowed_by_the_react_app(client, monkeypatch, tmp_path):
    (tmp_path / "index.html").write_text('<div id="root"></div>')
    monkeypatch.setattr(spa, "DIST", tmp_path)
    assert client.get("/api/v1/does-not-exist").status_code == 404
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/classic/login").status_code == 200
    assert client.get("/manifest.webmanifest").status_code == 200
    assert client.get("/assets/missing-file.js").status_code == 404
