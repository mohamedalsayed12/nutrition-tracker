
def register_routes(app):
    import auth
    from routers import activity_logs, food_logs, foods, goals, health, reports, settings, users

    for router, prefix in (
        (auth.router, "/api/v1/auth"),
        (users.router, "/api/v1/users"),
        (food_logs.router, "/api/v1/food-logs"),
        (activity_logs.router, "/api/v1/activity-logs"),
        (goals.router, "/api/v1/goals"),
        (settings.router, "/api/v1/settings"),
        (foods.router, "/api/v1"),
        (reports.router, "/api/v1"),
        (health.router, ""),
    ):
        app.register_blueprint(router, url_prefix=prefix)
