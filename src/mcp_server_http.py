#!/usr/bin/env python3
"""
Azure Image Editor MCP Server - HTTP Version

A MCP server that supports Azure AI Foundry image generation and editing capabilities.
This version uses HTTP with JSON-RPC for communication.
"""

import asyncio
import base64
import os
import sys
import logging
import json
from datetime import datetime
from typing import Any
from pathlib import Path

try:
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse, Response
    from starlette.requests import Request
    import uvicorn
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: Required dependency missing: {e}", file=sys.stderr)
    print("Please install required packages: pip install python-dotenv starlette uvicorn", file=sys.stderr)
    sys.exit(1)

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from azure_image_client import AzureImageGenerator
except ImportError as e:
    print(f"Error: Cannot import azure_image_client: {e}", file=sys.stderr)
    print("Please ensure azure_image_client.py is in the same directory", file=sys.stderr)
    sys.exit(1)

# Load environment variables
load_dotenv()

# Set up logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"mcp_server_http_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stderr)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


def get_azure_config():
    """Get Azure configuration from environment variables"""
    try:
        required_vars = {
            "AZURE_BASE_URL": "Base URL for Azure AI service",
            "AZURE_API_KEY": "API key for Azure AI service", 
            "AZURE_DEPLOYMENT_NAME": "Deployment model name"
        }
        
        missing_vars = []
        config = {}
        
        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            if not value or not value.strip():
                missing_vars.append(f"{var_name} ({description})")
            else:
                key_map = {
                    "AZURE_BASE_URL": "base_url",
                    "AZURE_API_KEY": "api_key",
                    "AZURE_DEPLOYMENT_NAME": "deployment_name"
                }
                config[key_map[var_name]] = value.strip()
        
        # Handle optional variables
        model_value = os.getenv("AZURE_MODEL")
        config["model"] = model_value.strip() if model_value and model_value.strip() else "flux.1-kontext-pro"
        
        api_version_value = os.getenv("AZURE_API_VERSION")
        config["api_version"] = api_version_value.strip() if api_version_value and api_version_value.strip() else "2025-04-01-preview"
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Basic validation
        if not config["base_url"].startswith(("http://", "https://")):
            raise ValueError("AZURE_BASE_URL must be a valid HTTP/HTTPS URL")
        
        if len(config["api_key"]) < 10:
            raise ValueError("AZURE_API_KEY is too short, please check if the API key is correct")
        
        if not config["deployment_name"]:
            raise ValueError("AZURE_DEPLOYMENT_NAME cannot be empty")
        
        logger.info("Azure configuration loaded successfully")
        return config
        
    except ValueError:
        raise
    except Exception as e:
        error_msg = f"Error loading Azure configuration: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def is_english_text(text: str) -> bool:
    """Check if text is primarily in English"""
    if not text.strip():
        return True
    
    # Check if it contains CJK characters
    for char in text:
        if '\u4e00' <= char <= '\u9fff' or \
           '\u3040' <= char <= '\u309f' or \
           '\u30a0' <= char <= '\u30ff' or \
           '\uac00' <= char <= '\ud7af':
            return False
    
    return True


def validate_image_size(size: str) -> bool:
    """Validate image size format"""
    supported_sizes = ["1024x1024", "1792x1024", "1024x1792"]
    return size in supported_sizes


async def get_tools_list():
    """Get list of available tools"""
    default_size = os.getenv("DEFAULT_IMAGE_SIZE", "1024x1024")
    
    return {
        "tools": [
            {
                "name": "generate_image",
                "description": "Generate images from text prompts using Azure AI Foundry (English prompts only)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "English description for image generation",
                        },
                        "size": {
                            "type": "string",
                            "description": f"Image size, supports 1024x1024, 1792x1024, 1024x1792, default: {default_size}",
                            "default": default_size,
                            "enum": ["1024x1024", "1792x1024", "1024x1792"]
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional: output file path (for server-side save). Image data is always returned to client."
                        }
                    },
                    "required": ["prompt", "size"]
                },
            },
            {
                "name": "edit_image",
                "description": "Edit an existing image with intelligent dimension preservation. Upload image data using base64 encoding.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_data_base64": {
                            "type": "string",
                            "description": "Base64 encoded image data. Supports both raw base64 (iVBORw0K...) and Data URL format (data:image/png;base64,iVBORw0K...)"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "English description of how to edit the image"
                        },
                        "size": {
                            "type": "string",
                            "description": "Optional size for edited image, if not specified uses original image dimensions",
                            "enum": ["1024x1024", "1792x1024", "1024x1792"]
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional: output file path (for server-side save). Image data is always returned to client."
                        }
                    },
                    "required": ["image_data_base64", "prompt"]
                },
            }
        ]
    }


