#!/usr/bin/env python3
"""
Quick test to verify the fixes:
1. HTTP mode no longer accepts image_path parameter
2. BytesIO error is fixed by proper image format detection
"""

import asyncio
import base64
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Install with: pip install httpx")
    exit(1)


async def test_fix():
    """Test the fixed edit_image functionality"""
    print("\n" + "="*60)
    print("Testing Fixed Edit Image Functionality")
    print("="*60)
    
    server_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Step 1: Generate a test image
            print("\n1️⃣  Generating test image...")
            response = await client.post(
                f"{server_url}/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "generate_image",
                        "arguments": {
                            "prompt": "A simple red square on white background",
                            "size": "1024x1024"
                        }
                    }
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to generate image: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            result = response.json()
            image_content = [c for c in result["result"]["content"] if c.get("type") == "image"]
            
            if not image_content:
                print("❌ No image in response")
                return False
            
            raw_base64 = image_content[0].get("data")
            print(f"✅ Generated test image successfully")
            
            # Step 2: Test with Data URL format (the format that was causing the error)
            print("\n2️⃣  Testing edit with Data URL format...")
            data_url = f"data:image/png;base64,{raw_base64}"
            print(f"   Using Data URL format (length: {len(data_url)})")
            
            response = await client.post(
                f"{server_url}/",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "edit_image",
                        "arguments": {
                            "image_data_base64": data_url,
                            "prompt": "Transform to deep black theme with elegant contrast"
                        }
                    }
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Edit request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            result = response.json()
            
            # Check for errors
            if "error" in result:
                print(f"❌ Error in response: {result['error']}")
                return False
            
            # Check for edited image
            edited_content = [c for c in result["result"]["content"] if c.get("type") == "image"]
            if not edited_content:
                print("❌ No edited image in response")
                text_content = [c for c in result["result"]["content"] if c.get("type") == "text"]
                if text_content:
                    print(f"   Text response: {text_content[0].get('text')}")
                return False
            
            # Save result
            edited_base64 = edited_content[0].get("data")
            output_file = Path("./test_fix_verification_result.png")
            output_file.write_bytes(base64.b64decode(edited_base64))
            
            print("✅ Successfully edited image with Data URL format")
            print(f"   Saved to: {output_file.absolute()}")
            print(f"   Image size: {len(base64.b64decode(edited_base64))} bytes")
            
            # Step 3: Verify tool schema no longer has image_path
            print("\n3️⃣  Verifying tool schema...")
            response = await client.post(
                f"{server_url}/",
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/list",
                    "params": {}
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                tools = result.get("result", {}).get("tools", [])
                edit_tool = next((t for t in tools if t["name"] == "edit_image"), None)
                
                if edit_tool:
                    properties = edit_tool["inputSchema"]["properties"]
                    required = edit_tool["inputSchema"]["required"]
                    
                    if "image_path" in properties:
                        print("❌ Tool schema still contains image_path parameter")
                        return False
                    
                    if "image_data_base64" not in required:
                        print("❌ image_data_base64 is not required")
                        return False
                    
                    print("✅ Tool schema correctly updated:")
                    print(f"   Required parameters: {required}")
                    print(f"   Available parameters: {list(properties.keys())}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    print("\n" + "="*60)
    print("Fix Verification Test")
    print("="*60)
    print("\nThis test verifies:")
    print("1. ✅ Data URL format (data:image/png;base64,...) works correctly")
    print("2. ✅ BytesIO image format detection issue is fixed")
    print("3. ✅ image_path parameter removed from HTTP mode")
    print("4. ✅ image_data_base64 is now required in HTTP mode")
    print("\n⚠️  Make sure the HTTP server is running:")
    print("    python src/mcp_server_http.py\n")
    
    success = await test_fix()
    
    print("\n" + "="*60)
    if success:
        print("🎉 All fixes verified successfully!")
        print("="*60)
        print("\n✅ Issues resolved:")
        print("   1. Data URL format now works correctly")
        print("   2. Image format detection prevents BytesIO errors")
        print("   3. HTTP mode only uses image_data_base64 (no image_path)")
        print("   4. Tool schema properly requires image_data_base64")
    else:
        print("❌ Verification failed - please check server logs")
        print("="*60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
