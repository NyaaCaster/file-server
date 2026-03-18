FROM nginx:alpine

RUN mkdir -p /usr/share/nginx/html/files
RUN mkdir -p /etc/nginx/ssl

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5100

CMD ["nginx", "-g", "daemon off;"]
