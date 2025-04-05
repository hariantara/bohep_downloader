#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    # Create a 1024x1024 image with a white background
    size = 1024
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a rounded rectangle
    margin = size // 8
    draw.rounded_rectangle(
        [(margin, margin), (size - margin, size - margin)],
        radius=size//8,
        fill='#007AFF'
    )
    
    # Add text
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size//8)
    except:
        font = ImageFont.load_default()
    
    text = "BD"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    draw.text((x, y), text, fill='white', font=font)
    
    # Create iconset directory
    os.makedirs("assets/icon.iconset", exist_ok=True)
    
    # Save different sizes
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for size in sizes:
        resized = image.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f'assets/icon.iconset/icon_{size}x{size}.png')
        if size <= 512:
            resized.save(f'assets/icon.iconset/icon_{size}x{size}@2x.png')
    
    # Convert to icns
    os.system('iconutil -c icns assets/icon.iconset -o assets/icon.icns')
    
    # Clean up
    os.system('rm -rf assets/icon.iconset')
    
    print("Icon created successfully at assets/icon.icns")

if __name__ == "__main__":
    create_icon() 