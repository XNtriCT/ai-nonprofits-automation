"""
Standalone test for ChatGPT image generation.
Run this to test JUST the image generation without the full pipeline.
Debug screenshots are saved to downloads/ for each step.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import cfg, DOWNLOADS_DIR
from image_generator import generate_image, _clean_prompt

# A simple test prompt (short, to avoid issues)
TEST_PROMPT = (
    "A clean, minimalist top-down shot of a wooden desk. "
    "An open laptop showing a simple line chart trending upward. "
    "A coffee cup next to it. Natural window lighting. "
    "Text overlay in bold serif at top center: 'YOUR PROCESS IS BROKEN.' "
    "Beige and navy color palette. Editorial magazine style. 1:1 square."
)

if __name__ == "__main__":
    print("=" * 60)
    print("  ChatGPT Image Generation — Standalone Test")
    print("=" * 60)

    prompt = _clean_prompt(TEST_PROMPT)
    print(f"\nPrompt ({len(prompt)} chars):")
    print(f"  {prompt[:120]}...\n")

    output = os.path.join(DOWNLOADS_DIR, "test_generated.png")

    print("Starting image generation (Brave will open)...")
    print("Debug screenshots will appear in: downloads/debug_*.png\n")

    try:
        result = generate_image(prompt, output)
        if result and os.path.exists(result):
            size = os.path.getsize(result)
            print(f"\n✅ SUCCESS! Image saved to: {result}")
            print(f"   Size: {size} bytes ({size/1024:.1f} KB)")
        else:
            print(f"\n❌ FAILED: generate_image returned {result}")
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

    print("\nCheck downloads/debug_*.png for screenshots of each step.")
    print("Done.")
