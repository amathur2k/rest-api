#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define the Redis URL from the first argument, or use a default (e.g., localhost for testing)
REDIS_URL=${1:-"redis://localhost:6379/0"} # Default to localhost if no arg given
UPLOAD_FOLDER="./uploads"
PROJECT_DIR=$(pwd) # Assumes the script is run from the project root

echo "--- Starting Deployment ---"

# 1. Pull latest code
echo "Updating code from Git..."
git pull origin main

# 2. Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate # Assuming venv exists in project root

# 3. Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# 4. Create .env file if it doesn't exist or update Redis URL
echo "Configuring environment..."
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Creating .env file..."
  echo "CELERY_BROKER_URL=$REDIS_URL" > $ENV_FILE
  echo "CELERY_RESULT_BACKEND=$REDIS_URL" >> $ENV_FILE
  echo "UPLOAD_FOLDER=$UPLOAD_FOLDER" >> $ENV_FILE
  echo ".env file created."
else
  echo ".env file found. Ensuring Redis URL is set..."
  # Remove existing Redis lines and add the new one (simple approach)
  # Note: Use temp file for macOS compatibility with sed -i
  sed '/^CELERY_BROKER_URL=/d' $ENV_FILE > ${ENV_FILE}.tmp && mv ${ENV_FILE}.tmp $ENV_FILE
  sed '/^CELERY_RESULT_BACKEND=/d' $ENV_FILE > ${ENV_FILE}.tmp && mv ${ENV_FILE}.tmp $ENV_FILE

  echo "CELERY_BROKER_URL=$REDIS_URL" >> $ENV_FILE
  echo "CELERY_RESULT_BACKEND=$REDIS_URL" >> $ENV_FILE
  
  # Ensure UPLOAD_FOLDER exists
  if ! grep -q "^UPLOAD_FOLDER=" $ENV_FILE; then
    echo "UPLOAD_FOLDER=$UPLOAD_FOLDER" >> $ENV_FILE
  fi
  echo ".env file updated/verified."
fi

# 5. Stop existing servers (if any - simple approach using pkill)
echo "Attempting to stop any existing Celery/Uvicorn processes..."
pkill -f "celery -A celery_app.celery worker" || echo "No running Celery worker found to stop."
pkill -f "uvicorn main:app" || echo "No running Uvicorn server found to stop."
sleep 2 # Give processes a moment to stop

# 6. Start Celery worker in background
echo "Starting Celery worker in background..."
nohup celery -A celery_app.celery worker --loglevel=info > celery_worker.log 2>&1 &
sleep 2 # Give worker a moment to start

# 7. Start Uvicorn server in background
echo "Starting Uvicorn server in background..."
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &

echo "--- Deployment Attempt Complete ---"
echo "Servers started in background. Check celery_worker.log and uvicorn.log for status."
echo "App should be accessible at http://<your_ec2_public_ip>:8000"
