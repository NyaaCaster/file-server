# 文件服务器 Docker 项目

一个基于 Nginx 的安全文件服务器，支持 HTTPS 访问、实时文件更新和可选的上传 API 服务。

## 🚀 功能特性

### 文件服务器
- ✅ **HTTP/HTTPS 双协议支持**：同时支持 HTTP 和 HTTPS 访问
- ✅ **HTTPS 加密传输**：使用 SSL 证书保护数据安全
- ✅ **目录浏览**：自动生成文件列表页面
- ✅ **实时更新**：修改 `./Files` 目录中的文件会立即反映到浏览器

### 上传服务（可选）
- ✅ **可开关**：通过 `.env` 中的 `ENABLE_UPLOAD_API` 一键启停，关闭时节省内存与 CPU
- ✅ **API Key 鉴权**：简单的单 Key 认证机制
- ✅ **多文件上传**：支持单文件和批量上传
- ✅ **文件管理**：支持上传、删除、列表查询

## 📋 系统要求

- Docker
- Docker Compose
- 端口未被占用（默认 80 / 443 / 8080，可在 `docker-compose.yml` 中调整）

## 🛠️ 快速开始

### 1. 配置 `.env`

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env，至少设置 API_KEY（推荐 32+ 字符随机串）
# .env 文件不会被提交到 Git
```

`.env` 支持的配置项见 [配置说明](#️-配置说明)。

### 2. 配置 `docker-compose.yml`

```bash
# 复制示例配置
cp docker-compose.example.yml docker-compose.yml

# 按需修改端口映射（示例使用默认 80/443/8080，主项目可能使用 5101/5102/5103 等）
# docker-compose.yml 文件不会被提交到 Git
```

> `docker-compose.example.yml` 是模板，会被提交到 Git。实际使用的 `docker-compose.yml` 因部署环境（端口、卷路径等）不同而异，已加入 `.gitignore`。

### 3. 配置 SSL 证书

将 SSL 证书放入 `./SSL` 目录：
- `your-domain.com.key` - 私钥文件
- `your-domain.com_bundle.crt` - 证书文件

### 4. 构建并启动容器

```bash
docker-compose up -d --build
```

### 5. 访问服务

> 下表以 `docker-compose.example.yml` 的默认端口为例（80/443/8080）。实际端口以你的 `docker-compose.yml` 为准。

| 服务 | 默认端口 | 地址 | 说明 |
|------|---------|------|------|
| 文件服务器 HTTP | 80 | `http://localhost/files/` | HTTP 文件访问 |
| 文件服务器 HTTPS | 443 | `https://localhost/files/` | HTTPS 文件访问 |
| 上传 API | 8080 | `http://localhost:8080/api/` | 直接访问上传 API（仅当启用时） |

**注意**：通过 Nginx 代理访问上传 API（HTTP/HTTPS 端口）更安全。

## 📁 目录结构

```
file-server/
├── Dockerfile                  # 单一镜像配置
├── docker-compose.example.yml  # Docker Compose 配置模板（提交）
├── docker-compose.yml          # 实际 Docker Compose 配置（不提交）
├── nginx.conf                  # Nginx 配置（启用上传 API 时使用）
├── nginx-no-upload.conf        # Nginx 配置（禁用上传 API 时使用，/api 返回 503）
├── start.sh                    # 启动脚本（依据 ENABLE_UPLOAD_API 选择 nginx 配置）
├── .env.example                # 配置示例（提交）
├── .env                        # 实际配置（不提交）
├── Files/                      # 文件存储目录
├── SSL/                        # SSL 证书目录
├── upload-server/              # 上传服务
│   ├── index.js
│   └── package.json
└── README.md
```

## 🔑 上传 API 开关与鉴权

### 开关

通过 `.env` 中的 `ENABLE_UPLOAD_API` 控制：

- `ENABLE_UPLOAD_API=true`（默认）：启动 node 上传服务，`/api` 和 `/health` 正常工作
- `ENABLE_UPLOAD_API=false`：不启动 node 进程，`/api` 与 `/health` 返回 503 提示信息（节省内存与 CPU）

修改后需要重建容器：

```bash
./rebuild-and-restart.ps1   # Windows
./rebuild-and-restart.sh    # Linux/macOS
```

### API Key

在 `.env` 中设置 `API_KEY`：

```env
API_KEY=sk-file-your-secret-key-here-32chars
```

**安全建议：**
- 使用 32+ 字符的随机字符串
- 不要使用容易猜测的内容
- 定期更换 Key

## 📡 API 接口

> 仅在 `ENABLE_UPLOAD_API=true` 时可用。禁用时所有 `/api` 请求会得到 503 响应。

### 认证方式

所有 API 请求需要在 Header 中携带 API Key：

```
Authorization: Bearer YOUR_API_KEY
```

### 上传单文件

