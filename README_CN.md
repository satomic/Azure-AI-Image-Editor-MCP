# Azure Image Editor MCP Server

**中文** | [English](./README.md)

这是一个支持Azure AI Foundry图片生成和编辑功能的MCP (Model Context Protocol) 服务器。

## 功能特性

1. **文字生成图片** - 使用Azure AI Foundry模型从文字描述生成高质量图片
2. **智能图片编辑** - 编辑和修改现有图片，支持智能尺寸保持
3. **全面审计追踪** - 完整的请求/响应日志记录和图片存档
4. **可配置模型** - 通过环境变量支持多种Azure AI模型

## 项目结构

```
azure-image-editor/
├── .venv/                        # Python虚拟环境
├── src/
│   ├── azure_image_client.py     # Azure API客户端
│   └── http_server.py            # HTTP MCP服务器
├── tests/                        # 测试文件
├── logs/                         # 服务器日志
├── audit/                        # 审计日志和图片
├── tmp/                          # 临时文件
├── requirements.txt              # Python依赖
├── .env                          # 环境配置
├── .env.example                  # 环境配置模板
└── README.md                     # 项目文档
```

## 安装和设置

1. **克隆和设置环境**：
```bash
git clone <repository-url>
cd azure-image-editor
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或者 .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **配置环境变量**：
```bash
# 复制示例配置
cp .env.example .env

# 使用你喜欢的编辑器编辑.env文件
nano .env  # 或使用其他编辑器
```

## 配置

### 必需的环境变量

```bash
# Azure AI Foundry 配置
AZURE_BASE_URL=https://your-endpoint.services.ai.azure.com
AZURE_API_KEY=your-api-key-here
AZURE_DEPLOYMENT_NAME=your-deployment-name
```

### 可选的环境变量

```bash
# 模型配置
AZURE_MODEL=flux.1-kontext-pro  # 默认模型

# 服务器配置
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
DEFAULT_IMAGE_SIZE=1024x1024
```

## 使用方法

### 启动服务器

```bash
source .venv/bin/activate
python src/http_server.py
```

**服务器信息**：
- 📍 **端口号**: 8000（可配置）
- 🌐 **服务器地址**: http://localhost:8000
- 🔧 **健康检查**: http://localhost:8000/health
- 📋 **MCP端点**: http://localhost:8000/（支持POST请求）

**VSCode MCP配置**：
```json
{
  "servers": {
    "azure-image-editor": {
      "url": "http://localhost:8000",
      "type": "http"
    }
  },
  "inputs": []
}
```

### 可用的MCP工具

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
- `image_data`（必需）：Base64编码的图片数据
- `prompt`（必需）：描述如何编辑图片的英文文字提示
- `size`（可选）：输出图片尺寸，如果未指定则使用原图尺寸
- `output_path`（可选）：输出文件路径，如果不提供则返回base64编码的图片

**示例**：
```json
{
  "name": "edit_image",
  "arguments": {
    "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "prompt": "Make this black and white",
    "output_path": "/path/to/output/edited_image.png"
  }
}
```

## 审计日志

每个请求都会在`audit/`目录中创建全面的审计追踪：

```
audit/
└── 20250826_143052_a1b2c3d4_anonymous_generate_image/
    ├── request.json      # 完整的请求数据
    ├── response.json     # 完整的响应数据
    └── result.png        # 生成的图片
    # 或者 output_filename.png 如果指定了 output_path
```

对于编辑操作，输入和输出图片都会被存档：
```
audit/
└── 20250826_143052_a1b2c3d4_anonymous_edit_image/
    ├── request.json
    ├── response.json
    ├── input_base64_data.png     # 来自base64的原始输入图片
    ├── result.png               # 编辑结果（未指定output_path时）
    └── output_edited.jpg        # 编辑结果（指定output_path时）
```

### 审计文件命名规则：
- **输入文件**: `input_base64_data.png`
- **结果文件（无output_path）**: `result.png`
- **输出文件（有output_path）**: `output_{文件名}`

## 测试

### 测试HTTP服务器
```bash
# 健康检查
curl http://localhost:8000/health

# 获取工具列表  
curl http://localhost:8000 -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

### 运行测试套件
```bash
source .venv/bin/activate
python tests/comprehensive_test.py
python tests/test_http_server.py
```

## 技术规格

- **Python版本**: 3.8+
- **主要依赖**:
  - `mcp`: MCP协议支持
  - `httpx`: HTTP客户端，支持超时处理
  - `pillow`: 图片处理和尺寸检测
  - `aiofiles`: 异步文件操作
  - `pydantic`: 数据验证
  - `fastapi`: HTTP服务器框架
  - `uvicorn`: ASGI服务器

- **Azure AI Foundry**:
  - 默认模型: flux.1-kontext-pro（可配置）
  - API版本: 2025-04-01-preview
  - 支持的图片尺寸: 1024x1024, 1792x1024, 1024x1792
  - 超时时间: 每个请求5分钟

## 安全功能

1. **审计日志**：完整的请求/响应跟踪
2. **输入验证**：仅限英文提示，尺寸验证
3. **错误处理**：全面的错误日志和用户反馈
4. **资源管理**：超时控制和内存限制

## 最新更新

### 版本 2.0 功能
✅ **图片尺寸保持**：编辑操作保持原图尺寸，除非另有指定
✅ **可配置模型**：通过环境变量选择Azure模型
✅ **全面审计**：请求/响应日志记录和图片存档

### 更新日志
- **v2.0**: 添加智能尺寸保持、可配置模型和全面审计日志
- **v1.0**: 基础图片生成和编辑功能

## 故障排除

1. **超时错误**：图片处理有5分钟超时，请检查网络连接
2. **API错误**：验证Azure凭据和端点URL
3. **依赖问题**：确保虚拟环境已激活且依赖已安装
4. **审计错误**：检查`audit/`目录的写入权限

## 许可证

此项目仅供学习和测试使用。请遵守Azure AI服务的使用条款和条件。