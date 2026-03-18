#!/bin/bash
# Rebuild and restart file server containers
# 使用 -p 参数明确指定项目名称，避免与主项目冲突
# 使用 -f 参数明确指定配置文件路径

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="file-server"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

echo "Stopping file server containers..."
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE down

echo ""
echo "Rebuilding and starting file server containers..."
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d --build

echo ""
echo "Cleaning up old file-server images..."
docker images --filter "dangling=true" --filter "label=com.docker.compose.project=$PROJECT_NAME" --format "{{.ID}}" | xargs -r docker rmi

echo ""
echo "Done!"