async def call_tool(name: str, arguments: dict[str, Any]):
    """Call a tool by name with arguments"""
    try:
        if name == "generate_image":
            return await handle_generate_image(arguments or {})
        elif name == "edit_image":
            return await handle_edit_image(arguments or {})
        else:
            return {
                "content": [
                    {"type": "text", "text": f"Error: Unknown tool '{name}'"}
                ]
            }
            
    except Exception as e:
        error_msg = f"Unexpected error in tool '{name}': {str(e)}"
        logger.error(error_msg)
        return {"content": [{"type": "text", "text": error_msg}]}


async def handle_generate_image(arguments: dict[str, Any]):
    """Handle image generation request"""
    try:
        prompt = arguments.get("prompt", "")
        size = arguments.get("size", os.getenv("DEFAULT_IMAGE_SIZE", "1024x1024"))
        output_path = arguments.get("output_path")
        
        logger.info(f"Image generation request: prompt='{prompt}', size={size}, output_path={output_path}")
        
        # Get Azure configuration
        try:
            azure_config = get_azure_config()
        except (ValueError, Exception) as e:
            error_msg = f"Azure configuration error: {str(e)}"
            logger.error(f"Failed to get Azure configuration: {error_msg}")
            return {"content": [{"type": "text", "text": error_msg}]}
        
        # Validate prompt is in English
        if not is_english_text(prompt):
            error_msg = "Prompt must be in English. Please use English to describe the image you want to generate."
            logger.warning(f"Non-English prompt rejected: '{prompt}'")
            return {"content": [{"type": "text", "text": error_msg}]}
        
        # Validate image size
        if not validate_image_size(size):
            error_msg = f"Unsupported image size: {size}. Supported sizes: 1024x1024, 1792x1024, 1024x1792"
            logger.warning(f"Invalid image size: {size}")
            return {"content": [{"type": "text", "text": error_msg}]}
        
        async with AzureImageGenerator(
            base_url=azure_config["base_url"],
            api_key=azure_config["api_key"],
            deployment_name=azure_config["deployment_name"],
            model=azure_config["model"],
            api_version=azure_config["api_version"]
        ) as generator:
            
            # In HTTP mode, always get image bytes for return to client
            # If output_path is provided, also save to server
            result = await generator.generate_image(
                prompt=prompt,
                size=size,
                output_path=output_path
            )
            
            # HTTP mode: always return image data to client
            if output_path:
                # Image was saved to file, read it back
                import aiofiles
                async with aiofiles.open(output_path, 'rb') as f:
                    image_bytes = await f.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                logger.info(f"Image saved to server at: {result} and returning to client (size: {len(image_bytes)} bytes)")
                return {
                    "content": [
                        {"type": "text", "text": f"Image successfully generated. Saved to server at: {result}"},
                        {"type": "image", "data": image_b64, "mimeType": "image/png"}
                    ]
                }
            else:
                # result is bytes
                image_b64 = base64.b64encode(result).decode('utf-8')
                logger.info(f"Image generation successful, returning base64 data (size: {len(result)} bytes)")
                return {
                    "content": [
                        {"type": "text", "text": f"Image generation successful, prompt: '{prompt}', size: {size}"},
                        {"type": "image", "data": image_b64, "mimeType": "image/png"}
                    ]
                }
                
    except Exception as e:
        error_msg = f"Error generating image: {str(e)}"
        logger.error(f"Image generation failed: {error_msg}")
        return {"content": [{"type": "text", "text": error_msg}]}


