#!/bin/sh

echo "Starting file server..."

cd /app
node index.js &

nginx -g 'daemon off;' &

wait -n
exit $?
