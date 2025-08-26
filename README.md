# Azure Image Editor MCP Server

[中文](./README_CN.md) | **English**

This is an MCP (Model Context Protocol) server that supports Azure AI Foundry image generation and editing capabilities.

## Features

1. **Text-to-Image Generation** - Generate high-quality images from text descriptions using Azure AI Foundry's FLUX.1-Kontext-pro model
2. **Image Editing** - Edit and modify existing images using AI technology

## Project Structure

```
azure-image-editor/
├── .venv/                        # Python virtual environment
├── src/
│   ├── azure_image_client.py     # Azure API client
│   ├── http_server.py            # General HTTP server
│   └── vscode_http_server.py     # VSCode compatible MCP server (recommended)
├── requirements.txt              # Python dependencies
├── test_azure_client.py          # Azure client tests
├── simple_test.py                # Simplified test script
├── test_http_server.py           # HTTP server tests
└── README.md                     # Project documentation
```

## Installation and Setup

1. **Create virtual environment and install dependencies**:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Configure Azure credentials**:
   - Update `AZURE_CONFIG` configuration in `src/server.py`
   - Include your Azure AI Foundry endpoint URL, API key, and model deployment name

## Usage

### HTTP/MCP Server Mode (Recommended for VSCode)

**Start VSCode compatible HTTP server**:
```bash
source .venv/bin/activate
python src/vscode_http_server.py
```

**Server information**:
- 📍 **Port**: 8000
- 🌐 **Server address**: http://localhost:8000
- 🔧 **Health check**: http://localhost:8000/health
- 📋 **MCP endpoint**: http://localhost:8000/ (supports POST requests)

**VSCode MCP configuration**:
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

### General HTTP API Mode

**Start general HTTP server**:
```bash
source .venv/bin/activate
python src/http_server.py
```

**HTTP endpoints**:
- `GET /` - Server information
- `GET /health` - Health check
- `GET /tools` - Get available tools list
- `POST /mcp` - MCP JSON-RPC interface
- `POST /generate_image` - Direct image generation interface
- `POST /edit_image` - Direct image editing interface

**Test HTTP server**:
```bash
# Test health status
curl http://localhost:8000/health

# Get tools list
curl http://localhost:8000/tools

# Generate image
curl -X POST http://localhost:8000/generate_image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful sunset", "size": "1024x1024"}'
```

### Available MCP Tools

#### 1. generate_image
Generate images from text prompts

**Parameters**:
- `prompt` (required): Text description for image generation
- `size` (optional): Image size, supports "1024x1024", "1792x1024", "1024x1792", default "1024x1024"
- `output_path` (optional): Output file path, returns base64 encoded image data if not provided

**Example**:
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
Edit existing images

**Parameters**:
- `image_path` (required): Path to the image file to edit
- `prompt` (required): Text description of how to edit the image
- `output_path` (optional): Output file path, returns base64 encoded image data if not provided

**Example**:
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

## Testing

### Test Azure client functionality
```bash
source .venv/bin/activate
python simple_test.py
```

### Test stdio mode MCP server
```bash
source .venv/bin/activate
python test_mcp_server.py
```

### Test HTTP server
```bash
# Start HTTP server
source .venv/bin/activate
python src/http_server.py

# Test in another terminal
curl http://localhost:8000/health
curl http://localhost:8000/tools
```

## Technical Specifications

- **Python version**: 3.8+
- **Main dependencies**:
  - `mcp`: MCP protocol support
  - `httpx`: HTTP client
  - `pillow`: Image processing
  - `aiofiles`: Async file operations
  - `pydantic`: Data validation
  - `fastapi`: HTTP server framework
  - `uvicorn`: ASGI server

- **Server modes**:
  - **stdio mode**: Standard MCP protocol, communicates via stdin/stdout
  - **HTTP mode**: REST API + FastAPI, port 8000

- **Azure AI Foundry**:
  - Model: FLUX.1-Kontext-pro
  - API version: 2025-04-01-preview
  - Supported image sizes: 1024x1024, 1792x1024, 1024x1792

## Security Considerations

- Azure API keys should be stored securely, do not commit to code repository
- Recommend using environment variables or configuration files to manage sensitive information
- Image processing may consume significant resources, recommend setting appropriate timeouts and limits

## Troubleshooting

1. **Timeout errors**: Image generation and editing may take longer time, 2-minute timeout is set
2. **API errors**: Check if Azure credentials and endpoint URL are correct
3. **Dependency issues**: Make sure all dependencies are installed in the correct virtual environment

## Development Status

✅ **Completed**:
- Azure AI Foundry integration
- Image generation functionality (tested and working)
- Image editing functionality (basic implementation complete)
- stdio mode MCP server
- HTTP/REST API mode server (port 8000)
- Memory and file output support
- FastAPI integration and API documentation
- Health check and monitoring endpoints

⚠️ **Known issues**:
- Image editing functionality may experience network timeouts in some cases
- Tool list response in stdio mode needs further debugging

✅ **Test status**:
- Image generation functionality: Passed ✅
- HTTP server: Passed ✅ 
- Health check: Passed ✅
- Tool list API: Passed ✅

## License

This project is for learning and testing purposes only. Please comply with Azure AI service terms and conditions.