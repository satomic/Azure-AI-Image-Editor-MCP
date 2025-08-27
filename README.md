# Azure Image Editor MCP Server

[中文](./README_CN.md) | **English**

This is an MCP (Model Context Protocol) server that supports Azure AI Foundry image generation and editing capabilities.

## Features

1. **Text-to-Image Generation** - Generate high-quality images from text descriptions using Azure AI Foundry models
2. **Image Editing** - Edit and modify existing images with intelligent dimension preservation
3. **Comprehensive Audit Trail** - Complete request/response logging with image archiving
4. **Configurable Models** - Support for multiple Azure AI models via environment variables

## Project Structure

```
azure-image-editor/
├── .venv/                        # Python virtual environment
├── src/
│   ├── azure_image_client.py     # Azure API client
│   └── http_server.py            # HTTP MCP server
├── tests/                        # Test files
├── logs/                         # Server logs
├── audit/                        # Audit logs and images
├── tmp/                          # Temporary files
├── requirements.txt              # Python dependencies
├── .env                          # Environment configuration
├── .env.example                  # Environment configuration template
└── README.md                     # Project documentation
```

## Installation and Setup

1. **Clone and setup environment**:
```bash
git clone <repository-url>
cd azure-image-editor
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Configure environment variables**:
```bash
# Copy example configuration
cp .env.example .env

# Edit .env file with your Azure credentials
nano .env  # or use your preferred editor
```

## Configuration

### Required Environment Variables

```bash
# Azure AI Foundry Configuration
AZURE_BASE_URL=https://your-endpoint.services.ai.azure.com
AZURE_API_KEY=your-api-key-here
AZURE_DEPLOYMENT_NAME=your-deployment-name
```

### Optional Environment Variables

```bash
# Model Configuration
AZURE_MODEL=flux.1-kontext-pro  # Default model

# Server Configuration
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
DEFAULT_IMAGE_SIZE=1024x1024
```

## Usage

### Start the Server

```bash
source .venv/bin/activate
python src/http_server.py
```

**Server Information**:
- 📍 **Port**: 8000 (configurable)
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

### Available MCP Tools

#### 1. generate_image
Generate images from text prompts

**Parameters**:
- `prompt` (required): English text description for image generation
- `size` (optional): Image size - "1024x1024", "1792x1024", "1024x1792", default: "1024x1024"
- `output_path` (optional): Output file path, returns base64 encoded image if not provided

**Example**:
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
Edit existing images with intelligent dimension preservation

**Parameters**:
- `image_data` (required): Base64 encoded image data
- `prompt` (required): English text description of how to edit the image
- `size` (optional): Output image size, uses original dimensions if not specified
- `output_path` (optional): Output file path, returns base64 encoded image if not provided

**Example**:
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

## Audit Logging

Every request creates a comprehensive audit trail in the `audit/` directory:

```
audit/
└── 20250826_143052_a1b2c3d4_anonymous_generate_image/
    ├── request.json      # Complete request data
    ├── response.json     # Complete response data
    └── result.png        # Generated image
    # OR output_filename.png if output_path was specified
```

For edit operations, both input and output images are always archived:
```
audit/
└── 20250826_143052_a1b2c3d4_anonymous_edit_image/
    ├── request.json
    ├── response.json
    ├── input_base64_data.png     # Original input image from base64
    ├── result.png               # Edited result (when no output_path)
    └── output_edited.jpg        # Edited result (when output_path specified)
```

### Audit File Naming Convention:
- **Input files**: `input_base64_data.png`
- **Result files (no output_path)**: `result.png`
- **Output files (with output_path)**: `output_{filename}`

## Testing

### Test HTTP Server
```bash
# Health check
curl http://localhost:8000/health

# Get tools list  
curl http://localhost:8000 -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

### Run Test Suite
```bash
source .venv/bin/activate
python tests/comprehensive_test.py
python tests/test_http_server.py
```

## Technical Specifications

- **Python version**: 3.8+
- **Main dependencies**:
  - `mcp`: MCP protocol support
  - `httpx`: HTTP client with timeout handling
  - `pillow`: Image processing and dimension detection
  - `aiofiles`: Async file operations
  - `pydantic`: Data validation
  - `fastapi`: HTTP server framework
  - `uvicorn`: ASGI server

- **Azure AI Foundry**:
  - Default model: flux.1-kontext-pro (configurable)
  - API version: 2025-04-01-preview
  - Supported image sizes: 1024x1024, 1792x1024, 1024x1792
  - Timeout: 5 minutes per request

## Security Features

1. **Audit Logging**: Complete request/response tracking
2. **Input Validation**: English-only prompts, size validation
3. **Error Handling**: Comprehensive error logging and user feedback
4. **Resource Management**: Timeout controls and memory limits

## Recent Updates

### Version 2.0 Features
✅ **Image Dimension Preservation**: Edit operations maintain original dimensions unless specified
✅ **Configurable Models**: Environment variable for Azure model selection  
✅ **Comprehensive Auditing**: Request/response logging with image archiving

### Changelog
- **v2.0**: Added intelligent dimension preservation, configurable models, and comprehensive audit logging
- **v1.0**: Basic image generation and editing functionality

## Troubleshooting

1. **Timeout Errors**: Image processing has 5-minute timeout, check network connectivity  
2. **API Errors**: Verify Azure credentials and endpoint URL
3. **Dependency Issues**: Ensure virtual environment is activated and dependencies installed
4. **Audit Errors**: Check write permissions for `audit/` directory

## License

This project is for learning and testing purposes only. Please comply with Azure AI service terms and conditions.