async def handle_edit_image(arguments: dict[str, Any]):
    """Handle image editing request"""
    try:
        image_data_base64 = arguments.get("image_data_base64")
        prompt = arguments.get("prompt", "") + " (and all other elements exactly the same)"
        size = arguments.get("size")  # Optional size override
        output_path = arguments.get("output_path")
        
        # Validate input parameters - image_data_base64 is required in HTTP mode
        if not image_data_base64:
            error_msg = "'image_data_base64' parameter is required in HTTP mode"
            logger.error(error_msg)
            return {"content": [{"type": "text", "text": error_msg}]}
        
        logger.info(f"Image editing request: prompt='{prompt}', has_base64=True, output_path={output_path}")
        
        # Get Azure configuration
        try:
            azure_config = get_azure_config()
        except (ValueError, Exception) as e:
            error_msg = f"Azure configuration error: {str(e)}"
            logger.error(f"Failed to get Azure configuration: {error_msg}")
            return {"content": [{"type": "text", "text": error_msg}]}
        
        # Validate prompt is in English
        if not is_english_text(prompt):
            error_msg = "Prompt must be in English. Please use English to describe how you want to edit the image."
            logger.warning(f"Non-English prompt rejected: '{prompt}'")
            return {"content": [{"type": "text", "text": error_msg}]}
        
        # Prepare image data for processing
        import tempfile
        temp_input_path = None
        
        try:
            # Decode base64 data and save to temporary file
            try:
                # Handle Data URL format (e.g., "data:image/png;base64,...")
                base64_data = image_data_base64.strip()
                if base64_data.startswith('data:'):
                    # Extract base64 data after the comma
                    if ',' in base64_data:
                        base64_data = base64_data.split(',', 1)[1]
                        logger.info("Detected Data URL format, extracted base64 content")
                    else:
                        error_msg = "Invalid Data URL format: missing comma separator"
                        logger.error(error_msg)
                        return {"content": [{"type": "text", "text": error_msg}]}
                
                # Decode base64 string to bytes
                image_bytes = base64.b64decode(base64_data)
                logger.info(f"Decoded base64 image data (size: {len(image_bytes)} bytes)")
                
                # Detect image format from the data
                import io
                from PIL import Image
                try:
                    with Image.open(io.BytesIO(image_bytes)) as img:
                        img_format = img.format.lower() if img.format else 'png'
                        logger.info(f"Detected image format: {img_format}")
                except Exception as e:
                    logger.warning(f"Could not detect image format, defaulting to png: {e}")
                    img_format = 'png'
                
                # Create temporary file with correct extension
                with tempfile.NamedTemporaryFile(mode='wb', suffix=f'.{img_format}', delete=False) as temp_file:
                    temp_input_path = temp_file.name
                    temp_file.write(image_bytes)
                logger.info(f"Saved to temporary file: {temp_input_path}")
                image_path_to_use = temp_input_path
            except Exception as e:
                error_msg = f"Failed to decode base64 image data: {str(e)}"
                logger.error(error_msg)
                return {"content": [{"type": "text", "text": error_msg}]}
            
            async with AzureImageGenerator(
                base_url=azure_config["base_url"],
                api_key=azure_config["api_key"],
                deployment_name=azure_config["deployment_name"],
                model=azure_config["model"],
                api_version=azure_config["api_version"]
            ) as generator:
                
                # Edit the image
                result = await generator.edit_image(
                    image_path=image_path_to_use,
                    prompt=prompt,
                    size=size,
                    output_path=output_path
                )
                
                # HTTP mode: always return image data to client
                if output_path:
                    # Image was saved to file, read it back
                    import aiofiles
                    async with aiofiles.open(output_path, 'rb') as f:
                        image_bytes = await f.read()
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                    logger.info(f"Edited image saved to server at: {result} and returning to client (size: {len(image_bytes)} bytes)")
                    return {
                        "content": [
                            {"type": "text", "text": f"Image successfully edited. Saved to server at: {result}"},
                            {"type": "image", "data": image_b64, "mimeType": "image/png"}
                        ]
                    }
                else:
                    # result is bytes
                    image_b64 = base64.b64encode(result).decode('utf-8')
                    logger.info(f"Image editing successful, returning base64 data (size: {len(result)} bytes)")
                    return {
                        "content": [
                            {"type": "text", "text": f"Image editing successful, edit prompt: '{prompt}'"},
                            {"type": "image", "data": image_b64, "mimeType": "image/png"}
                        ]
                    }
        finally:
            # Clean up temporary file if created
            if temp_input_path and os.path.exists(temp_input_path):
                try:
                    os.unlink(temp_input_path)
                    logger.info(f"Cleaned up temporary file: {temp_input_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_input_path}: {e}")
                
    except Exception as e:
        error_msg = f"Error editing image: {str(e)}"
        logger.error(f"Image editing failed: {error_msg}")
        return {"content": [{"type": "text", "text": error_msg}]}