```bash
# 推荐方式：使用 Header 指定目录
curl -X POST http://localhost/api/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Upload-Category: images/avatars" \
  -F "file=@/path/to/file.jpg"

# 或使用查询参数
curl -X POST "http://localhost/api/upload?category=images/avatars" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@/path/to/file.jpg"
```

**响应：**
```json
{
  "success": true,
  "filename": "file.jpg",
  "originalName": "file.jpg",
  "size": 102400,
  "mimeType": "image/jpeg",
  "path": "images/avatars/file.jpg",
  "url": "/files/images/avatars/file.jpg"
}
```

> **注意**：文件名保留原始名称，同名文件会被覆盖。目录不存在时会自动创建。

### 批量上传

```bash
curl -X POST http://localhost/api/upload/multiple \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Upload-Category: images/gallery" \
  -F "files=@/path/to/file1.jpg" \
  -F "files=@/path/to/file2.png"
```

### 删除文件

```bash
curl -X POST http://localhost/api/delete \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"path": "images/old-file.jpg"}'
```

### 列出文件

```bash
curl -X POST http://localhost/api/list \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"category": "images"}'
```

### 健康检查

```bash
curl http://localhost/health
```

启用时返回 `{"status":"ok",...}`；禁用时返回 503 `{"status":"upload_api_disabled"}`。

## 💻 前端集成示例

```typescript
async function uploadFile(file: File, apiKey: string, category: string = 'images'): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('https://your-domain.com/api/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'X-Upload-Category': category
    },
    body: formData
  });
  
  const result = await response.json();
  
  if (!result.success) {
    throw new Error(result.error);
  }
  
  return result.url;
}
```

## 📂 目录指定方式

上传时可通过以下方式指定目标目录（按优先级）：

| 方式 | 示例 | 优先级 |
|------|------|--------|
| Header | `-H "X-Upload-Category: images/avatars"` | 1（最高） |
| Query 参数 | `?category=images/avatars` | 2 |
| 表单字段 | `-F "category=images/avatars"` | 3 |
| 默认值 | 无上述参数时 | `general` |

**推荐使用 Header 方式**，因为在 multipart/form-data 请求中，Header 始终可用。

## ⚙️ 配置说明

### `.env` 配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_UPLOAD_API` | `true` | 是否启动上传 API（false 时仅作为静态文件服务器） |
| `API_KEY` | (必填) | 上传 API 鉴权密钥 |
| `TZ` | `Asia/Shanghai` | 容器时区 |

### 固定配置（在 `docker-compose.yml` 中）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| **HTTP 端口** | 80 | 文件服务器 HTTP（可在 docker-compose.yml 中改） |
| **HTTPS 端口** | 443 | 文件服务器 HTTPS（可在 docker-compose.yml 中改） |
| **API 端口** | 8080 | 上传服务 API 直接访问（可在 docker-compose.yml 中改） |
| **内部 API 端口** | 8080 | Nginx 代理到容器内部端口（不建议修改） |
| **文件大小限制** | 50MB | 单文件最大大小 |
| **批量上传限制** | 20个 | 单次最多上传文件数 |

## 🔧 常用命令

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 重建并启动（修改 .env 后需执行）
docker-compose up -d --build

# 停止服务
docker-compose down
```

## 🔒 安全建议

1. **保护 API Key**：`.env` 不会被提交到 Git
2. **关闭未使用的上传 API**：仅需文件服务时设置 `ENABLE_UPLOAD_API=false`，减少攻击面
3. **使用 HTTPS**：生产环境建议使用 HTTPS 上传
4. **定期更换 Key**：建议定期轮换 API Key

## 📝 更新日志

### v1.4.0 (2026-05-28)

- ✨ 新增 `ENABLE_UPLOAD_API` 开关，可关闭 node 上传服务以节省资源
- 🔧 敏感与可变配置迁移到 `.env`（API Key、时区）
- 🗑️ 移除 `upload-server/api-keys.env` 与 `api-keys.env.example`
- ✅ 上传 API 关闭时 `/api` 与 `/health` 返回 503 友好提示
- 📦 `docker-compose.yml` 改为不提交，以 `docker-compose.example.yml` 作为模板

### v1.3.0 (2026-03-19)

- ✨ 支持 Header 方式指定上传目录（`X-Upload-Category`）
- ✅ 文件名保留原始名称，同名文件自动覆盖
- ✅ 多级目录自动创建
- 📝 更新文档，添加目录指定方式说明

### v1.2.0 (2026-03-18)

- ✨ 添加上传服务 API
- ✅ 简化为单 Key 鉴权
- ✅ 整合为单一镜像（Nginx + Node.js）
- ✅ Nginx 代理上传 API

### v1.1.0 (2026-03-18)

- ✨ 添加 HTTP 80 端口支持
- ✅ 端口标准化：HTTP 映射到 5101，HTTPS 映射到 5102

### v1.0.0 (2026-02-06)

- ✨ 初始版本发布

## 📄 许可证

MIT License

## 📧 联系方式

- 项目地址：[GitHub](https://github.com/NyaaCaster/file-server/)
