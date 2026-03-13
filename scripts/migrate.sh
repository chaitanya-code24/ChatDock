#!/usr/bin/env bash
set -e

cd backend
python -m alembic -c alembic.ini upgrade head
echo "Migration complete."

