#!/usr/bin/env python3
"""
Example: How to use edit_image in HTTP mode with base64 image data
"""

import asyncio
import base64
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Install with: pip install httpx")
    exit(1)


async def edit_image_example():
    """
    Demonstrate how to edit an image using the HTTP MCP server.
    
    In HTTP mode, you need to:
    1. Read your local image file
    2. Encode it to base64
    3. Send the base64 data with your edit request
    4. Receive the edited image as base64
    5. Decode and save locally
    """
    
    server_url = "http://localhost:8000"
    
    # Step 1: Prepare your image
    # Replace this with your actual image path
    input_image_path = "./sample_input.png"
    
    if not Path(input_image_path).exists():
        print(f"❌ Error: Image file not found: {input_image_path}")
        print("📝 Please create a sample image or update the path in this script")
        return
    
    print("🎨 Azure Image Editor - HTTP Mode Edit Example\n")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Step 2: Read and encode the image
            print("\n1️⃣  Reading local image file...")
            with open(input_image_path, "rb") as f:
                image_bytes = f.read()
            
            print(f"   ✅ Image loaded: {len(image_bytes)} bytes")
            
            # Step 3: Encode to base64
            print("\n2️⃣  Encoding image to base64...")
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            print(f"   ✅ Base64 encoded: {len(image_base64)} characters")
            
            # Step 4: Send edit request
            print("\n3️⃣  Sending edit request to server...")
            edit_prompt = "Make this image black and white"
            print(f"   📝 Edit instruction: '{edit_prompt}'")
            
            response = await client.post(
                f"{server_url}/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "edit_image",
                        "arguments": {
                            "image_data_base64": image_base64,
                            "prompt": edit_prompt,
                            "output_path": "/tmp/edited_output.png"  # Optional server-side save
                        }
                    }
                }
            )
            
            if response.status_code != 200:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
            
            # Step 5: Parse response
            print("\n4️⃣  Processing response...")
            result = response.json()
            
            if "result" not in result or "content" not in result["result"]:
                print(f"   ❌ Unexpected response format")
                print(f"   Response: {result}")
                return
            
            content = result["result"]["content"]
            
            # Get text message
            text_content = [c for c in content if c.get("type") == "text"]
            if text_content:
                print(f"   📄 {text_content[0]['text']}")
            
            # Get edited image
            image_content = [c for c in content if c.get("type") == "image"]
            if not image_content:
                print("   ❌ No image data in response!")
                return
            
            # Step 6: Decode and save
            print("\n5️⃣  Saving edited image...")
            edited_base64 = image_content[0].get("data", "")
            edited_bytes = base64.b64decode(edited_base64)
            
            output_path = Path("./edited_output.png")
            output_path.write_bytes(edited_bytes)
            
            print(f"   ✅ Edited image saved to: {output_path.absolute()}")
            print(f"   📊 File size: {len(edited_bytes)} bytes")
            
            print("\n" + "=" * 60)
            print("🎉 Success! Image editing completed.")
            print("\n📋 What happened:")
            print("   1. Local image was read and encoded to base64")
            print("   2. Base64 data was sent to the HTTP server")
            print("   3. Server processed the edit using Azure AI")
            print("   4. Edited image was returned as base64")
            print("   5. Client decoded and saved the result")
            print("\n💡 Key Point for HTTP Mode:")
            print("   - Use 'image_data_base64' instead of 'image_path'")
            print("   - Server can't access client's file system")
            print("   - All image data is transferred via base64 encoding")
            
        except httpx.TimeoutException:
            print("\n❌ Request timeout - image editing can take time")
            print("   Try again or check server logs")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()


async def quick_test():
    """Quick test that doesn't require an existing image"""
    print("🧪 Quick Test Mode - Using generated image\n")
    print("This will:")
    print("1. Generate a test image")
    print("2. Edit that image")
    print("3. Show that base64 workflow works\n")
    
    server_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Generate a simple test image
            print("1️⃣  Generating test image...")
            response = await client.post(
                f"{server_url}/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "generate_image",
                        "arguments": {
                            "prompt": "A red circle on white background",
                            "size": "1024x1024"
                        }
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                image_content = [c for c in result["result"]["content"] if c.get("type") == "image"]
                
                if image_content:
                    generated_base64 = image_content[0].get("data")
                    print("   ✅ Test image generated")
                    
                    # Now edit it
                    print("\n2️⃣  Editing the generated image...")
                    print("   📝 Changing red to blue")
                    
                    response = await client.post(
                        f"{server_url}/",
                        json={
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/call",
                            "params": {
                                "name": "edit_image",
                                "arguments": {
                                    "image_data_base64": generated_base64,
                                    "prompt": "change the red circle to blue"
                                }
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        edited_content = [c for c in result["result"]["content"] if c.get("type") == "image"]
                        
                        if edited_content:
                            edited_base64 = edited_content[0].get("data")
                            
                            # Save both images
                            Path("./test_generated.png").write_bytes(base64.b64decode(generated_base64))
                            Path("./test_edited.png").write_bytes(base64.b64decode(edited_base64))
                            
                            print("   ✅ Image edited successfully")
                            print("\n📁 Saved files:")
                            print("   - test_generated.png (original red circle)")
                            print("   - test_edited.png (edited blue circle)")
                            print("\n🎉 Quick test completed!")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("Azure Image Editor MCP - HTTP Mode Edit Image Example")
    print("=" * 60 + "\n")
    print("⚠️  Make sure the HTTP server is running:")
    print("    python src/mcp_server_http.py\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print("Running in quick test mode...\n")
        asyncio.run(quick_test())
    else:
        print("Options:")
        print("  python tests/test_edit_image_http.py           # Edit sample_input.png")
        print("  python tests/test_edit_image_http.py --quick   # Quick test (no file needed)")
        print()
        
        if Path("./sample_input.png").exists():
            asyncio.run(edit_image_example())
        else:
            print("⚠️  sample_input.png not found. Running quick test instead...\n")
            asyncio.run(quick_test())
