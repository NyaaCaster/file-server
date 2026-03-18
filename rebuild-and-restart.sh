#!/bin/bash
# Rebuild and restart file server containers

echo "Stopping file server containers..."
docker compose down

echo ""
echo "Rebuilding and starting file server containers..."
docker compose up -d --build

echo ""
echo "Cleaning up old file-server images..."
docker images --filter "dangling=true" --filter "label=com.docker.compose.project=file-server" --format "{{.ID}}" | xargs -r docker rmi

echo ""
echo "Done!"
