import asyncio
import base64
import io
from pathlib import Path
from PIL import Image

from backend.router.vision import _compress_image
from backend.agent.tools_registry import _execute_vision_async

def test_compression():
    print("[*] Testing _compress_image with 2000x3000 image...")
    img = Image.new('RGB', (2000, 3000), color = 'red')
    out = io.BytesIO()
    img.save(out, format="JPEG")
    b64_original = base64.b64encode(out.getvalue()).decode("utf-8")
    
    b64_compressed = _compress_image(b64_original)
    
    compressed_bytes = base64.b64decode(b64_compressed)
    img_compressed = Image.open(io.BytesIO(compressed_bytes))
    
    print(f"    Original Size: (2000, 3000)")
    print(f"    Compressed Size: {img_compressed.size}")
    
    if img_compressed.size[0] <= 1024 and img_compressed.size[1] <= 1024:
        print("    [+] PASS: Image compressed correctly.")
    else:
        print("    [!] FAIL: Image was not compressed under 1024x1024.")

async def test_path_extraction():
    print("[*] Testing path extraction with spaces...")
    # This path does not exist, but we want to see if the regex extracts it completely.
    query = 'Please analyze this diagram for me: "C:\\My Documents\\Engineering Diagrams\\P&ID_01.jpg" and output JSON'
    
    result = await _execute_vision_async(query)
    
    # It should fail with "Image file not found: C:\My Documents\Engineering Diagrams\P&ID_01.jpg"
    # instead of breaking at the space.
    if "Image file not found: C:\\My Documents\\Engineering Diagrams\\P&ID_01.jpg" in result.error:
        print("    [+] PASS: Quoted path with spaces extracted correctly.")
    else:
        print(f"    [!] FAIL: Unexpected error message: {result.error}")

if __name__ == "__main__":
    test_compression()
    asyncio.run(test_path_extraction())
