import time
import logging
import io
from flask import request, jsonify, current_app
from ..constants import (
    EXT_BATCH_PROCESSOR,
    EXT_CSV_VALIDATOR,
    EXT_BATCH_SERVICE,
    KEY_TOTAL_HOSPITALS,
    KEY_PROCESSED_COUNT,
    KEY_FAILED_COUNT,
    KEY_STATUS,
)
from . import bp

logger = logging.getLogger(__name__)

@bp.route('/', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify API is running.
    
    ---
    get:
      tags: [System]
      summary: API Health Check
      description: Returns status OK when the API is operational
      responses:
        '200':
          description: API is operational
    """
    return jsonify({"status": "OK"}), 200

@bp.route('/hospitals/bulk', methods=['POST'])
def bulk_create_hospitals():
    """
    Upload a CSV file with hospital data for bulk processing in the background.
    Returns immediately with a batch ID that can be used to check processing status.

    ---
    post:
      tags: [Hospitals]
      summary: Bulk create hospitals from CSV
      description: Upload a CSV file with hospital data for background processing. Returns immediately with a batch ID.
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file]
              properties:
                file:
                  type: string
                  format: binary
                  description: CSV file containing hospital data (name,address,phone)
      responses:
        '202':
          description: Request accepted, processing in background
        '400':
          description: Invalid request or CSV format
    """
    start_time = time.time()
    logger.info("Bulk hospital creation request received")
    
    if 'file' not in request.files:
        logger.warning("Bulk upload request missing file")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    filename = file.filename
    logger.info(f"Processing uploaded file: {filename}")

    if filename == '' or not filename.endswith('.csv'):
        logger.warning(f"Invalid file format: {filename}")
        return jsonify({'error': 'Invalid file format. Only CSV files are accepted'}), 400

    try:
        csv_text = file.stream.read().decode("UTF-8")

        batch_service = current_app.extensions.get(EXT_BATCH_SERVICE)
        result = batch_service.bulk_create_hospitals(csv_text, max_hospitals=current_app.config.get('MAX_HOSPITALS_PER_BATCH'))

        elapsed_time = time.time() - start_time
        if not result.get("ok"):
            logger.warning(f"CSV validation failed ({elapsed_time:.2f}s)")
            return jsonify(result.get("body", {})), result.get("status", 400)

        body = result.get("body", {})
        batch_id = body.get('batch_id')
        hospital_count = body.get('total_hospitals', 0)
        logger.info(f"Bulk upload request accepted, batch {batch_id} ({hospital_count} hospitals) - {elapsed_time:.2f}s")
        return jsonify(body), result.get("status", 202)

    except UnicodeDecodeError:
        logger.error(f"File {filename} is not a valid UTF-8 encoded CSV")
        return jsonify({'error': 'File is not a valid UTF-8 encoded CSV'}), 400
    except ValueError as e:
        logger.warning(f"CSV validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception(f"Unexpected error processing bulk upload: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred processing the file'}), 500

@bp.route('/hospitals/validate', methods=['POST'])
def validate_hospitals_csv():
    """
    Validate a CSV file with hospital data without creating a batch.

    ---
    post:
      tags: [Hospitals]
      summary: Validate hospital CSV
      description: Upload a CSV file to validate header and rows. No processing is started.
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file]
              properties:
                file:
                  type: string
                  format: binary
                  description: CSV file containing hospital data (name,address,phone)
      responses:
        '200':
          description: Validation results
        '400':
          description: Invalid request or CSV format
    """
    start_time = time.time()
    logger.info("CSV validation request received")

    if 'file' not in request.files:
        logger.warning("Validation request missing file")
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    filename = file.filename
    logger.info(f"Validating uploaded file: {filename}")

    if filename == '' or not filename.endswith('.csv'):
        logger.warning(f"Invalid file format for validation: {filename}")
        return jsonify({'error': 'Invalid file format. Only CSV files are accepted'}), 400

    try:
        csv_text = file.stream.read().decode("UTF-8")

        batch_service = current_app.extensions.get(EXT_BATCH_SERVICE)
        result = batch_service.validate_hospitals(csv_text, max_hospitals=current_app.config.get('MAX_HOSPITALS_PER_BATCH'))
        elapsed_time = time.time() - start_time
        if not result.get("valid"):
            logger.info(f"CSV invalid: {len(result.get('errors', []))} errors ({elapsed_time:.2f}s)")
        else:
            logger.info(f"CSV valid: {result.get('row_count', 0)} rows ({elapsed_time:.2f}s)")

        return jsonify(result), 200

    except UnicodeDecodeError:
        logger.error(f"File {filename} is not a valid UTF-8 encoded CSV")
        return jsonify({'error': 'File is not a valid UTF-8 encoded CSV'}), 400
    except Exception as e:
        logger.exception(f"Unexpected error validating CSV: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred validating the file'}), 500

@bp.route('/hospitals/batch/<batch_id>/status', methods=['GET'])
def get_batch_status(batch_id):
    """
    Get the current processing status of a batch

    ---
    get:
      tags: [Hospitals]
      summary: Get batch processing status
      description: Get the current processing status of a hospital batch
      parameters:
        - in: path
          name: batch_id
          required: true
          schema:
            type: string
          description: Batch ID (UUID)
      responses:
        '200':
          description: Current batch status
        '404':
          description: Batch not found
    """
    start_time = time.time()
    logger.info(f"Status request for batch {batch_id}")
    
    try:
        batch_service = current_app.extensions.get(EXT_BATCH_SERVICE)
        result = batch_service.get_batch_status(batch_id)

        elapsed_time = time.time() - start_time
        if not result.get("ok"):
            logger.warning(f"Batch {batch_id} not found ({elapsed_time:.2f}s)")
            return jsonify(result.get("body", {})), result.get("status", 404)

        body = result.get("body", {})
        total = body.get(KEY_TOTAL_HOSPITALS, 0)
        processed = body.get(KEY_PROCESSED_COUNT, 0)
        failed = body.get(KEY_FAILED_COUNT, 0)
        batch_status = body.get(KEY_STATUS, 'unknown')
        logger.info(f"Returned status for batch {batch_id}: {batch_status}, processed: {processed}/{total}, failed: {failed} ({elapsed_time:.2f}s)")
        return jsonify(body), result.get("status", 200)
    except Exception as e:
        logger.exception(f"Error getting status for batch {batch_id}: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred while retrieving batch status'}), 500


@bp.route('/hospitals/batch/<batch_id>/resume', methods=['PATCH'])
def resume_batch(batch_id):
    """
    Resume processing for a previously started batch by re-queueing unprocessed/failed rows.

    ---
    patch:
      tags: [Hospitals]
      summary: Resume batch processing
      description: Resume processing for a previously started batch by re-queueing unprocessed or failed rows.
      parameters:
        - in: path
          name: batch_id
          required: true
          schema:
            type: string
          description: Batch ID (UUID)
      responses:
        '202':
          description: Resume accepted; background processing scheduled
        '200':
          description: Nothing to resume
        '409':
          description: Batch is still processing; cannot resume
    """
    try:
        batch_service = current_app.extensions.get(EXT_BATCH_SERVICE)
        result = batch_service.resume_batch(batch_id)
        body = result.get('body', {})
        status = result.get('status', 202)
        return jsonify(body), status
    except Exception as e:
        logger.exception(f"Error resuming batch {batch_id}: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred while resuming batch'}), 500