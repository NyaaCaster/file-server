# 文件服务器 Docker 项目

一个基于 Nginx 的安全文件服务器，支持 HTTPS 访问和实时文件更新。

## 🚀 功能特性

- ✅ **HTTPS 加密传输**：使用 SSL 证书保护数据安全
- ✅ **目录浏览**：自动生成文件列表页面
- ✅ **实时更新**：修改 `./Files` 目录中的文件会立即反映到浏览器
- ✅ **无需重启**：文件变更无需重启容器
- ✅ **文件信息显示**：显示文件大小和修改时间
- ✅ **支持所有文件类型**：文档、图片、视频等
- ✅ **时区配置**：Asia/Shanghai (UTC+8)
- ✅ **禁用缓存**：确保始终获取最新文件

## 📋 系统要求

- Docker
- Docker Compose
- 端口 5100 未被占用

## 🛠️ 快速开始

### 1. 构建并启动容器

```bash
cd file-server
docker-compose up -d --build
```

### 2. 访问文件服务器

打开浏览器访问：

- **本地访问**: `https://localhost:5100/files/`
- **域名访问**: `https://h.hony-wen.com:5100/files/`

### 3. 添加和管理文件

将你的文件放入 `./Files` 目录：

```bash
# 复制文件到 Files 目录
cp /path/to/your/file.pdf ./Files/

# 创建子目录
mkdir ./Files/documents

# 刷新浏览器即可看到新文件
```

## 📁 目录结构

```
file-server/
├── Dockerfile              # Docker 镜像配置
├── docker-compose.yml      # Docker Compose 配置
├── nginx.conf              # Nginx 服务器配置
├── .dockerignore           # Docker 构建忽略文件
├── SSL/                    # SSL 证书目录
│   ├── h.hony-wen.com.key
│   ├── h.hony-wen.com_bundle.crt
│   └── ...
├── Files/                  # 文件存储目录（映射到容器）
│   └── README.txt          # 示例文件
└── README.md               # 项目说明文档
```

## ⚙️ 配置说明

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **端口** | 5100 | HTTPS 服务端口 |
| **协议** | HTTPS | 使用 SSL/TLS 加密 |
| **SSL 协议** | TLSv1.2, TLSv1.3 | 支持的 SSL 版本 |
| **文件目录** | `./Files` | 本地文件存储路径 |
| **容器路径** | `/usr/share/nginx/html/files` | 容器内文件路径 |
| **时区** | Asia/Shanghai | 东八区时间 |
| **自动重启** | unless-stopped | 容器异常时自动重启 |

## 🔧 常用命令

### 容器管理

```bash
# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 重启容器
docker-compose restart

# 停止容器
docker-compose stop

# 启动已停止的容器
docker-compose start

# 停止并删除容器
docker-compose down

# 重新构建镜像
docker-compose build --no-cache
```

### 文件操作

```bash
# 查看 Files 目录内容
ls -lh ./Files/

# 递归查看所有文件
find ./Files/ -type f

# 查看文件数量
find ./Files/ -type f | wc -l
```

## 🌐 访问示例

假设你在 `./Files` 目录中有以下文件结构：

```
Files/
├── document.pdf
├── image.png
└── videos/
    └── demo.mp4
```

访问 URL：

- 文件列表：`https://localhost:5100/files/`
- PDF 文件：`https://localhost:5100/files/document.pdf`
- 图片文件：`https://localhost:5100/files/image.png`
- 视频文件：`https://localhost:5100/files/videos/demo.mp4`

## 🔒 安全建议

⚠️ **重要提示**：此服务器配置适用于本地开发或内网环境。

如需公网访问，请考虑以下安全措施：

1. **添加身份验证**
   ```nginx
   auth_basic "Restricted Access";
   auth_basic_user_file /etc/nginx/.htpasswd;
   ```

2. **限制访问 IP**
   ```nginx
   allow 192.168.1.0/24;
   deny all;
   ```

3. **禁用目录浏览**（如果不需要）
   ```nginx
   autoindex off;
   ```

4. **设置文件大小限制**
   ```nginx
   client_max_body_size 100M;
   ```

5. **配置防火墙规则**

6. **定期更新 SSL 证书**

## 🐛 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs

# 检查端口占用
netstat -ano | findstr :5100  # Windows
lsof -i :5100                  # Linux/Mac
```

### SSL 证书错误

- 确认 `./SSL` 目录中有正确的证书文件
- 检查证书文件名是否匹配 nginx.conf 中的配置
- 验证证书是否过期

### 文件无法访问

- 检查文件权限
- 确认文件在 `./Files` 目录中
- 刷新浏览器缓存（Ctrl+F5）

### 文件更新不生效

- 清除浏览器缓存
- 检查容器日志是否有错误
- 重启容器：`docker-compose restart`

## 📝 更新日志

### v1.0.0 (2026-02-06)

- ✨ 初始版本发布
- ✅ 支持 HTTPS 访问
- ✅ 实时文件更新
- ✅ 目录浏览功能
- ✅ SSL 证书集成

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 域名：h.hony-wen.com
- 项目地址：[GitHub](https://github.com/your-repo)

---

**享受你的文件服务器！** 🎉
