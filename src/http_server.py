#!/usr/bin/env python3
"""
Azure Image Editor MCP Server - VSCode Compatible HTTP Version

HTTP server specifically designed for VSCode MCP clients
"""

import asyncio
import base64
import os
import sys
import uvicorn
import json
import logging
import re
import uuid
import shutil
import aiofiles
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from azure_image_client import AzureImageGenerator

# Load environment variables
load_dotenv()

# Set up logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


class MCPMessage(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


def get_azure_config():
    """Get Azure configuration from environment variables
    
    Requires the following environment variables to be set:
    - AZURE_BASE_URL: Base URL for Azure AI service
    - AZURE_API_KEY: API key for Azure AI service
    - AZURE_DEPLOYMENT_NAME: Deployment model name
    - AZURE_MODEL: Model name (optional, defaults to flux.1-kontext-pro)
    
    Raises:
        ValueError: When required environment variables are not set
        Exception: When configuration validation fails
    """
    try:
        # Check required environment variables
        required_vars = {
            "AZURE_BASE_URL": "Base URL for Azure AI service",
            "AZURE_API_KEY": "API key for Azure AI service", 
            "AZURE_DEPLOYMENT_NAME": "Deployment model name"
        }
        
        # Optional environment variables
        optional_vars = {
            "AZURE_MODEL": "Model name (defaults to flux.1-kontext-pro)"
        }
        
        missing_vars = []
        config = {}
        
        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            if not value or not value.strip():
                missing_vars.append(f"{var_name} ({description})")
            else:
                # Convert environment variable names to config key names
                key_map = {
                    "AZURE_BASE_URL": "base_url",
                    "AZURE_API_KEY": "api_key",
                    "AZURE_DEPLOYMENT_NAME": "deployment_name"
                }
                config[key_map[var_name]] = value.strip()
        
        # Handle optional variables
        for var_name, description in optional_vars.items():
            value = os.getenv(var_name)
            if value and value.strip():
                if var_name == "AZURE_MODEL":
                    config["model"] = value.strip()
            else:
                # Set defaults for optional variables
                if var_name == "AZURE_MODEL":
                    config["model"] = "flux.1-kontext-pro"
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Basic validation of configuration values
        if not config["base_url"].startswith(("http://", "https://")):
            raise ValueError("AZURE_BASE_URL must be a valid HTTP/HTTPS URL")
        
        if len(config["api_key"]) < 10:
            raise ValueError("AZURE_API_KEY is too short, please check if the API key is correct")
        
        if not config["deployment_name"]:
            raise ValueError("AZURE_DEPLOYMENT_NAME cannot be empty")
        
        logger.debug("Azure configuration loaded successfully")
        return config
        
    except ValueError:
        # Re-raise validation errors
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
        # Unicode range detection: Chinese, Japanese, Korean
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



async def create_audit_session(operation_type: str) -> str:
    """Create a new audit session and return session ID"""
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create audit directory structure
    audit_base_dir = Path("audit")
    audit_base_dir.mkdir(exist_ok=True)
    
    session_dir_name = f"{timestamp}_{session_id[:8]}_anonymous_{operation_type}"
    session_dir = audit_base_dir / session_dir_name
    session_dir.mkdir(exist_ok=True)
    
    return str(session_dir)


async def log_audit_request(session_dir: str, request_data: Dict[str, Any]):
    """Log the request data to audit session"""
    session_path = Path(session_dir)
    request_file = session_path / "request.json"
    
    audit_data = {
        "timestamp": datetime.now().isoformat(),
        "request": request_data
    }
    
    async with aiofiles.open(request_file, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(audit_data, indent=2, ensure_ascii=False))


async def log_audit_response(session_dir: str, response_data: Dict[str, Any], image_data: Optional[bytes] = None, output_file_path: Optional[str] = None):
    """Log the response data and image to audit session"""
    session_path = Path(session_dir)
    response_file = session_path / "response.json"
    
    audit_data = {
        "timestamp": datetime.now().isoformat(),
        "response": response_data
    }
    
    # Save response JSON
    async with aiofiles.open(response_file, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(audit_data, indent=2, ensure_ascii=False))
    
    # Save image if provided as bytes
    if image_data:
        image_file = session_path / "result.png"
        async with aiofiles.open(image_file, 'wb') as f:
            await f.write(image_data)
    
    # Copy output file if provided as file path
    if output_file_path and os.path.exists(output_file_path):
        import asyncio
        loop = asyncio.get_event_loop()
        output_dest = session_path / f"output_{Path(output_file_path).name}"
        await loop.run_in_executor(None, shutil.copy2, output_file_path, str(output_dest))


async def copy_input_image_to_audit(session_dir: str, input_image_path: str):
    """Copy input image to audit session for edit operations"""
    if not os.path.exists(input_image_path):
        return
    
    session_path = Path(session_dir)
    input_image_dest = session_path / f"input_{Path(input_image_path).name}"
    
    # Use asyncio to run shutil.copy2 in thread pool to avoid blocking
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, shutil.copy2, input_image_path, str(input_image_dest))


