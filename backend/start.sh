#!/bin/sh

# This script is the entrypoint for the Docker container.
# It starts the Uvicorn server.

# The server is bound to 0.0.0.0 to be accessible from outside the container.
uvicorn app.main:app --host 0.0.0.0 --port 8000
