import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from flask import has_request_context, request

class RequestFormatter(logging.Formatter):
    """Custom formatter to include request details in log records"""
    
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
            if hasattr(request, 'id'):
                record.request_id = request.id
            else:
                record.request_id = '-'
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            record.request_id = None
            
        return super().format(record)

def configure_logging(app):
    """Configure application logging
    
    Args:
        app: Flask application instance
    """
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_format = '%(asctime)s [%(levelname)s] [%(request_id)s] %(remote_addr)s - %(method)s %(url)s - %(name)s - %(message)s'
    simple_format = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    
    formatter = RequestFormatter(log_format)
    simple_formatter = logging.Formatter(simple_format)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter if app.config.get('ENV') == 'production' else simple_formatter)
    root_logger.addHandler(console_handler)
    
    log_dir = app.config.get('LOG_DIR', 'logs')
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            app.logger.warning(f"Could not create log directory {log_dir}: {e}")
    
    if os.path.exists(log_dir):
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, 'error.log'),
            maxBytes=10485760,
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
    
    app.logger.setLevel(log_level)
    
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    app.logger.info(f"Logging configured with level: {log_level}")
