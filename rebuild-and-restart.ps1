# Rebuild and restart file server containers
Write-Host "Stopping file server containers..." -ForegroundColor Cyan
docker compose down

Write-Host "`nRebuilding and starting file server containers..." -ForegroundColor Cyan
docker compose up -d --build

Write-Host "`nCleaning up old file-server images..." -ForegroundColor Cyan
docker images --filter "dangling=true" --filter "label=com.docker.compose.project=file-server" --format "{{.ID}}" | ForEach-Object { docker rmi $_ }

Write-Host "`nDone!" -ForegroundColor Green
