import inspect
from typing import Any, Dict

import yaml
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin


def _load_yaml_from_docstring(obj: Any) -> Dict[str, Any]:
    doc = inspect.getdoc(obj) or ""
    if "---" not in doc:
        return {}
    yaml_part = doc.split("---", 1)[1]
    try:
        data = yaml.safe_load(yaml_part) or {}
        return data
    except Exception:
        return {}


def build_spec_from_app(app) -> Dict[str, Any]:
    """Build OpenAPI spec by scanning Flask app routes for YAML docstrings."""
    spec = APISpec(
        title="Hospital Bulk Processing API",
        version="1.0.0",
        openapi_version="3.0.2",
        plugins=[MarshmallowPlugin()],
        info={
            "description": "API for bulk processing of hospital records that integrates with the Hospital Directory API",
            "contact": {"email": "admin@example.com"},
            "license": {"name": "MIT License"},
            "termsOfService": "http://example.com/terms/",
        },
        servers=[{"url": "http://localhost:5001", "description": "Development server"}],
    )

    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        view = app.view_functions.get(rule.endpoint)
        if not view:
            continue
        operations = _load_yaml_from_docstring(view)
        if not operations:
            continue
        allowed_methods = [m.lower() for m in rule.methods if m in {"GET", "POST", "PUT", "PATCH", "DELETE"}]
        ops = {m: operations.get(m, {}) for m in allowed_methods if operations.get(m)}
        if not ops:
            continue
        path = _flask_rule_to_openapi_path(str(rule.rule))
        spec.path(path=path, operations=ops)

    return spec.to_dict()


def _flask_rule_to_openapi_path(rule: str) -> str:
    """Convert Flask/Werkzeug route syntax to OpenAPI curly-brace parameters.

    Examples:
      /api/v1/hospitals/batch/<batch_id>/status -> /api/v1/hospitals/batch/{batch_id}/status
      /items/<int:item_id> -> /items/{item_id}
    """
    out = []
    i = 0
    while i < len(rule):
        if rule[i] == '<':
            j = rule.find('>', i + 1)
            if j == -1:
                out.append(rule[i:])
                break
            segment = rule[i + 1:j]
            if ':' in segment:
                _, name = segment.split(':', 1)
            else:
                name = segment
            out.append('{')
            out.append(name)
            out.append('}')
            i = j + 1
        else:
            out.append(rule[i])
            i += 1
    return ''.join(out)


def assert_route_docs(app, strict: bool = False) -> None:
    """Validate that each non-static route has a YAML docstring. If strict, raise."""
    missing = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue
        view = app.view_functions.get(rule.endpoint)
        if not view:
            continue
        doc = inspect.getdoc(view) or ''
        if '---' not in doc:
            missing.append((rule.rule, sorted(m for m in rule.methods if m in {"GET","POST","PUT","PATCH","DELETE"})))
    if missing:
        msg = 'Endpoints missing OpenAPI YAML docstrings: ' + ', '.join(f"{r} {m}" for r, m in missing)
        if strict:
            raise RuntimeError(msg)
        else:
            app.logger.warning(msg)