# HTTP Handlers
async def handle_jsonrpc(request: Request):
    """Handle JSON-RPC 2.0 requests"""
    try:
        body = await request.json()
        logger.info(f"Received JSON-RPC request: {body.get('method')}")
        
        # Extract request details
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # Handle notifications (no response needed)
        if request_id is None:
            # This is a notification, not a request
            if method == "notifications/initialized":
                logger.info("Client initialized notification received")
                return Response(status_code=204)  # No Content
            elif method.startswith("notifications/"):
                logger.info(f"Notification received: {method}")
                return Response(status_code=204)  # No Content
            else:
                # Unknown notification
                logger.warning(f"Unknown notification: {method}")
                return Response(status_code=204)  # No Content
        
        # Handle different methods (requests that need responses)
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "azure-image-editor",
                    "version": "1.0.0"
                }
            }
        elif method == "tools/list":
            result = await get_tools_list()
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await call_tool(tool_name, arguments)
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }, status_code=400)
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }, status_code=400)
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }, status_code=500)


async def handle_health(request: Request):
    """Health check endpoint"""
    return Response("OK", status_code=200)


def create_app():
    """Create Starlette application"""
    routes = [
        Route("/", endpoint=handle_jsonrpc, methods=["POST"]),
        Route("/health", endpoint=handle_health, methods=["GET"]),
    ]
    
    return Starlette(debug=True, routes=routes)


async def main():
    """Main server function"""
    # Verify Azure configuration before starting server
    try:
        logger.info("🔍 Verifying Azure configuration...")
        azure_config = get_azure_config()
        logger.info("✅ Azure configuration verification successful")
        logger.info(f"   - Service URL: {azure_config['base_url']}")
        logger.info(f"   - Deployment name: {azure_config['deployment_name']}")
        logger.info(f"   - Model: {azure_config['model']}")
        logger.info(f"   - API key: {'*' * (len(azure_config['api_key']) - 4) + azure_config['api_key'][-4:]}")
    except (ValueError, Exception) as e:
        logger.error(f"❌ Azure configuration verification failed: {str(e)}")
        logger.error("Please set the following required environment variables:")
        logger.error("  - AZURE_BASE_URL: Base URL for Azure AI service")
        logger.error("  - AZURE_API_KEY: API key for Azure AI service")
        logger.error("  - AZURE_DEPLOYMENT_NAME: Deployment model name")
        logger.error("Optional environment variables:")
        logger.error("  - AZURE_MODEL: Model name (defaults to flux.1-kontext-pro)")
        logger.error("  - AZURE_API_VERSION: API version (defaults to 2025-04-01-preview)")
        print("\n💡 Tip: Set these environment variables in a .env file", file=sys.stderr)
        sys.exit(1)
    
    # Get server configuration
    host = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    logger.info("🚀 Starting Azure Image Editor MCP HTTP Server")
    logger.info(f"📊 Default image size: {os.getenv('DEFAULT_IMAGE_SIZE', '1024x1024')}")
    logger.info(f"🌐 Server listening on http://{host}:{port}")
    logger.info(f"🔌 JSON-RPC endpoint: http://{host}:{port}/")
    logger.info(f"❤️  Health check: http://{host}:{port}/health")
    
    app = create_app()
    
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
