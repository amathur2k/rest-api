from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import io

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.post("/processfile/")
async def process_file(file: UploadFile = File(...)):
    """
    Receives a file, processes it (mocked), and returns a processed file.
    Now modified to simply return the uploaded file directly.
    """
    # Return the uploaded file content directly
    # We need to read the file content into a BytesIO object because
    # the file object might be closed by the time StreamingResponse reads it.
    file_content = await file.read()
    content_stream = io.BytesIO(file_content)
    
    # Ensure the stream is reset to the beginning
    content_stream.seek(0) 

    return StreamingResponse(
        content_stream,
        media_type=file.content_type,
        headers={"Content-Disposition": f"attachment; filename={file.filename}"}
    )

# Add this for local testing if needed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
