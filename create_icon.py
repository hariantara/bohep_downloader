#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    # Create a 1024x1024 image with a blue background
    size = 1024
    img = Image.new('RGBA', (size, size), color=(0, 120, 212, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw a white circle
    circle_margin = 50
    draw.ellipse(
        [(circle_margin, circle_margin), (size - circle_margin, size - circle_margin)],
        fill=(255, 255, 255, 255)
    )
    
    # Draw text
    try:
        font = ImageFont.truetype("Arial Bold", 200)
    except IOError:
        font = ImageFont.load_default()
    
    text = "BD"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    text_position = ((size - text_width) // 2, (size - text_height) // 2 - 50)
    draw.text(text_position, text, fill=(0, 120, 212, 255), font=font)
    
    # Save as PNG
    img.save('icon.png')
    
    # Convert to ICNS (macOS icon format)
    os.system('mkdir icon.iconset')
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    for size in sizes:
        resized = img.resize((size, size), Image.LANCZOS)
        resized.save(f'icon.iconset/icon_{size}x{size}.png')
        if size <= 512:
            resized.save(f'icon.iconset/icon_{size}x{size}@2x.png')
    
    os.system('iconutil -c icns icon.iconset')
    os.system('rm -rf icon.iconset')
    
    print("Icon created successfully: icon.icns")

if __name__ == '__main__':
    create_icon() 