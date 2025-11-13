# Docker 部署指南 - Azure Image Editor MCP HTTP Server

本文档说明如何使用 Docker 部署和运行 Azure Image Editor MCP HTTP Server。

## 快速开始

### 1. 构建 Docker 镜像

```bash
docker build -t azure-image-editor-mcp:latest .
```

### 2. 运行容器

#### 基础运行（使用环境变量）

```bash
docker run -d \
  --name azure-image-editor \
  -p 8000:8000 \
  -e AZURE_BASE_URL="https://your-endpoint.services.ai.azure.com" \
  -e AZURE_API_KEY="your-api-key" \
  -e AZURE_DEPLOYMENT_NAME="FLUX.1-Kontext-pro" \
  -e AZURE_MODEL="flux.1-kontext-pro" \
  -e AZURE_API_VERSION="2025-04-01-preview" \
  azure-image-editor-mcp:latest
```

#### 使用 .env 文件

```bash
docker run -itd --restart=always \
  --name azure-image-editor \
  -p 8082:8000 \
  --env-file .env \
  azure-image-editor-mcp:latest
```

#### 挂载卷保存生成的图片

```bash
docker run -itd --restart=always \
  --name azure-image-editor \
  -p 8082:8000 \
  -v $(pwd)/images:/app/images \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  azure-image-editor-mcp:latest
```

## 环境变量配置

### 必需的环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `AZURE_BASE_URL` | Azure AI Foundry 服务端点 URL | `https://your-endpoint.services.ai.azure.com` |
| `AZURE_API_KEY` | Azure AI Foundry API 密钥 | `your-api-key-here` |
| `AZURE_DEPLOYMENT_NAME` | 部署的模型名称 | `FLUX.1-Kontext-pro` |

### 可选的环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `AZURE_MODEL` | 使用的模型名称 | `flux.1-kontext-pro` |
| `AZURE_API_VERSION` | Azure API 版本 | `2025-04-01-preview` |
| `MCP_SERVER_HOST` | HTTP 服务器监听地址 | `0.0.0.0` |
| `MCP_SERVER_PORT` | HTTP 服务器端口 | `8000` |
| `DEFAULT_IMAGE_SIZE` | 默认生成图片尺寸 | `1024x1024` |

## Docker Compose 部署

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  azure-image-editor:
    build: .
    image: azure-image-editor-mcp:latest
    container_name: azure-image-editor
    ports:
      - "8000:8000"
    environment:
      - AZURE_BASE_URL=${AZURE_BASE_URL}
      - AZURE_API_KEY=${AZURE_API_KEY}
      - AZURE_DEPLOYMENT_NAME=${AZURE_DEPLOYMENT_NAME}
      - AZURE_MODEL=${AZURE_MODEL:-flux.1-kontext-pro}
      - AZURE_API_VERSION=${AZURE_API_VERSION:-2025-04-01-preview}
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8000
      - DEFAULT_IMAGE_SIZE=${DEFAULT_IMAGE_SIZE:-1024x1024}
    volumes:
      - ./images:/app/images
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

启动服务：

```bash
# 使用 .env 文件
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 容器管理命令

### 查看容器状态

```bash
docker ps -a | grep azure-image-editor
```

### 查看日志

```bash
# 实时查看日志
docker logs -f azure-image-editor

# 查看最近 100 行日志
docker logs --tail 100 azure-image-editor
```

### 进入容器

```bash
docker exec -it azure-image-editor /bin/bash
```

### 重启容器

```bash
docker restart azure-image-editor
```

### 停止并删除容器

```bash
docker stop azure-image-editor
docker rm azure-image-editor
```

## 健康检查

容器自带健康检查功能，每 30 秒检查一次服务状态：

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' azure-image-editor
```

手动检查服务：

```bash
curl http://localhost:8000/health
```

## 测试 API

### 列出可用工具

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### 生成图片

**重要说明**：在 HTTP 模式下，即使提供了 `output_path` 参数，服务器也会：
1. 将图片保存到服务器的指定路径
2. **同时**将图片的 base64 数据返回给客户端

这样客户端可以接收到图片数据并保存到本地，而不需要通过额外的文件传输。

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "generate_image",
      "arguments": {
        "prompt": "A beautiful sunset over mountains",
        "size": "1024x1024",
        "output_path": "/app/images/sunset.png"
      }
    }
  }'
