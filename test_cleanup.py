#!/usr/bin/env python3
"""
Test script to demonstrate the screenshot cleanup functionality.
This script creates test screenshots to verify the cleanup function works correctly.
"""

import os
import time
from PIL import Image
import numpy as np
from config import SCREENSHOTS_FOLDER

def create_test_screenshots(count=8):
    """Create test screenshots to demonstrate cleanup functionality"""
    os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)
    
    print(f"Creating {count} test screenshots...")
    
    for i in range(count):
        # Create a simple test image
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        # Save with timestamp-like filename
        timestamp = int(time.time()) + i
        filename = f"test_screenshot_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_FOLDER, filename)
        
        img.save(filepath)
        print(f"Created: {filename}")
        
        # Small delay to ensure different timestamps
        time.sleep(0.1)
    
    print(f"\nTest screenshots created in: {SCREENSHOTS_FOLDER}")
    print(f"Total files: {len([f for f in os.listdir(SCREENSHOTS_FOLDER) if f.endswith('.png')])}")
    print("\nNow run the main application and perform a capture to see the cleanup in action!")
    print("The cleanup function will keep only the last 5 screenshots.")

if __name__ == "__main__":
    create_test_screenshots()