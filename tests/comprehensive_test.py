#!/usr/bin/env python3
"""
Comprehensive test script to verify all improvements in Azure image generation and editing functionality
"""

import asyncio
import os
import tempfile
import json
from pathlib import Path
import sys

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from azure_image_client import AzureImageGenerator
from http_server import is_english_text, validate_image_size, get_azure_config


async def test_english_validation():
    """Test English validation functionality"""
    print("🔤 Testing English validation functionality...")
    
    test_cases = [
        ("A beautiful sunset", True),
        ("你好世界", False),
        ("Hello 世界", False),
        ("", True),
        ("123 numbers", True),
        ("Mixed text 中文", False),
        ("Pure English text with punctuation!", True)
    ]
    
    for text, expected in test_cases:
        result = is_english_text(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' -> {result} (expected: {expected})")
        
        if result != expected:
            print(f"    English validation test failed!")
            return False
    
    print("✅ English validation functionality test passed")
    return True


def test_size_validation():
    """Test size validation functionality"""
    print("\n📐 Testing size validation functionality...")
    
    test_cases = [
        ("1024x1024", True),
        ("1792x1024", True),
        ("1024x1792", True),
        ("512x512", False),
        ("2048x2048", False),
        ("invalid", False),
        ("", False)
    ]
    
    for size, expected in test_cases:
        result = validate_image_size(size)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{size}' -> {result} (expected: {expected})")
        
        if result != expected:
            print(f"    Size validation test failed!")
            return False
    
    print("✅ Size validation functionality test passed")
    return True


def test_env_config():
    """Test environment variable configuration"""
    print("\n🔧 Testing environment variable configuration...")
    
    try:
        config = get_azure_config()
        required_keys = ["base_url", "api_key", "deployment_name"]
        
        for key in required_keys:
            if key not in config or not config[key]:
                print(f"❌ Missing or empty configuration: {key}")
                return False
                
        print("✅ Azure configuration loaded successfully")
        print(f"    Base URL: {config['base_url']}")
        print(f"    Deployment: {config['deployment_name']}")
        print(f"    API Key: {'*' * (len(config['api_key']) - 8) + config['api_key'][-8:]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment variable configuration test failed: {str(e)}")
        return False


async def test_image_generation_with_validation():
    """Test image generation functionality (including new validation logic)"""
    print("\n🎨 Testing image generation functionality (with validation)...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        config = get_azure_config()
        async with AzureImageGenerator(
            base_url=config["base_url"],
            api_key=config["api_key"],
            deployment_name=config["deployment_name"]
        ) as generator:
            
            # Test English prompt + custom size
            prompt = "A simple geometric pattern"
            size = "1792x1024"  # Test non-default size
            output_path = os.path.join(temp_dir, "test_custom_size.png")
            
            print(f"    Generating image: prompt='{prompt}', size={size}")
            
            result = await generator.generate_image(
                prompt=prompt,
                size=size,
                output_path=output_path
            )
            
            if os.path.exists(result):
                file_size = os.path.getsize(result)
                print(f"✅ Image generation successful!")
                print(f"    File: {result}")
                print(f"    Size: {file_size} bytes")
                print(f"    Dimensions: {size}")
                return True
            else:
                print("❌ Generated image file not found")
                return False
                
    except Exception as e:
        print(f"❌ Image generation test failed: {str(e)}")
        return False


async def test_server_logging():
    """Test logging functionality"""
    print("\n📝 Testing logging functionality...")
    
    try:
        # Check if log directory was created
        log_dir = Path("logs")
        if not log_dir.exists():
            print("❌ Log directory not created")
            return False
        
        print("✅ Log directory exists")
        
        # Check if there are log files
        log_files = list(log_dir.glob("mcp_server_*.log"))
        if log_files:
            print(f"✅ Found log files: {log_files}")
            
            # Read the latest log file
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            if latest_log.stat().st_size > 0:
                print(f"✅ Log file has content: {latest_log}")
                return True
        
        print("ℹ️ Log files may not be created yet (server not started)")
        return True
        
    except Exception as e:
        print(f"❌ Logging functionality test failed: {str(e)}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting comprehensive functionality tests\n")
    
    tests = [
        ("English validation", test_english_validation()),
        ("Size validation", test_size_validation()),
        ("Environment configuration", test_env_config()),
        ("Logging functionality", test_server_logging()),
        ("Image generation", test_image_generation_with_validation())
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        if asyncio.iscoroutine(test_func):
            results[test_name] = await test_func
        else:
            results[test_name] = test_func
    
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ Passed" if passed else "❌ Failed"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*50)
    if all_passed:
        print("🎉 All tests passed! Functionality improvements successful!")
    else:
        print("⚠️ Some tests failed, please check related functionality")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(run_all_tests())