# Create FastAPI application
app = FastAPI(
    title="Azure Image Editor MCP Server",
    description="VSCode compatible MCP server, supports Azure AI Foundry image generation and editing",
    version="1.0.0"
)

# Add CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_mcp_response(request_id: Optional[int], result: Any = None, error: Any = None) -> Dict:
    """Create standard MCP response"""
    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }
    
    if error:
        response["error"] = error
    else:
        response["result"] = result
        
    return response


def create_mcp_error(code: int, message: str, data: Any = None) -> Dict:
    """Create MCP error response"""
    error = {
        "code": code,
        "message": message
    }
    if data:
        error["data"] = data
    return error


@app.post("/")
async def handle_mcp_request(request: Request):
    """Handle all MCP requests - main endpoint"""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        logger.info(f"Received MCP request: method={method}, id={request_id}")
        
        if method == "initialize":
            logger.info("Handling initialization request")
            return create_mcp_response(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    }
                },
                "serverInfo": {
                    "name": "azure-image-editor",
                    "version": "1.0.0"
                }
            })
            
        elif method == "tools/list":
            logger.info("Returning tool list")
            default_size = os.getenv("DEFAULT_IMAGE_SIZE", "1024x1024")
            tools = [
                {
                    "name": "generate_image",
                    "description": "Generate images from text prompts using Azure AI Foundry (English prompts only)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "English description for image generation"
                            },
                            "size": {
                                "type": "string",
                                "description": f"Image size, supports 1024x1024, 1792x1024, 1024x1792, default: {default_size}",
                                "default": default_size,
                                "enum": ["1024x1024", "1792x1024", "1024x1792"]
                            },
                            "output_path": {
                                "type": "string",
                                "description": "Optional output file path"
                            }
                        },
                        "required": ["prompt"]
                    }
                },
                {
                    "name": "edit_image",
                    "description": "Edit existing images using Azure AI Foundry (English prompts only)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "image_path": {
                                "type": "string",
                                "description": "Path to the image file to edit"
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
                                "description": "Optional output file path"
                            }
                        },
                        "required": ["image_path", "prompt"]
                    }
                }
            ]
            
            return create_mcp_response(request_id, {"tools": tools})
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info(f"Tool call: {tool_name}, arguments: {arguments}")
            
            if tool_name == "generate_image":
                result = await handle_generate_image(arguments)
                return create_mcp_response(request_id, {"content": result})
                
            elif tool_name == "edit_image":
                result = await handle_edit_image(arguments)
                return create_mcp_response(request_id, {"content": result})
                
            else:
                logger.error(f"Unknown tool: {tool_name}")
                return create_mcp_response(
                    request_id, 
                    error=create_mcp_error(-32602, f"Unknown tool: {tool_name}")
                )
                
        else:
            logger.error(f"Unknown method: {method}")
            return create_mcp_response(
                request_id,
                error=create_mcp_error(-32601, f"Unknown method: {method}")
            )
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return create_mcp_response(
            None,
            error=create_mcp_error(-32700, "Parse error")
        )
    except Exception as e:
        logger.error(f"Internal error: {str(e)}")
        return create_mcp_response(
            request_id,
            error=create_mcp_error(-32603, f"Internal error: {str(e)}")
        )


