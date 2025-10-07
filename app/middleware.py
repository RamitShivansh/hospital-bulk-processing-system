import uuid
from flask import request, current_app


def register_middlewares(app):
    """Register request/response and error handlers on the Flask app."""

    def assign_request_id():
        request.id = str(uuid.uuid4())
        current_app.logger.debug(f"Request received: {request.method} {request.path}")

    def log_response(response):
        current_app.logger.info(f"Request completed with status: {response.status_code}")
        return response

    def handle_exception(e):
        current_app.logger.exception(f"Unhandled exception: {str(e)}")
        return {"error": "Internal server error"}, 500

    app.before_request(assign_request_id)
    app.after_request(log_response)
    app.register_error_handler(Exception, handle_exception)