```

响应示例：
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Image successfully generated. Saved to server at: /app/images/sunset.png"
      },
      {
        "type": "image",
        "data": "iVBORw0KGgoAAAANSUhEUgAA...(base64 encoded image data)",
        "mimeType": "image/png"
      }
    ]
  }
}
```

### 编辑图片

**重要说明**：在 HTTP 模式下，由于服务器无法访问客户端本地文件，需要使用 `image_data_base64` 参数而不是 `image_path`。

**支持的 base64 格式：**
- 纯 base64 字符串：`iVBORw0KGgoAAAANS...`
- Data URL 格式：`data:image/png;base64,iVBORw0KGgoAAAANS...`

```bash
# 方法 1: 使用纯 base64 格式
IMAGE_BASE64=$(base64 -i /path/to/local/image.png)

curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 3,
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"edit_image\",
      \"arguments\": {
        \"image_data_base64\": \"$IMAGE_BASE64\",
        \"prompt\": \"Make this black and white\",
        \"output_path\": \"/app/images/edited.png\"
      }
    }
  }"
```

```bash
# 方法 2: 使用 Data URL 格式（某些工具自动生成此格式）
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "edit_image",
      "arguments": {
        "image_data_base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
        "prompt": "Make this black and white",
        "output_path": "/app/images/edited.png"
      }
    }
  }'
```

响应格式与生成图片相同，包含文本消息和 base64 编码的图片数据。

## 生产环境建议

### 1. 使用 Docker Secrets

对于生产环境，建议使用 Docker secrets 管理敏感信息：

```bash
# 创建 secret
echo "your-api-key" | docker secret create azure_api_key -

# 在 docker-compose.yml 中使用
services:
  azure-image-editor:
    secrets:
      - azure_api_key
    environment:
      - AZURE_API_KEY_FILE=/run/secrets/azure_api_key

secrets:
  azure_api_key:
    external: true
```

### 2. 资源限制

限制容器资源使用：

```yaml
services:
  azure-image-editor:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 3. 使用反向代理

建议在生产环境中使用 Nginx 或 Traefik 作为反向代理：

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - azure-image-editor

  azure-image-editor:
    # ... (same as above)
    expose:
      - "8000"
```

### 4. 日志管理

配置日志轮转：

```yaml
services:
  azure-image-editor:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 故障排查

### 容器无法启动

1. 检查环境变量是否正确配置：
   ```bash
   docker inspect azure-image-editor | grep -A 20 "Env"
   ```

2. 查看启动日志：
   ```bash
   docker logs azure-image-editor
   ```

### 端口冲突

如果 8000 端口被占用，可以映射到其他端口：

```bash
docker run -d -p 9000:8000 ... azure-image-editor-mcp:latest
```

### 权限问题

如果需要保存图片到主机目录，确保目录权限正确：

```bash
mkdir -p images logs
chmod 755 images logs
```

## 镜像优化

### 多阶段构建

如果需要进一步优化镜像大小，可以使用多阶段构建：

```dockerfile
# Builder stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "src/mcp_server_http.py"]
```

### 查看镜像大小

```bash
docker images azure-image-editor-mcp
```

## 更新和维护

### 更新镜像

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker build -t azure-image-editor-mcp:latest .

# 重启容器
docker-compose up -d --build
```

### 清理旧镜像

```bash
docker image prune -f
```

## 安全建议

1. **不要在镜像中硬编码密钥** - 始终使用环境变量或 secrets
2. **定期更新基础镜像** - 保持 Python 和依赖包为最新版本
3. **使用非 root 用户运行** - 在 Dockerfile 中添加用户切换
4. **扫描镜像漏洞** - 使用工具如 `docker scan` 或 `trivy`

```bash
# 扫描镜像漏洞
docker scan azure-image-editor-mcp:latest
```

## 监控和告警

### Prometheus 监控

可以添加 Prometheus 监控端点：

```python
# 在 mcp_server_http.py 中添加 metrics 端点
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

async def handle_metrics(request: Request):
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### 日志聚合

使用 ELK 或 Loki 收集和分析日志：

```yaml
services:
  azure-image-editor:
    logging:
      driver: "loki"
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
```

## 许可证

MIT License
