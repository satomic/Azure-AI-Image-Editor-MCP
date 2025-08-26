#!/usr/bin/env python3
"""
Test HTTP version of MCP server
"""

import asyncio
import json
import httpx


async def test_http_mcp_server():
    """Test HTTP version of MCP server"""
    server_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test server health status
            print("🔧 Testing server connection...")
            response = await client.get(f"{server_url}/health")
            if response.status_code == 200:
                print("✅ Server connection successful")
            
            # Test tool list
            print("📋 Getting tool list...")
            tools_response = await client.post(
                f"{server_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                }
            )
            
            if tools_response.status_code == 200:
                tools_data = tools_response.json()
                print(f"✅ Tool list: {json.dumps(tools_data, indent=2, ensure_ascii=False)}")
            
            # Test image generation
            print("🎨 Testing image generation...")
            generate_response = await client.post(
                f"{server_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "generate_image",
                        "arguments": {
                            "prompt": "A simple red circle",
                            "size": "1024x1024"
                        }
                    }
                }
            )
            
            if generate_response.status_code == 200:
                result = generate_response.json()
                print(f"✅ Image generation test completed: {result.get('result', {}).get('content', [{}])[0].get('text', 'Unknown')}")
            else:
                print(f"❌ Image generation failed: {generate_response.status_code}")
                
        except Exception as e:
            print(f"❌ HTTP test failed: {str(e)}")


async def main():
    """Run HTTP tests"""
    print("🌐 Testing HTTP version of MCP server")
    print("⚠️  Please make sure to start HTTP server first: python src/http_server.py")
    
    await asyncio.sleep(1)  # Wait for user to read the prompt
    await test_http_mcp_server()
    
    print("✅ HTTP test completed!")


if __name__ == "__main__":
    asyncio.run(main())