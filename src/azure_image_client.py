import asyncio
import base64
import io
import httpx
import aiofiles
from PIL import Image
from typing import Optional, Union
import json


class AzureImageGenerator:
    def __init__(self, base_url: str, api_key: str, deployment_name: str, model: str = "flux.1-kontext-pro"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.deployment_name = deployment_name
        self.model = model
        # Increase timeout duration
        timeout = httpx.Timeout(300.0)  # 5-minute timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def generate_image(
        self, 
        prompt: str, 
        size: str = "1024x1024", 
        n: int = 1,
        output_path: Optional[str] = None
    ) -> Union[bytes, str]:
        """
        Generate image
        
        Args:
            prompt: Text prompt
            size: Image size, e.g. "1024x1024"
            n: Number of images to generate
            output_path: Optional output path, saves file if provided
        
        Returns:
            File path if output_path provided, otherwise returns image bytes data
        """
        url = f"{self.base_url}/openai/deployments/{self.deployment_name}/images/generations"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "prompt": prompt,
            "size": size,
            "n": n,
            "model": self.model
        }
        
        params = {"api-version": "2025-04-01-preview"}
        
        try:
            response = await self.client.post(url, json=data, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if "data" not in result or len(result["data"]) == 0:
                raise Exception("No image data returned from API")
            
            # Get base64 encoded image data
            b64_image = result["data"][0]["b64_json"]
            image_bytes = base64.b64decode(b64_image)
            
            if output_path:
                async with aiofiles.open(output_path, 'wb') as f:
                    await f.write(image_bytes)
                return output_path
            else:
                return image_bytes
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise Exception(f"Azure API error: {e.response.status_code} - {error_detail}")
        except Exception as e:
            raise Exception(f"Image generation failed: {str(e)}")

    async def edit_image(
        self, 
        image_data: str,
        prompt: str = "",
        size: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Union[bytes, str]:
        """
        Edit image
        
        Args:
            image_data: Base64 encoded image data
            prompt: Edit prompt
            size: Optional size override, if not provided uses original image dimensions
            output_path: Optional output path, saves file if provided
        
        Returns:
            File path if output_path provided, otherwise returns image bytes data
        """
        url = f"{self.base_url}/openai/deployments/{self.deployment_name}/images/edits"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        params = {"api-version": "2025-04-01-preview"}
        
        try:
            # Validate input parameters
            if not image_data:
                raise Exception("image_data parameter is required")
            
            # Decode from base64
            raw_image_data = base64.b64decode(image_data)
            
            # Get original image dimensions if size not specified
            if not size:
                with Image.open(io.BytesIO(raw_image_data)) as img:
                    width, height = img.size
                    size = f"{width}x{height}"
            
            # Prepare multipart form data
            files = {
                "model": (None, self.model),
                "image": ("image.png", raw_image_data, "image/png"),
                "prompt": (None, prompt),
                "size": (None, size)
            }
            
            response = await self.client.post(
                url, 
                files=files, 
                headers=headers, 
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "data" not in result or len(result["data"]) == 0:
                raise Exception("No image data returned from API")
            
            # Get base64 encoded image data
            b64_image = result["data"][0]["b64_json"]
            image_bytes = base64.b64decode(b64_image)
            
            if output_path:
                async with aiofiles.open(output_path, 'wb') as f:
                    await f.write(image_bytes)
                return output_path
            else:
                return image_bytes
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise Exception(f"Azure API error: {e.response.status_code} - {error_detail}")
        except Exception as e:
            raise Exception(f"Image editing failed: {str(e)}")