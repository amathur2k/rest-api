from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import io

app = FastAPI()

@app.post("/processfile/")
async def process_file(file: UploadFile = File(...)):
    """
    Accepts a file upload, mocks processing, and returns a dummy file.
    """
    print(f"Received file: {file.filename}")
    print(f"Content type: {file.content_type}")

    # --- Mock file processing --- 
    # In a real application, you would read the file content using:
    # content = await file.read()
    # And then process the content.
    
    # Here, we just simulate creating an output file.
    output_content = f"Processed content for {file.filename}\nThis is mocked output."
    output_stream = io.StringIO(output_content)
    
    # Define the output filename
    output_filename = f"processed_{file.filename}.txt"
    
    # --- End Mock Processing ---
    
    return StreamingResponse(
        iter([output_stream.getvalue()]), 
        media_type="text/plain", 
        headers={"Content-Disposition": f"attachment; filename={output_filename}"}
    )

@app.get("/")
async def read_root():
    return {"message": "Welcome to the File Processing API. Use the /processfile/ endpoint to upload files."}
