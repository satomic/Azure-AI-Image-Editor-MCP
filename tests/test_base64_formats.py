#!/usr/bin/env python3
"""
Test script to verify both base64 formats work correctly
Tests:
1. Raw base64 format
2. Data URL format (data:image/png;base64,...)
"""

import asyncio
import base64
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Install with: pip install httpx")
    exit(1)


async def test_raw_base64():
    """Test with raw base64 format"""
    print("\n" + "="*60)
    print("Test 1: Raw Base64 Format")
    print("="*60)
    
    server_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Generate a test image first
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
                            "prompt": "A red square on white background",
                            "size": "1024x1024"
                        }
                    }
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to generate image: {response.status_code}")
                return False
            
            result = response.json()
            image_content = [c for c in result["result"]["content"] if c.get("type") == "image"]
            
            if not image_content:
                print("❌ No image in response")
                return False
            
            raw_base64 = image_content[0].get("data")
            print(f"✅ Generated image (base64 length: {len(raw_base64)})")
            
            # Test editing with raw base64
            print("\n2️⃣  Testing edit with RAW base64 format...")
            response = await client.post(
                f"{server_url}/",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "edit_image",
                        "arguments": {
                            "image_data_base64": raw_base64,  # Raw format
                            "prompt": "change the red square to blue"
                        }
                    }
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Edit request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            result = response.json()
            if "error" in result:
                print(f"❌ Error in response: {result['error']}")
                return False
            
            edited_content = [c for c in result["result"]["content"] if c.get("type") == "image"]
            if not edited_content:
                print("❌ No edited image in response")
                return False
            
            # Save result
            edited_base64 = edited_content[0].get("data")
            Path("./test_raw_base64_edited.png").write_bytes(base64.b64decode(edited_base64))
            
            print("✅ Successfully edited with RAW base64 format")
            print("   Saved to: test_raw_base64_edited.png")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_data_url_format():
    """Test with Data URL format"""
    print("\n" + "="*60)
    print("Test 2: Data URL Format")
    print("="*60)
    
    server_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Generate a test image first
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
                            "prompt": "A green circle on white background",
                            "size": "1024x1024"
                        }
                    }
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to generate image: {response.status_code}")
                return False
            
            result = response.json()
            image_content = [c for c in result["result"]["content"] if c.get("type") == "image"]
            
            if not image_content:
                print("❌ No image in response")
                return False
            
            raw_base64 = image_content[0].get("data")
            
            # Convert to Data URL format
            data_url = f"data:image/png;base64,{raw_base64}"
            print(f"✅ Generated image and converted to Data URL format")
            print(f"   Data URL length: {len(data_url)}")
            print(f"   Prefix: {data_url[:50]}...")
            
            # Test editing with Data URL format
            print("\n2️⃣  Testing edit with Data URL format...")
            response = await client.post(
                f"{server_url}/",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "edit_image",
                        "arguments": {
                            "image_data_base64": data_url,  # Data URL format
                            "prompt": "change the green circle to yellow"
                        }
                    }
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Edit request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            result = response.json()
            if "error" in result:
                print(f"❌ Error in response: {result['error']}")
                return False
            
            edited_content = [c for c in result["result"]["content"] if c.get("type") == "image"]
            if not edited_content:
                print("❌ No edited image in response")
                return False
            
            # Save result
            edited_base64 = edited_content[0].get("data")
            Path("./test_data_url_edited.png").write_bytes(base64.b64decode(edited_base64))
            
            print("✅ Successfully edited with Data URL format")
            print("   Saved to: test_data_url_edited.png")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    print("\n" + "="*60)
    print("Base64 Format Compatibility Test")
    print("="*60)
    print("\n⚠️  Make sure the HTTP server is running:")
    print("    python src/mcp_server_http.py\n")
    
    # Run both tests
    test1_passed = await test_raw_base64()
    test2_passed = await test_data_url_format()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Test 1 (Raw base64):     {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Data URL):       {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed!")
        print("\n📁 Generated files:")
        print("   - test_raw_base64_edited.png")
        print("   - test_data_url_edited.png")
        print("\n💡 Both base64 formats are working correctly!")
    else:
        print("\n⚠️  Some tests failed. Please check the server logs.")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
