from flask_swagger_ui import get_swaggerui_blueprint
from flask import jsonify, request
from .utils.openapi_auto import build_spec_from_app

def get_apispec(app):
    return build_spec_from_app(app)

swagger_ui_blueprint = get_swaggerui_blueprint(
    "/docs",
    "/api/v1/swagger.json",
    config={
        'app_name': "Hospital Bulk Processing API"
    },
)

def configure_swagger(app):
    """Configure Swagger UI for Flask application"""
    app.register_blueprint(swagger_ui_blueprint)
    
    @app.route('/api/v1/swagger.json')
    def swagger_json():
        spec = get_apispec(app)
        server_url = request.url_root.rstrip('/')
        spec['servers'] = [{"url": server_url, "description": "Current server"}]
        return jsonify(spec)