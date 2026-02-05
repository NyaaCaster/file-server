FROM nginx:alpine

# 创建文件目录和 SSL 目录
RUN mkdir -p /usr/share/nginx/html/files
RUN mkdir -p /etc/nginx/ssl

# 复制 SSL 证书
COPY SSL/ /etc/nginx/ssl/

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 5100

CMD ["nginx", "-g", "daemon off;"]