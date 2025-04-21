# Simple FastAPI File Processing API

This is a basic FastAPI application that demonstrates file uploads and downloads.

## Setup

1.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the API

Use uvicorn to run the application:

```bash
uvicorn main:app --reload
```

This will start the server, typically at `http://127.0.0.1:8000`.

## Usage

-   Navigate to `http://127.0.0.1:8000` in your browser to see the welcome message.
-   Navigate to `http://127.0.0.1:8000/docs` for the interactive API documentation (Swagger UI).
-   Use a tool like `curl` or Postman to send a POST request to the `/processfile/` endpoint with a file attached.

    Example using `curl`:
    ```bash
    curl -X POST "http://127.0.0.1:8000/processfile/" -F "file=@your_file_name.txt" -o output.txt
    ```
    Replace `your_file_name.txt` with the path to the file you want to upload. The processed (mocked) output will be saved to `output.txt`.
