import base64
import io
import httpx
import aiofiles
from PIL import Image
from typing import Optional, Union


class AzureImageGenerator:
    def __init__(self, base_url: str, api_key: str, deployment_name: str, model: str = "flux.1-kontext-pro", api_version: str = "2025-04-01-preview"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.deployment_name = deployment_name
        self.model = model
        self.api_version = api_version
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
        
        params = {"api-version": self.api_version}
        
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
        image_path: str,
        prompt: str = "",
        size: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Union[bytes, str]:
        """
        Edit image
        
        Args:
            image_path: Input image path
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
        
        params = {"api-version": self.api_version}
        
        try:
            # Validate input parameters
            if not image_path:
                raise Exception("image_path parameter is required")
            
            # Read image file
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()
            
            # Get original image dimensions if size not specified
            if not size:
                try:
                    with Image.open(io.BytesIO(image_data)) as img:
                        width, height = img.size
                        size = f"{width}x{height}"
                except Exception as e:
                    # If we can't read dimensions, try to detect from file path
                    try:
                        with Image.open(image_path) as img:
                            width, height = img.size
                            size = f"{width}x{height}"
                    except Exception as e2:
                        # Default to 1024x1024 if all else fails
                        size = "1024x1024"
                        raise Exception(f"Could not determine image dimensions, tried BytesIO and file path: {str(e)}, {str(e2)}")
            
            # Prepare multipart form data
            files = {
                "model": (None, self.model),
                "image": ("image.png", image_data, "image/png"),
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
        

if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    async def main():
        async with AzureImageGenerator(
            base_url=os.getenv("AZURE_BASE_URL"),
            api_key=os.getenv("AZURE_API_KEY"),
            deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_API_VERSION", "2025-04-01-preview")
        ) as client:
            # Example usage - save to images folder
            output_path = "images/generated_image.png"
            os.makedirs("images", exist_ok=True)
            
            result = await client.generate_image(
                prompt="A fantasy landscape",
                output_path=output_path
            )
            print(f"Image saved to: {result}")

    asyncio.run(main())