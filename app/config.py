import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    HOSPITAL_API_BASE_URL = os.environ.get('HOSPITAL_API_BASE_URL')
    MAX_HOSPITALS_PER_BATCH = int(os.environ.get('MAX_HOSPITALS_PER_BATCH', '20'))
    
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', 'default')
    ENV = os.environ.get('FLASK_ENV', 'production')
    BATCH_STORAGE_DIR = os.environ.get('BATCH_STORAGE_DIR', 'batches')
    OPENAPI_STRICT_DOCS = os.environ.get('OPENAPI_STRICT_DOCS', 'false').lower() == 'true'

