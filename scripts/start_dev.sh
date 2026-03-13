#!/usr/bin/env bash
set -e
echo "Starting infrastructure and app stack..."
docker compose -f infrastructure/docker-compose.yml up --build
