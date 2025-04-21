import time
import os
import logging
from celery_app import celery
from config import UPLOAD_FOLDER

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery.task(bind=True)
def process_uploaded_file_task(self, filepath: str):
    """Celery task to process the uploaded file, save result, return result path."""
    logger.info(f"[{self.request.id}] Received task for file: {filepath}")

    original_filename = os.path.basename(filepath)
    processed_filename = f"{os.path.splitext(original_filename)[0]}_processed{os.path.splitext(original_filename)[1]}"
    processed_filepath = os.path.join(UPLOAD_FOLDER, processed_filename)

    if not os.path.exists(filepath):
        logger.error(f"[{self.request.id}] File not found: {filepath}")
        self.update_state(state='FAILURE', meta={'exc_type': 'FileNotFoundError', 'exc_message': f'File not found: {filepath}'})
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        logger.info(f"[{self.request.id}] Simulating processing for 5 seconds...")
        time.sleep(5)

        # --- Actual Processing Would Go Here ---
        # Read input file
        with open(filepath, 'r', encoding='utf-8') as f_in:
            processed_content = f_in.read()
            # Example modification: Add a prefix
            processed_content = f"Processed Content:\n--------------------\n{processed_content}"

        # Save processed content to a new file
        logger.info(f"[{self.request.id}] Saving processed content to: {processed_filepath}")
        with open(processed_filepath, 'w', encoding='utf-8') as f_out:
            f_out.write(processed_content)

        logger.info(f"[{self.request.id}] Processing complete. Result saved to: {processed_filepath}")

        # Clean up the *original* temporary input file after processing
        try:
            os.remove(filepath)
            logger.info(f"[{self.request.id}] Removed original temporary file: {filepath}")
        except OSError as e:
            logger.error(f"[{self.request.id}] Error removing original temporary file {filepath}: {e}")

        # Return the path to the *processed* file
        return {"result_filepath": processed_filepath, "result_filename": processed_filename}

    except Exception as e:
        logger.error(f"[{self.request.id}] Error processing file {filepath}: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        # Attempt to clean up input file even on failure, if it exists
        if os.path.exists(filepath):
             try:
                 os.remove(filepath)
                 logger.info(f"[{self.request.id}] Removed original temporary file after error: {filepath}")
             except OSError as e_rem:
                 logger.error(f"[{self.request.id}] Error removing original file {filepath} after error: {e_rem}")
        # Clean up potentially partially written output file on failure
        if os.path.exists(processed_filepath):
            try:
                os.remove(processed_filepath)
                logger.info(f"[{self.request.id}] Removed partial result file after error: {processed_filepath}")
            except OSError as e_rem_out:
                logger.error(f"[{self.request.id}] Error removing partial result file {processed_filepath} after error: {e_rem_out}")
        raise

# Ensure the upload folder exists when the module loads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logger.info(f"Ensured upload folder exists: {UPLOAD_FOLDER}")
