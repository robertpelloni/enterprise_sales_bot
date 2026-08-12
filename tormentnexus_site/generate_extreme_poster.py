from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math
import random
import os

# Create EXTREME psychedelic background
width, height = 1200, 630
img = Image.new('RGB', (width, height))
draw = ImageDraw.Draw(img)

# Layer 1: Deep space nebula background
for y in range(height):
    for x in range(width):
        # Create nebula effect
        angle = math.atan2(y - height/2, x - width/2)
        dist = math.sqrt((x - width/2)**2 + (y - height/2)**2)
        
        # Multiple overlapping waves
        wave1 = math.sin(dist / 30 + x / 100) * 0.5
        wave2 = math.cos(angle * 3 + dist / 50) * 0.3
        wave3 = math.sin(x / 50 + y / 80) * 0.2
        
        # Dark cyberpunk colors (purple/blue/cyan)
        try:
            r = int(50 + 30 * math.sin(wave1 + wave2 + x / 100))
            g = int(20 + 20 * math.sin(wave2 + wave3 + y / 120))
            b = int(100 + 80 * math.sin(wave3 + wave1 + dist / 80))
        except (ValueError, OverflowError):
            r, g, b = 50, 20, 100
        
        img.putpixel((x, y), (r, g, b))

# Layer 2: Add electric lightning bolts
for _ in range(30):
    x1 = random.randint(0, width)
    y1 = random.randint(0, height)
    for _ in range(random.randint(5, 20)):
        x2 = x1 + random.randint(-150, 150)
        y2 = y1 + random.randint(-80, 80)
        # Draw lightning with glow
        for thickness in range(8, 0, -1):
            alpha = 255 - (thickness * 30)
            color = (random.randint(100, 255), 0, random.randint(200, 255))
            draw.line([(x1, y1), (x2, y2)], fill=color, width=thickness)
        x1, y1 = x2, y2

# Layer 3: Add neon grid
for i in range(0, width, 40):
    draw.line([(i, 0), (i, height)], fill=(255, 0, 255, 30), width=1)
for i in range(0, height, 40):
    draw.line([(0, i), (width, i)], fill=(0, 255, 255, 30), width=1)

# Layer 4: Add floating particles
for _ in range(800):
    x = random.randint(0, width)
    y = random.randint(0, height)
    size = random.randint(1, 6)
    color = (random.randint(200, 255), random.randint(0, 100), random.randint(200, 255))
    draw.ellipse([x, y, x+size, y+size], fill=color)

# Apply blur for glow effect
img = img.filter(ImageFilter.GaussianBlur(radius=3))

# Layer 5: Add chromatic aberration (RGB split)
r, g, b = img.split()
r = r.transform(r.size, Image.AFFINE, (1, 0, 5, 0, 1, 0))
b = b.transform(b.size, Image.AFFINE, (1, 0, -5, 0, 1, 0))
img = Image.merge('RGB', (r, g, b))

# Layer 6: Add scanlines (VHS effect)
for y in range(0, height, 2):
    for x in range(width):
        pixel = img.getpixel((x, y))
        img.putpixel((x, y), (pixel[0]//3, pixel[1]//3, pixel[2]//3))

# Layer 7: Add glitch blocks
for _ in range(50):
    x = random.randint(0, width-150)
    y = random.randint(0, height-50)
    w = random.randint(30, 150)
    h = random.randint(10, 50)
    # Copy a random block and shift it
    block = img.crop((x, y, x+w, y+h))
    offset = random.randint(-80, 80)
    img.paste(block, (x+offset, y))

# Layer 8: Add matrix rain effect
for _ in range(200):
    x = random.randint(0, width)
    y = random.randint(0, height)
    length = random.randint(10, 50)
    for i in range(length):
        if y + i < height:
            alpha = 255 - (i * 5)
            draw.text((x, y + i * 15), chr(random.randint(33, 126)), fill=(0, random.randint(150, 255), 0))

# Enhance colors
enhancer = ImageEnhance.Color(img)
img = enhancer.enhance(2.0)

enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(1.5)

# Try to load fonts
try:
    font_huge = ImageFont.truetype("arial.ttf", 120)
    font_large = ImageFont.truetype("arial.ttf", 80)
    font_medium = ImageFont.truetype("arial.ttf", 50)
    font_small = ImageFont.truetype("arial.ttf", 35)
except Exception:
    font_huge = ImageFont.load_default()
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Create text with multiple layers
draw = ImageDraw.Draw(img)

# Main title with glow effect
title = "AT LONG LAST"
subtitle = "THE MACHINES"
subtitle2 = "AWAKEN!"

# Draw glow layers
for offset in range(15, 0, -1):
    alpha = 255 - (offset * 15)
    draw.text((width/2 + offset, 120 + offset), title, font=font_large, fill=(0, 0, 0), anchor='mm')
    draw.text((width/2 - offset, 120 - offset), title, font=font_large, fill=(0, 0, 0), anchor='mm')

# Draw main text with neon effect
draw.text((width/2, 120), title, font=font_large, fill=(0, 255, 255), anchor='mm')

# Draw subtitle with fire effect
for offset in range(10, 0, -1):
    draw.text((width/2 + offset, 250 + offset), subtitle, font=font_huge, fill=(0, 0, 0), anchor='mm')
draw.text((width/2, 250), subtitle, font=font_huge, fill=(255, 0, 100), anchor='mm')

# Draw subtitle2 with lightning effect
for offset in range(8, 0, -1):
    draw.text((width/2 + offset, 380 + offset), subtitle2, font=font_huge, fill=(0, 0, 0), anchor='mm')
draw.text((width/2, 380), subtitle2, font=font_huge, fill=(255, 255, 0), anchor='mm')

# Draw brand name
brand = "TORMENTNEXUS"
for offset in range(3, 0, -1):
    draw.text((width/2 + offset, 470 + offset), brand, font=font_medium, fill=(0, 0, 0), anchor='mm')
draw.text((width/2, 470), brand, font=font_medium, fill=(255, 0, 255), anchor='mm')

# Draw URL with fire effect
url = "tormentnexus.site"
for i in range(len(url)):
    x = width/2 - len(url)*8 + i*16
    r = random.randint(200, 255)
    g = random.randint(50, 150)
    b = 0
    draw.text((x, 550), url[i], font=font_small, fill=(r, g, b), anchor='mm')

# Save
output_path = os.path.join(os.path.dirname(__file__), 'hypernexus_poster.jpg')
img.save(output_path, 'JPEG', quality=95)
print(f"EXTREME OG image saved to {output_path}")
