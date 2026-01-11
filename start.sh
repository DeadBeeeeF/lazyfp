#!/bin/bash

# Define Port
PORT=8000

echo "Checking for existing process on port $PORT..."

# Kill process on port 8000 if it exists
# fuser returns non-zero if no process is found, so we ignore errors
fuser -k $PORT/tcp > /dev/null 2>&1

# Wait a moment to ensure release
sleep 1

echo "Starting LazyFP WebUI..."
# Run uvicorn using the venv
./venv/bin/uvicorn app:app --reload --host 0.0.0.0 --port $PORT