@app.get("/")
async def root_info():
    """Root path information"""
    return {
        "name": "Azure Image Editor MCP Server",
        "version": "1.0.0",
        "protocol": "MCP HTTP",
        "capabilities": ["tools"],
        "status": "ready"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "azure-image-editor-mcp"}


async def handle_generate_image(arguments: Dict[str, Any]):
    """Handle image generation request"""
    # Create audit session
    session_dir = await create_audit_session("generate_image")
    
    try:
        prompt = arguments.get("prompt", "")
        size = arguments.get("size", os.getenv("DEFAULT_IMAGE_SIZE", "1024x1024"))
        output_path = arguments.get("output_path")
        
        # Log request to audit
        await log_audit_request(session_dir, {
            "operation": "generate_image",
            "prompt": prompt,
            "size": size,
            "output_path": output_path
        })
        
        logger.info(f"Image generation request: prompt='{prompt}', size={size}, output_path={output_path}, audit_session={session_dir}")
        
        # Get Azure configuration
        try:
            azure_config = get_azure_config()
        except (ValueError, Exception) as e:
            error_msg = f"Azure configuration error: {str(e)}"
            logger.error(f"Failed to get Azure configuration: {error_msg}")
            await log_audit_response(session_dir, {"error": error_msg})
            return [{"type": "text", "text": error_msg}]
        
        # Validate prompt is in English
        if not is_english_text(prompt):
            error_msg = "Prompt must be in English. Please use English to describe the image you want to generate."
            logger.warning(f"Non-English prompt rejected: '{prompt}'")
            await log_audit_response(session_dir, {"error": error_msg})
            return [{"type": "text", "text": error_msg}]
        
        # Validate image size
        if not validate_image_size(size):
            error_msg = f"Unsupported image size: {size}. Supported sizes: 1024x1024, 1792x1024, 1024x1792"
            logger.warning(f"Invalid image size: {size}")
            await log_audit_response(session_dir, {"error": error_msg})
            return [{"type": "text", "text": error_msg}]
        
        async with AzureImageGenerator(
            base_url=azure_config["base_url"],
            api_key=azure_config["api_key"],
            deployment_name=azure_config["deployment_name"],
            model=azure_config["model"]
        ) as generator:
            
            result = await generator.generate_image(
                prompt=prompt,
                size=size,
                output_path=output_path
            )
            
            if output_path:
                logger.info(f"Image saved to file: {result}")
                response_data = {"success": True, "output_file": result}
                await log_audit_response(session_dir, response_data, output_file_path=result)
                return [{"type": "text", "text": f"Image successfully generated and saved to: {result}"}]
            else:
                image_b64 = base64.b64encode(result).decode('utf-8')
                logger.info(f"Image generation successful, returning base64 data (size: {len(result)} bytes)")
                response_data = {"success": True, "image_size_bytes": len(result)}
                await log_audit_response(session_dir, response_data, image_data=result)
                return [
                    {"type": "text", "text": f"Image generation successful, prompt: '{prompt}', size: {size}"},
                    {"type": "image", "data": image_b64, "mimeType": "image/png"}
                ]
                
    except Exception as e:
        error_msg = f"Error generating image: {str(e)}"
        logger.error(f"Image generation failed: {error_msg}")
        await log_audit_response(session_dir, {"error": error_msg})
        return [{"type": "text", "text": error_msg}]


