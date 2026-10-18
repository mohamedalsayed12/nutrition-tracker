import re


def api_specification(app):
    paths = {}
    public = {"users.create_user", "auth.login", "health.health", "health.ready",
              "foods.foods", "foods.measures", "foods.exercises"}
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/v1"):
            continue
        view = app.view_functions[rule.endpoint]
        path = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", rule.rule)
        parameters = [dict(name=name, **{"in": "path"}, required=True,
                           schema={"type": "integer" if "int:" + name in rule.rule else "string"})
                      for name in rule.arguments]
        if rule.endpoint.endswith(("list_food_logs", "list_activity_logs")):
            parameters += [dict(name=name, **{"in": "query"}, schema={"type": "integer", "minimum": 1})
                           for name in ("page", "per_page")]
        if rule.endpoint.startswith("foods.") and not rule.arguments:
            parameters.append(dict(name="q", **{"in": "query"}, schema={"type": "string"}))
        if rule.endpoint in {"reports.daily", "reports.weekly"}:
            for name in ("timezone", "date" if rule.endpoint == "reports.daily" else "week_start"):
                parameters.append(dict(name=name, **{"in": "query"}, schema={"type": "string"}))
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            operation = dict(operationId=rule.endpoint.replace(".", "_"),
                             parameters=parameters, security=[] if rule.endpoint in public else [{"bearerAuth": []}],
                             responses={"200": {"description": "Success"}, "400": {"description": "Invalid request"},
                                        "401": {"description": "Authentication required"}, "404": {"description": "Not found"}})
            schema = getattr(view, "request_schema", None)
            if schema:
                operation["requestBody"] = dict(required=True, content={"application/json": {"schema": schema.model_json_schema()}})
            if method == "POST":
                operation["responses"]["201"] = {"description": "Created"}
            if method == "DELETE":
                operation["responses"]["204"] = {"description": "Deleted"}
            paths.setdefault(path, {})[method.lower()] = operation
    return dict(openapi="3.1.0", info={"title": "Nutrition Tracker API", "version": "1.0.0"},
                paths=paths, components={"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}}})
