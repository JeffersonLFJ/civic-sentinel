#!/bin/bash
set -e

# Ensure data directories exist (redundant safety)
mkdir -p data/chromadb data/sqlite data/uploads_temp data/processed

echo "Starting Sentinel Civic Backend..."
exec "$@"
