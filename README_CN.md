# Azure Image Editor MCP Server

**中文** | [English](./README.md)

这是一个支持Azure AI Foundry图片生成和编辑功能的MCP (Model Context Protocol) 服务器。

## 功能特性

1. **文字生成图片** - 使用Azure AI Foundry的FLUX.1-Kontext-pro模型从文字描述生成高质量图片
2. **图片编辑** - 使用AI技术对现有图片进行编辑和修改

## 项目结构

```
azure-image-editor/
├── .venv/                        # Python虚拟环境
├── src/
│   ├── azure_image_client.py     # Azure API客户端
│   ├── http_server.py            # 通用HTTP服务器
│   └── vscode_http_server.py     # VSCode兼容的MCP服务器 (推荐)
├── requirements.txt              # Python依赖
├── test_azure_client.py          # Azure客户端测试
├── simple_test.py                # 简化测试脚本
├── test_http_server.py           # HTTP服务器测试
└── README.md                     # 项目文档
```

## 安装和设置

1. **创建虚拟环境并安装依赖**：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或者 .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **配置Azure凭据**：
   - 在 `src/server.py` 中更新 `AZURE_CONFIG` 配置
   - 包含你的Azure AI Foundry端点URL、API密钥和模型部署名称

## 使用方法

### HTTP/MCP服务器模式 (推荐用于VSCode)

**启动VSCode兼容的HTTP服务器**：
```bash
source .venv/bin/activate
python src/vscode_http_server.py
```

**服务器信息**：
- 📍 **端口号**: 8000
- 🌐 **服务器地址**: http://localhost:8000
- 🔧 **健康检查**: http://localhost:8000/health
- 📋 **MCP端点**: http://localhost:8000/ (支持POST请求)

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

### 通用HTTP API模式

**启动通用HTTP服务器**：
```bash
source .venv/bin/activate
python src/http_server.py
```

**HTTP端点**：
- `GET /` - 服务器信息
- `GET /health` - 健康检查
- `GET /tools` - 获取可用工具列表
- `POST /mcp` - MCP JSON-RPC接口
- `POST /generate_image` - 直接图片生成接口
- `POST /edit_image` - 直接图片编辑接口

**测试HTTP服务器**：
```bash
# 测试健康状态
curl http://localhost:8000/health

# 获取工具列表
curl http://localhost:8000/tools

# 生成图片
curl -X POST http://localhost:8000/generate_image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful sunset", "size": "1024x1024"}'
```

### 可用的MCP工具

#### 1. generate_image
生成图片从文字提示

**参数**：
- `prompt` (必需): 用于生成图片的文字描述
- `size` (可选): 图片尺寸，支持 "1024x1024", "1792x1024", "1024x1792"，默认 "1024x1024"
- `output_path` (可选): 输出文件路径，如果不提供将返回base64编码的图片数据

**示例**：
```json
{
  "name": "generate_image",
  "arguments": {
    "prompt": "A beautiful sunset over a mountain landscape",
    "size": "1024x1024",
    "output_path": "/path/to/output/image.png"
  }
}
```

#### 2. edit_image
编辑现有图片

**参数**：
- `image_path` (必需): 要编辑的图片文件路径
- `prompt` (必需): 描述如何编辑图片的文字提示
- `output_path` (可选): 输出文件路径，如果不提供将返回base64编码的图片数据

**示例**：
```json
{
  "name": "edit_image",
  "arguments": {
    "image_path": "/path/to/input/image.png",
    "prompt": "Make this image black and white",
    "output_path": "/path/to/output/edited_image.png"
  }
}
```

## 测试

### 测试Azure客户端功能
```bash
source .venv/bin/activate
python simple_test.py
```

### 测试stdio模式MCP服务器
```bash
source .venv/bin/activate
python test_mcp_server.py
```

### 测试HTTP服务器
```bash
# 启动HTTP服务器
source .venv/bin/activate
python src/http_server.py

# 在另一个终端测试
curl http://localhost:8000/health
curl http://localhost:8000/tools
```

## 技术规格

- **Python版本**: 3.8+
- **主要依赖**:
  - `mcp`: MCP协议支持
  - `httpx`: HTTP客户端
  - `pillow`: 图片处理
  - `aiofiles`: 异步文件操作
  - `pydantic`: 数据验证
  - `fastapi`: HTTP服务器框架
  - `uvicorn`: ASGI服务器

- **服务器模式**:
  - **stdio模式**: 标准MCP协议，通过stdin/stdout通信
  - **HTTP模式**: REST API + FastAPI，端口8000

- **Azure AI Foundry**:
  - 模型: FLUX.1-Kontext-pro
  - API版本: 2025-04-01-preview
  - 支持的图片尺寸: 1024x1024, 1792x1024, 1024x1792

## 安全注意事项

- Azure API密钥应当安全存储，不要提交到代码仓库
- 建议使用环境变量或配置文件来管理敏感信息
- 图片处理可能消耗大量资源，建议设置适当的超时和限制

## 故障排除

1. **超时错误**: 图片生成和编辑可能需要较长时间，已设置2分钟超时
2. **API错误**: 检查Azure凭据和端点URL是否正确
3. **依赖问题**: 确保在正确的虚拟环境中安装了所有依赖

## 开发状态

✅ **已完成**:
- Azure AI Foundry集成
- 图片生成功能 (已测试通过)
- 图片编辑功能 (基础实现完成)
- stdio模式MCP服务器
- HTTP/REST API模式服务器 (端口8000)
- 内存和文件输出支持
- FastAPI集成和API文档
- 健康检查和监控端点

⚠️ **已知问题**:
- 图片编辑功能在某些情况下可能出现网络超时
- stdio模式的工具列表响应需要进一步调试

✅ **测试状态**:
- 图片生成功能: 通过 ✅
- HTTP服务器: 通过 ✅ 
- 健康检查: 通过 ✅
- 工具列表API: 通过 ✅

## 许可证

此项目仅供学习和测试使用。请遵守Azure AI服务的使用条款和条件。