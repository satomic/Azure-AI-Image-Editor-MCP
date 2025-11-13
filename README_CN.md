# Azure Image Editor MCP Server

**中文** | [English](./README.md)

这是一个支持Azure AI Foundry图片生成和编辑功能的MCP (Model Context Protocol) 服务器。

## 功能特性

1. **文字生成图片** - 使用Azure AI Foundry模型从文字描述生成高质量图片
2. **智能图片编辑** - 编辑和修改现有图片
3. **可配置模型** - 通过环境变量支持多种Azure AI模型

## Demo
点击👇查看YouTube上的demo

[![Using GitHub Copilot & Azure AI Foundry with FLUX 1 Kontext Full Walkthrough for Image Generation Demo](https://img.youtube.com/vi/bnioXb5dd3M/0.jpg)](https://www.youtube.com/watch?v=bnioXb5dd3M)


## 项目结构

```
azure-image-editor/
├── .venv/                        # Python虚拟环境
├── src/
│   ├── azure_image_client.py     # Azure API客户端
│   ├── mcp_server.py             # STDIO MCP服务器
│   └── mcp_server_http.py        # HTTP/JSON-RPC MCP服务器
├── tests/                        # 测试文件
├── logs/                         # 服务器日志
├── tmp/                          # 临时文件
├── requirements.txt              # Python依赖
├── .env                          # 环境配置
├── .env.example                  # 环境配置模板
└── README.md                     # 项目文档
```

## 先决条件

**⚠️ 重要**：在使用此MCP服务器之前，您必须在Azure AI Foundry环境中部署所需的模型。

### Azure AI Foundry模型部署

1. **访问Azure AI Foundry**：前往 [Azure AI Foundry](https://ai.azure.com/)
2. **部署模型**：在您的Azure AI Foundry工作区中部署 `flux.1-kontext-pro`（或您偏好的其他模型）
3. **获取部署详情**：记录以下信息：
   - 基础URL（端点）
   - API密钥
   - 部署名称
   - 模型名称

如果没有正确部署模型，MCP服务器将无法正常工作。

## 安装和设置

1. **克隆和设置环境**：
```bash
git clone https://github.com/satomic/Azure-AI-Image-Editor-MCP.git
cd azure-image-editor
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或者 .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 服务器模式

本项目支持两种 MCP 服务器模式：

### 1. STDIO 模式（默认）
通过标准输入输出通信，适合 VSCode 集成。

### 2. HTTP/JSON-RPC 模式
通过 HTTP 和 JSON-RPC 2.0 协议通信，适合 Web 应用和远程访问。

## 配置说明

### 配置 STDIO 模式（VSCode MCP）

在VSCode MCP配置中添加：

```json
{
  "servers": {
    "azure-image-editor": {
      "command": "/full/path/to/.venv/bin/python", 
      "args": ["/full/path/to/azure-image-editor/src/mcp_server.py"],
      "env": {
        "AZURE_BASE_URL": "https://your-endpoint.services.ai.azure.com", // 部署端点
        "AZURE_API_KEY": "${input:azure-api-key}",
        "AZURE_DEPLOYMENT_NAME": "FLUX.1-Kontext-pro", // 部署指定的名称
        "AZURE_MODEL": "flux.1-kontext-pro", // 默认模型
        "AZURE_API_VERSION": "2025-04-01-preview" // 默认API版本
      }
    }
  },
  "inputs": [
    {
      "id": "azure-api-key",
      "type": "promptString",
      "description": "Enter your Azure API Key",
      "password": "true"
    }
  ]
}
```

**重要**：将 `/完整路径/到/` 替换为项目目录的实际绝对路径。

### 配置 HTTP/JSON-RPC 模式

#### 方法 1：使用环境变量直接运行

```bash
# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或者 .venv\Scripts\activate  # Windows

# 设置环境变量
export AZURE_BASE_URL="https://your-endpoint.services.ai.azure.com"
export AZURE_API_KEY="your-api-key"
export AZURE_DEPLOYMENT_NAME="FLUX.1-Kontext-pro"
export AZURE_MODEL="flux.1-kontext-pro"
export AZURE_API_VERSION="2025-04-01-preview"

# 可选：配置服务器主机和端口（默认为 127.0.0.1:8000）
export MCP_SERVER_HOST="0.0.0.0"  # 监听所有网络接口
export MCP_SERVER_PORT="8000"      # 服务器端口

# 启动 HTTP 服务器
python src/mcp_server_http.py
```

#### 方法 2：使用 .env 文件

在项目根目录创建 `.env` 文件：

```bash
AZURE_BASE_URL=https://your-endpoint.services.ai.azure.com
AZURE_API_KEY=your-api-key
AZURE_DEPLOYMENT_NAME=FLUX.1-Kontext-pro
AZURE_MODEL=flux.1-kontext-pro
AZURE_API_VERSION=2025-04-01-preview

# 可选的服务器配置
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
DEFAULT_IMAGE_SIZE=1024x1024
```

然后启动服务器：

```bash
source .venv/bin/activate
python src/mcp_server_http.py
```

#### 服务器端点

当 HTTP 服务器运行时，以下端点可用：

- **JSON-RPC 端点**: `http://127.0.0.1:8000/` - 主要的 JSON-RPC 2.0 端点（POST）
- **健康检查**: `http://127.0.0.1:8000/health` - 服务器健康状态（GET）

#### 连接到 HTTP 服务器

**使用 VSCode MCP 客户端：**

```json
{
  "servers": {
    "azure-image-editor-http": {
      "type": "http",
      "url": "http://127.0.0.1:8000"
    }
  }
}
```

**使用 curl：**

```bash
# 列出可用工具
curl -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

# 调用生成图片工具
curl -X POST http://127.0.0.1:8000/ \
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
        "output_path": "./images/sunset.png"
      }
    }
  }'
```

## 可用的MCP工具

#### 1. generate_image
从文字提示生成图片

**参数**：
- `prompt`（必需）：用于生成图片的英文文字描述
- `size`（可选）：图片尺寸 - "1024x1024"、"1792x1024"、"1024x1792"，默认："1024x1024"
- `output_path`（可选）：输出文件路径，如果不提供则返回base64编码的图片

**示例**：
```json
{
  "name": "generate_image",
  "arguments": {
    "prompt": "A beautiful sunset over mountains",
    "size": "1024x1024",
    "output_path": "/path/to/output/image.png"
  }
}
```

#### 2. edit_image
使用智能尺寸保持功能编辑现有图片

**参数**：
- `image_path`（必需）：要编辑的图片文件路径
- `prompt`（必需）：描述如何编辑图片的英文文字提示
- `size`（可选）：输出图片尺寸，如果未指定则使用原图尺寸
- `output_path`（可选）：输出文件路径，如果不提供则返回base64编码的图片

**示例**：
```json
{
  "name": "edit_image",
  "arguments": {
    "image_path": "/path/to/input/image.png",
    "prompt": "Make this black and white",
    "output_path": "/path/to/output/edited_image.png"
  }
}
```

## 技术规格

- **Python版本**: 3.8+
- **主要依赖**:
  - `mcp`: MCP协议支持
  - `httpx`: HTTP客户端，支持超时处理
  - `pillow`: 图片处理和尺寸检测
  - `aiofiles`: 异步文件操作
  - `pydantic`: 数据验证
  - `python-dotenv`: 环境变量管理
  - `starlette`: ASGI 框架，用于 HTTP 服务器（仅 HTTP 模式）
  - `uvicorn`: ASGI 服务器（仅 HTTP 模式）

- **Azure AI Foundry**:
  - 默认模型: flux.1-kontext-pro（可配置）
  - 默认API版本: 2025-04-01-preview（可配置）
  - 支持的图片尺寸: 1024x1024, 1792x1024, 1024x1792
  - 超时时间: 每个请求5分钟

## 故障排除

1. **超时错误**：图片处理有5分钟超时，请检查网络连接
2. **API错误**：验证Azure凭据和端点URL
3. **依赖问题**：确保虚拟环境已激活且依赖已安装
4. **服务器连接问题**：验证VSCode MCP配置路径是否正确

## 许可证
MIT License