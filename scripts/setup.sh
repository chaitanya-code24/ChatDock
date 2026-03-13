#!/usr/bin/env bash
set -e
echo "Installing backend dependencies..."
python -m pip install -r backend/requirements.txt
echo "Setup complete."
