# Azure Image Editor MCP Server

[中文](./README_CN.md) | **English**

This is an MCP (Model Context Protocol) server that supports Azure AI Foundry image generation and editing capabilities.

## Features

1. **Text-to-Image Generation** - Generate high-quality images from text descriptions using Azure AI Foundry models
2. **Image Editing** - Edit and modify existing images
3. **Configurable Models** - Support for multiple Azure AI models via environment variables

## Demo
Click 👇 to go to the demo on YouTube

[![Using GitHub Copilot & Azure AI Foundry with FLUX 1 Kontext Full Walkthrough for Image Generation Demo](https://img.youtube.com/vi/bnioXb5dd3M/0.jpg)](https://www.youtube.com/watch?v=bnioXb5dd3M)

## Project Structure

```
azure-image-editor/
├── .venv/                        # Python virtual environment
├── src/
│   ├── azure_image_client.py     # Azure API client
│   └── mcp_server.py             # STDIO MCP server
├── tests/                        # Test files
├── logs/                         # Server logs
├── tmp/                          # Temporary files
├── requirements.txt              # Python dependencies
├── .env                          # Environment configuration
├── .env.example                  # Environment configuration template
└── README.md                     # Project documentation
```

## Prerequisites

**⚠️ Important**: Before using this MCP server, you must deploy the required model in your Azure AI Foundry environment.

### Azure AI Foundry Model Deployment

1. **Access Azure AI Foundry**: Go to [Azure AI Foundry](https://ai.azure.com/)
2. **Deploy the model**: Deploy `flux.1-kontext-pro` (or your preferred model) in your Azure AI Foundry workspace
3. **Get deployment details**: Note down your:
   - Base URL (endpoint)
   - API key
   - Deployment name
   - Model name

Without proper model deployment, the MCP server will not function correctly.

## Installation and Setup

1. **Clone and setup environment**:
```bash
git clone https://github.com/satomic/Azure-AI-Image-Editor-MCP.git
cd azure-image-editor
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Configure VSCode MCP

Add the following to your VSCode MCP configuration:

```json
{
  "servers": {
    "azure-image-editor": {
      "command": "/full/path/to/.venv/bin/python",
      "args": ["/full/path/to/azure-image-editor/src/mcp_server.py"],
      "env": {
        "AZURE_BASE_URL": "https://your-endpoint.services.ai.azure.com", // deployment endpoint
        "AZURE_API_KEY": "${input:azure-api-key}",
        "AZURE_DEPLOYMENT_NAME": "FLUX.1-Kontext-pro", // The name you gave your deployment
        "AZURE_MODEL": "flux.1-kontext-pro", // Default model
        "AZURE_API_VERSION": "2025-04-01-preview" // Default API version
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

**Important**: Replace `/full/path/to/` with the actual absolute path to this project directory.

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
- `image_path` (required): Path to the image file to edit
- `prompt` (required): English text description of how to edit the image
- `size` (optional): Output image size, uses original dimensions if not specified
- `output_path` (optional): Output file path, returns base64 encoded image if not provided

**Example**:
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

## Technical Specifications

- **Python version**: 3.8+
- **Main dependencies**:
  - `mcp`: MCP protocol support
  - `httpx`: HTTP client with timeout handling
  - `pillow`: Image processing and dimension detection
  - `aiofiles`: Async file operations
  - `pydantic`: Data validation
  - `python-dotenv`: Environment variable management

- **Azure AI Foundry**:
  - Default model: flux.1-kontext-pro (configurable)
  - Default API version: 2025-04-01-preview (configurable)
  - Supported image sizes: 1024x1024, 1792x1024, 1024x1792
  - Timeout: 5 minutes per request

## Troubleshooting

1. **Timeout Errors**: Image processing has 5-minute timeout, check network connectivity  
2. **API Errors**: Verify Azure credentials and endpoint URL
3. **Dependency Issues**: Ensure virtual environment is activated and dependencies installed
4. **Server Connection Issues**: Verify VSCode MCP configuration path is correct

## License
MIT License