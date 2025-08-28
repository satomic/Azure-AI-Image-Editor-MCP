# Azure Image Editor MCP Server

[中文](./README_CN.md) | **English**

This is an MCP (Model Context Protocol) server that supports Azure AI Foundry image generation and editing capabilities.

## Features

1. **Text-to-Image Generation** - Generate high-quality images from text descriptions using Azure AI Foundry models
2. **Image Editing** - Edit and modify existing images
3. **Configurable Models** - Support for multiple Azure AI models via environment variables

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

# API Version
AZURE_API_VERSION=2025-04-01-preview  # Default API version

# Image Settings
DEFAULT_IMAGE_SIZE=1024x1024
```

## Usage

### Configure VSCode MCP

Add the following to your VSCode MCP configuration:

```json
{
  "servers": {
    "azure-image-editor": {
      "command": "python",
      "args": ["/full/path/to/azure-image-editor/src/mcp_server.py"],
      "env": {}
    }
  }
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

## Testing

### Test the MCP Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Test the server (requires VSCode MCP or another MCP client)
python src/mcp_server.py
```

The server will start and wait for MCP client connections through STDIO.

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

This project is for learning and testing purposes only. Please comply with Azure AI service terms and conditions.