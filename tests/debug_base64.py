#!/usr/bin/env python3
"""
Debug script to test if base64 data can be properly decoded and validated
"""

import base64
import io
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: PIL not installed. Install with: pip install pillow")
    exit(1)


def test_base64_data(base64_string):
    """Test if base64 data is valid image data"""
    print("\n" + "="*60)
    print("Base64 Image Data Validation Test")
    print("="*60)
    
    # Handle Data URL format
    if base64_string.startswith('data:'):
        print("\n1️⃣  Detected Data URL format")
        if ',' in base64_string:
            mime_type = base64_string.split(',')[0]
            base64_data = base64_string.split(',', 1)[1]
            print(f"   MIME type: {mime_type}")
            print(f"   Base64 length: {len(base64_data)}")
        else:
            print("❌ Invalid Data URL format: missing comma separator")
            return False
    else:
        print("\n1️⃣  Raw base64 format detected")
        base64_data = base64_string
        print(f"   Base64 length: {len(base64_data)}")
    
    # Try to decode
    print("\n2️⃣  Attempting to decode base64...")
    try:
        image_bytes = base64.b64decode(base64_data)
        print(f"✅ Decoded successfully")
        print(f"   Decoded size: {len(image_bytes)} bytes")
    except Exception as e:
        print(f"❌ Failed to decode: {e}")
        return False
    
    # Try to open with PIL
    print("\n3️⃣  Attempting to open with PIL...")
    try:
        img = Image.open(io.BytesIO(image_bytes))
        print(f"✅ Opened successfully")
        print(f"   Format: {img.format}")
        print(f"   Mode: {img.mode}")
        print(f"   Size: {img.size}")
        
        # Try to verify
        print("\n4️⃣  Verifying image integrity...")
        img.verify()
        print("✅ Image verification passed")
        
        # Re-open and save
        print("\n5️⃣  Attempting to save as PNG...")
        img_for_save = Image.open(io.BytesIO(image_bytes))
        output_path = Path("./test_decoded_image.png")
        img_for_save.save(output_path, format='PNG')
        print(f"✅ Saved to: {output_path.absolute()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to process image: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("Base64 Image Validation Tool")
    print("="*60)
    print("\nUsage:")
    print("  python tests/debug_base64.py")
    print("\nThis script will prompt you to paste your base64 data.")
    print("Supports both formats:")
    print("  - Raw: iVBORw0KGgoAAAANS...")
    print("  - Data URL: data:image/png;base64,iVBORw0KGgoAAAANS...")
    print("="*60 + "\n")
    
    # Check if base64 provided as argument
    if len(sys.argv) > 1:
        base64_input = sys.argv[1]
    else:
        print("Please paste your base64 string (can be multiline, press Ctrl+D when done):")
        print("-" * 60)
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        base64_input = ''.join(lines).strip()
    
    if not base64_input:
        print("❌ No input provided")
        exit(1)
    
    print(f"\nReceived {len(base64_input)} characters of input")
    
    success = test_base64_data(base64_input)
    
    print("\n" + "="*60)
    if success:
        print("🎉 Base64 data is valid!")
        print("\nYour image data should work with the HTTP server.")
    else:
        print("❌ Base64 data is invalid or corrupted")
        print("\nPossible issues:")
        print("  1. Data was not properly base64 encoded")
        print("  2. Image file is corrupted at the source")
        print("  3. Encoding/decoding error during transfer")
        print("\nSuggestions:")
        print("  - Try encoding the original image file again")
        print("  - Verify the original image opens correctly")
        print("  - Use a different image file")
    print("="*60 + "\n")