async def handle_edit_image(arguments: Dict[str, Any]):
    """Handle image editing request"""
    # Create audit session
    session_dir = await create_audit_session("edit_image")
    
    try:
        image_path = arguments.get("image_path", "")
        prompt = arguments.get("prompt", "") + " (and all other elements exactly the same)"
        size = arguments.get("size")  # Optional size override
        output_path = arguments.get("output_path")
        
        # Log request to audit
        await log_audit_request(session_dir, {
            "operation": "edit_image",
            "image_path": image_path,
            "prompt": prompt,
            "size": size,
            "output_path": output_path
        })
        
        # Copy input image to audit session
        await copy_input_image_to_audit(session_dir, image_path)
        
        logger.info(f"Image editing request: image_path='{image_path}', prompt='{prompt}', output_path={output_path}, audit_session={session_dir}")
        
        # Get Azure configuration
        try:
            azure_config = get_azure_config()
        except (ValueError, Exception) as e:
            error_msg = f"Azure configuration error: {str(e)}"
            logger.error(f"Failed to get Azure configuration: {error_msg}")
            await log_audit_response(session_dir, {"error": error_msg})
            return [{"type": "text", "text": error_msg}]
        
        # Validate prompt is in English
        if not is_english_text(prompt):
            error_msg = "Prompt must be in English. Please use English to describe how you want to edit the image."
            logger.warning(f"Non-English prompt rejected: '{prompt}'")
            await log_audit_response(session_dir, {"error": error_msg})
            return [{"type": "text", "text": error_msg}]
        
        # Check if input file exists
        if not os.path.exists(image_path):
            error_msg = f"Error: Image file not found {image_path}"
            logger.error(f"Input file does not exist: {image_path}")
            await log_audit_response(session_dir, {"error": error_msg})
            return [{"type": "text", "text": error_msg}]
        
        async with AzureImageGenerator(
            base_url=azure_config["base_url"],
            api_key=azure_config["api_key"],
            deployment_name=azure_config["deployment_name"],
            model=azure_config["model"]
        ) as generator:
            
            result = await generator.edit_image(
                image_path=image_path,
                prompt=prompt,
                size=size,
                output_path=output_path
            )
            
            if output_path:
                logger.info(f"Edited image saved to file: {result}")
                response_data = {"success": True, "output_file": result, "input_file": image_path}
                await log_audit_response(session_dir, response_data, output_file_path=result)
                return [{"type": "text", "text": f"Image successfully edited and saved to: {result}"}]
            else:
                image_b64 = base64.b64encode(result).decode('utf-8')
                logger.info(f"Image editing successful, returning base64 data (size: {len(result)} bytes)")
                response_data = {"success": True, "image_size_bytes": len(result), "input_file": image_path}
                await log_audit_response(session_dir, response_data, image_data=result)
                return [
                    {"type": "text", "text": f"Image editing successful, edit prompt: '{prompt}', source file: {image_path}"},
                    {"type": "image", "data": image_b64, "mimeType": "image/png"}
                ]
                
    except Exception as e:
        error_msg = f"Error editing image: {str(e)}"
        logger.error(f"Image editing failed: {error_msg}")
        await log_audit_response(session_dir, {"error": error_msg})
        return [{"type": "text", "text": error_msg}]


def main():
    """Start HTTP server"""
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
        print("\n💡 Tip: Set these environment variables in a .env file, or set them before startup")
        print("Example:")
        print("  export AZURE_BASE_URL='https://your-service.services.ai.azure.com'")
        print("  export AZURE_API_KEY='your-api-key'")
        print("  export AZURE_DEPLOYMENT_NAME='your-deployment-name'")
        print("  export AZURE_MODEL='flux.1-kontext-pro'")
        sys.exit(1)
    
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    logger.info(f"🚀 Starting Azure Image Editor MCP HTTP Server (VSCode Compatible)")
    logger.info(f"📍 Server address: http://{host}:{port}")
    logger.info(f"🔧 Health check: http://{host}:{port}/health")
    logger.info(f"📋 MCP endpoint: http://{host}:{port}/")
    logger.info(f"📊 Default image size: {os.getenv('DEFAULT_IMAGE_SIZE', '1024x1024')}")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")