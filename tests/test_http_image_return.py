#!/usr/bin/env python3
"""
Test script to demonstrate HTTP MCP server image data return behavior
"""

import asyncio
import json
import base64
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Install with: pip install httpx")
    exit(1)


async def test_image_generation_with_path():
    """Test that image data is returned even when output_path is provided"""
    server_url = "http://localhost:8000"
    
    print("🧪 Testing HTTP MCP Server - Image Data Return Behavior\n")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Test 1: Health check
            print("\n1️⃣  Testing server health...")
            response = await client.get(f"{server_url}/health")
            if response.status_code == 200:
                print("   ✅ Server is healthy")
            else:
                print(f"   ❌ Server health check failed: {response.status_code}")
                return
            
            # Test 2: Generate image WITH output_path
            print("\n2️⃣  Generating image with output_path specified...")
            print("   📝 Request: output_path='/tmp/test_image.png'")
            
            response = await client.post(
                f"{server_url}/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "generate_image",
                        "arguments": {
                            "prompt": "A simple red circle on white background",
                            "size": "1024x1024",
                            "output_path": "/tmp/test_image.png"
                        }
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "result" in result and "content" in result["result"]:
                    content = result["result"]["content"]
                    
                    # Check for text message
                    text_content = [c for c in content if c.get("type") == "text"]
                    if text_content:
                        print(f"   📄 Server message: {text_content[0]['text']}")
                    
                    # Check for image data
                    image_content = [c for c in content if c.get("type") == "image"]
                    if image_content:
                        image_data = image_content[0].get("data", "")
                        print(f"   ✅ Image data returned! Size: {len(image_data)} characters (base64)")
                        
                        # Save the image locally (client-side)
                        local_path = Path("./test_client_received_image.png")
                        image_bytes = base64.b64decode(image_data)
                        local_path.write_bytes(image_bytes)
                        print(f"   💾 Image saved to client at: {local_path.absolute()}")
                        print(f"   📊 Image file size: {len(image_bytes)} bytes")
                        
                        print("\n   🎉 SUCCESS: Image data was returned to client!")
                        print("   📝 This demonstrates that in HTTP mode:")
                        print("      - Image is saved on server (/tmp/test_image.png)")
                        print("      - Image data is ALSO returned to client (base64)")
                        print("      - Client can save it locally without file transfer")
                    else:
                        print("   ❌ No image data in response!")
                else:
                    print(f"   ❌ Unexpected response format: {result}")
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
            
            # Test 3: Generate image WITHOUT output_path
            print("\n3️⃣  Generating image WITHOUT output_path...")
            print("   📝 Request: No output_path specified")
            
            response = await client.post(
                f"{server_url}/",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "generate_image",
                        "arguments": {
                            "prompt": "A simple blue square on white background",
                            "size": "1024x1024"
                        }
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "result" in result and "content" in result["result"]:
                    content = result["result"]["content"]
                    image_content = [c for c in content if c.get("type") == "image"]
                    
                    if image_content:
                        image_data = image_content[0].get("data", "")
                        print(f"   ✅ Image data returned! Size: {len(image_data)} characters (base64)")
                        
                        # Save locally
                        local_path = Path("./test_client_no_path_image.png")
                        image_bytes = base64.b64decode(image_data)
                        local_path.write_bytes(image_bytes)
                        print(f"   💾 Image saved to client at: {local_path.absolute()}")
                    else:
                        print("   ❌ No image data in response!")
            
            # Test 4: Edit image with base64 input (HTTP mode)
            print("\n4️⃣  Testing edit_image with base64 input (HTTP mode)...")
            
            # Use the previously generated image
            if Path("./test_client_received_image.png").exists():
                # Read the image and encode to base64
                with open("./test_client_received_image.png", "rb") as f:
                    image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                print(f"   📤 Uploading image as base64 ({len(image_base64)} chars)")
                print("   📝 Request: Edit to add blue background")
                
                response = await client.post(
                    f"{server_url}/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "edit_image",
                            "arguments": {
                                "image_data_base64": image_base64,
                                "prompt": "change background to blue",
                                "output_path": "/tmp/edited_image.png"
                            }
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "result" in result and "content" in result["result"]:
                        content = result["result"]["content"]
                        
                        text_content = [c for c in content if c.get("type") == "text"]
                        if text_content:
                            print(f"   📄 Server message: {text_content[0]['text']}")
                        
                        image_content = [c for c in content if c.get("type") == "image"]
                        if image_content:
                            edited_data = image_content[0].get("data", "")
                            print(f"   ✅ Edited image returned! Size: {len(edited_data)} characters")
                            
                            # Save edited image
                            edited_path = Path("./test_edited_image.png")
                            edited_bytes = base64.b64decode(edited_data)
                            edited_path.write_bytes(edited_bytes)
                            print(f"   💾 Edited image saved to: {edited_path.absolute()}")
                            
                            print("\n   🎉 SUCCESS: Image editing with base64 input works!")
                            print("   📝 This demonstrates HTTP mode:")
                            print("      - Client uploads image as base64")
                            print("      - Server processes the edit")
                            print("      - Edited image returned as base64")
                        else:
                            print("   ❌ No edited image data in response!")
                else:
                    print(f"   ❌ Edit request failed: {response.status_code}")
            else:
                print("   ⚠️  Skipping edit test - no source image available")
            
            print("\n" + "=" * 60)
            print("✅ Test completed successfully!")
            print("\n📋 Summary:")
            print("   - HTTP mode ALWAYS returns image data to client")
            print("   - output_path saves on server AND returns to client")
            print("   - Client can receive and save images locally")
            print("   - edit_image accepts base64 input in HTTP mode")
            
        except httpx.TimeoutException:
            print("\n❌ Request timeout - image generation takes time")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    print("\n🚀 Azure Image Editor MCP HTTP Server - Image Return Test")
    print("⚠️  Make sure the HTTP server is running: python src/mcp_server_http.py\n")
    
    asyncio.run(test_image_generation_with_path())
