FROM nginx:alpine

RUN apk add --no-cache nodejs npm

RUN mkdir -p /usr/share/nginx/html/files
RUN mkdir -p /etc/nginx/ssl
RUN mkdir -p /app/config

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY upload-server/package.json /app/package.json
RUN cd /app && npm install --production

COPY upload-server/index.js /app/index.js

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80 443 8080

CMD ["/start.sh"]
