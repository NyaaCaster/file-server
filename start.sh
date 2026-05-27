#!/bin/sh

echo "Starting file server..."

if [ "$ENABLE_UPLOAD_API" = "true" ]; then
    echo "[Config] Upload API: ENABLED"
    cp /etc/nginx/templates/with-upload.conf /etc/nginx/conf.d/default.conf
    cd /app
    node index.js &
else
    echo "[Config] Upload API: DISABLED (static file server only)"
    cp /etc/nginx/templates/without-upload.conf /etc/nginx/conf.d/default.conf
fi

nginx -g 'daemon off;' &

wait -n
exit $?
