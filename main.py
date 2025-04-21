import io
import os
import uuid
import logging
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse

# --- New Imports ---
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from celery.result import AsyncResult
from config import UPLOAD_FOLDER
from tasks import process_uploaded_file_task 
from celery_app import celery 

# --- Rate Limiting Setup ---
# Use a simple in-memory storage for rate limiting (suitable for single-instance local dev)
# For production with multiple workers, use a shared storage like Redis
limiter = Limiter(key_func=lambda: "global", default_limits=["10/minute"])

# --- FastAPI App Initialization ---
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logger.info(f"Ensured upload folder exists at startup: {UPLOAD_FOLDER}")

# --- Original Endpoints (can be kept or removed) ---
@app.get("/")
def read_root():
    return {"Hello": "World"}

# --- Modified File Processing Endpoint ---
@app.post("/processfile/")
@limiter.limit("5/minute") 
async def create_upload_file(request: Request, file: UploadFile = File(...)):
    """Accepts file upload, saves it, queues processing task, returns job ID."""
    try:
        # Generate a unique filename to avoid collisions
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

        # Save the uploaded file asynchronously
        logger.info(f"Saving uploaded file to: {filepath}")
        with open(filepath, "wb") as buffer:
            content = await file.read() 
            buffer.write(content) 
        logger.info(f"File saved successfully: {filepath}")

        # Dispatch the Celery task
        logger.info(f"Dispatching Celery task for file: {filepath}")
        task = process_uploaded_file_task.delay(filepath)
        logger.info(f"Celery task dispatched with ID: {task.id}")

        return JSONResponse(status_code=202, content={"job_id": task.id, "message": "File upload accepted, processing started."}) 

    except Exception as e:
        logger.error(f"Error during file upload or task dispatch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    finally:
        # Ensure the file object is closed
        await file.close()

# --- New Job Status Endpoint ---
@app.get("/jobstatus/{job_id}")
def get_job_status(job_id: str):
    """Checks the status of a Celery task."""
    logger.info(f"Checking status for job ID: {job_id}")
    task_result = AsyncResult(job_id, app=celery)

    response = {
        "job_id": job_id,
        "status": task_result.status,
        "result": None
    }

    if task_result.failed():
        logger.warning(f"Job {job_id} failed. State: {task_result.state}")
        response["result"] = {"error": str(task_result.result), "traceback": task_result.traceback}
    elif task_result.successful():
        logger.info(f"Job {job_id} succeeded.")
        response["result"] = task_result.result 
    else:
        logger.info(f"Job {job_id} status: {task_result.status}")
        response["result"] = f"Task is currently in state: {task_result.status}"

    return response

# --- Modified Result Retrieval Endpoint (now POST and returns file) ---
@app.post("/jobresult/{job_id}") 
def get_job_result(job_id: str):
    """Retrieves the final result file of a successful Celery task as a download."""
    logger.info(f"Retrieving result file for job ID: {job_id}")
    task_result = AsyncResult(job_id, app=celery)

    if task_result.successful():
        result_data = task_result.result
        logger.info(f"Job {job_id} succeeded. Result data: {result_data}")

        if isinstance(result_data, dict) and "result_filepath" in result_data and "result_filename" in result_data:
            result_filepath = result_data["result_filepath"]
            result_filename = result_data["result_filename"]

            if os.path.exists(result_filepath):
                logger.info(f"Result file found: {result_filepath}. Sending as download: {result_filename}")
                return FileResponse(
                    path=result_filepath,
                    filename=result_filename,
                    media_type='application/octet-stream' 
                )
            else:
                logger.error(f"Job {job_id} successful, but result file not found at: {result_filepath}")
                raise HTTPException(status_code=404, detail=f"Result file for job {job_id} not found on server.")
        else:
            logger.error(f"Job {job_id} successful, but result structure is invalid: {result_data}")
            raise HTTPException(status_code=500, detail=f"Internal server error: Invalid result structure for job {job_id}.")

    elif task_result.failed():
        logger.warning(f"Job {job_id} failed. Cannot retrieve result file.")
        raise HTTPException(status_code=400, detail=f"Job {job_id} failed: {str(task_result.result)}")
    else:
        logger.info(f"Job {job_id} not yet successful (Status: {task_result.status}). Cannot retrieve result file.")
        raise HTTPException(status_code=202, detail=f"Job {job_id} is not complete yet (Status: {task_result.status}). Please try again later.")


# Add this for local testing if needed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
