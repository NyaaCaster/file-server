# 文件服务器 Docker 项目

一个基于 Nginx 的安全文件服务器，支持 HTTPS 访问、实时文件更新和 API 上传服务。

## 🚀 功能特性

### 文件服务器
- ✅ **HTTP/HTTPS 双协议支持**：同时支持 HTTP 和 HTTPS 访问
- ✅ **HTTPS 加密传输**：使用 SSL 证书保护数据安全
- ✅ **目录浏览**：自动生成文件列表页面
- ✅ **实时更新**：修改 `./Files` 目录中的文件会立即反映到浏览器

### 上传服务
- ✅ **API Key 鉴权**：简单的单 Key 认证机制
- ✅ **多文件上传**：支持单文件和批量上传
- ✅ **文件管理**：支持上传、删除、列表查询

## 📋 系统要求

- Docker
- Docker Compose
- 端口 5101 (HTTP)、5102 (HTTPS)、5103 (上传 API) 未被占用

## 🛠️ 快速开始

### 1. 配置 API Key

```bash
# 复制示例配置
cp upload-server/api-keys.env.example upload-server/api-keys.env

# 编辑配置，设置你的 API Key（32+ 字符推荐）
# api-keys.env 文件不会被提交到 Git
```

### 2. 配置 SSL 证书

将 SSL 证书放入 `./SSL` 目录：
- `your-domain.com.key` - 私钥文件
- `your-domain.com_bundle.crt` - 证书文件

### 3. 构建并启动容器

```bash
docker-compose up -d --build
```

### 4. 访问服务

| 服务 | 端口 | 地址 | 说明 |
|------|------|------|------|
| 文件服务器 HTTP | 5101 | `http://localhost:5101/files/` | HTTP 文件访问 |
| 文件服务器 HTTPS | 5102 | `https://localhost:5102/files/` | HTTPS 文件访问 |
| 上传 API | 5103 | `http://localhost:5103/api/` | 直接访问上传 API |

**注意**：通过 Nginx 代理访问上传 API（端口 5101/5102）更安全。

## 📁 目录结构

```
file-server/
├── Dockerfile              # 单一镜像配置
├── docker-compose.yml      # Docker Compose 配置
├── nginx.conf              # Nginx 配置（含 API 代理）
├── start.sh                # 启动脚本
├── Files/                  # 文件存储目录
├── SSL/                    # SSL 证书目录
├── upload-server/          # 上传服务
│   ├── index.js
│   ├── package.json
│   ├── api-keys.env.example  # API Key 示例
│   └── api-keys.env          # 实际 Key（不提交）
└── README.md
```

## 🔑 API Key 配置

### 配置文件格式 (api-keys.env)

```env
# File Server API Key Configuration
API_KEY=sk-file-your-secret-key-here-32chars
```

### 安全建议

- 使用 32+ 字符的随机字符串
- 不要使用容易猜测的内容
- 定期更换 Key

## 📡 API 接口

### 认证方式

所有 API 请求需要在 Header 中携带 API Key：

```
Authorization: Bearer YOUR_API_KEY
```

### 上传单文件

```bash
# 推荐方式：使用 Header 指定目录
curl -X POST http://localhost:5101/api/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Upload-Category: images/avatars" \
  -F "file=@/path/to/file.jpg"

# 或使用查询参数
curl -X POST "http://localhost:5101/api/upload?category=images/avatars" \
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
curl -X POST http://localhost:5101/api/upload/multiple \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Upload-Category: images/gallery" \
  -F "files=@/path/to/file1.jpg" \
  -F "files=@/path/to/file2.png"
```

### 删除文件

```bash
curl -X POST http://localhost:5101/api/delete \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"path": "images/old-file.jpg"}'
```

### 列出文件

```bash
curl -X POST http://localhost:5101/api/list \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"category": "images"}'
```

### 健康检查

```bash
curl http://localhost:5101/health
```

## 💻 前端集成示例

```typescript
async function uploadFile(file: File, apiKey: string, category: string = 'images'): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('https://your-domain.com:5102/api/upload', {
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

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **HTTP 端口** | 5101 | 文件服务器 HTTP |
| **HTTPS 端口** | 5102 | 文件服务器 HTTPS |
| **API 端口** | 5103 | 上传服务 API（直接访问） |
| **内部 API 端口** | 8080 | Nginx 代理到内部端口 |
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

# 重建并启动
docker-compose up -d --build

# 停止服务
docker-compose down
```

## 🔒 安全建议

1. **保护 API Key**：`api-keys.env` 不会被提交到 Git
2. **使用 HTTPS**：生产环境建议使用 HTTPS 上传
3. **定期更换 Key**：建议定期轮换 API Key

## 📝 更新日志

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
