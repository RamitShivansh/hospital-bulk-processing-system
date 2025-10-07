import logging
from flask import Flask, request
import uuid
from .config import Config
from werkzeug.middleware.proxy_fix import ProxyFix
from .swagger import configure_swagger
from .utils.logging_config import configure_logging
from .middleware import register_middlewares
from .services.validation_service import HospitalCsvValidator
from .utils.csv_parser import CsvHospitalParser
from .services.hospital_api_client import HospitalApiClient
from .services.batch_processor import BatchProcessor
from .repository.hospital_batch_repository import HospitalBatchRepository
from .services.batch_service import BatchService
from .utils.openapi_auto import assert_route_docs
from .constants import EXT_BATCH_PROCESSOR, EXT_BATCH_REPOSITORY, EXT_CSV_VALIDATOR, EXT_BATCH_SERVICE

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
    
    configure_logging(app)
    
    register_middlewares(app)
    
    from .api import bp as api_bp
    app.register_blueprint(api_bp)
    
    configure_swagger(app)
    
    def client_factory():
        return HospitalApiClient(base_url=app.config['HOSPITAL_API_BASE_URL'])

    repository = HospitalBatchRepository()
    batch_processor = BatchProcessor(
        client_factory=client_factory,
        repository=repository,
        logger=logging.getLogger('app.batch_processor')
    )
    validator = HospitalCsvValidator()
    parser = CsvHospitalParser()
    batch_service = BatchService(validator=validator, repository=repository, processor=batch_processor)

    app.extensions = getattr(app, 'extensions', {})
    app.extensions[EXT_BATCH_PROCESSOR] = batch_processor
    app.extensions[EXT_BATCH_REPOSITORY] = repository
    app.extensions[EXT_CSV_VALIDATOR] = validator
    app.extensions[EXT_BATCH_SERVICE] = batch_service

    strict_docs = app.config.get('OPENAPI_STRICT_DOCS', False)
    try:
        assert_route_docs(app, strict=strict_docs)
    except Exception as e:
        raise

    app.logger.info("Application initialized successfully")
    return app

