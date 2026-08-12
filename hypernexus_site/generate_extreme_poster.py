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
        
        # Rainbow nebula colors
        try:
            r = int(128 + 127 * math.sin(wave1 + wave2 + x / 100))
            g = int(128 + 127 * math.sin(wave2 + wave3 + y / 120))
            b = int(128 + 127 * math.sin(wave3 + wave1 + dist / 80))
        except (ValueError, OverflowError):
            r, g, b = 128, 128, 128
        
        img.putpixel((x, y), (r, g, b))

# Layer 2: Add electric lightning bolts
for _ in range(20):
    x1 = random.randint(0, width)
    y1 = random.randint(0, height)
    for _ in range(random.randint(5, 15)):
        x2 = x1 + random.randint(-100, 100)
        y2 = y1 + random.randint(-50, 50)
        # Draw lightning with glow
        for thickness in range(5, 0, -1):
            alpha = 255 - (thickness * 50)
            draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, max(0, alpha)), width=thickness)
        x1, y1 = x2, y2

# Layer 3: Add neon grid
for i in range(0, width, 50):
    draw.line([(i, 0), (i, height)], fill=(0, 255, 255, 50), width=1)
for i in range(0, height, 50):
    draw.line([(0, i), (width, i)], fill=(255, 0, 255, 50), width=1)

# Layer 4: Add floating particles
for _ in range(500):
    x = random.randint(0, width)
    y = random.randint(0, height)
    size = random.randint(1, 5)
    color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
    draw.ellipse([x, y, x+size, y+size], fill=color)

# Apply blur for glow effect
img = img.filter(ImageFilter.GaussianBlur(radius=2))

# Layer 5: Add chromatic aberration (RGB split)
r, g, b = img.split()
r = r.transform(r.size, Image.AFFINE, (1, 0, 3, 0, 1, 0))
b = b.transform(b.size, Image.AFFINE, (1, 0, -3, 0, 1, 0))
img = Image.merge('RGB', (r, g, b))

# Layer 6: Add scanlines (VHS effect)
for y in range(0, height, 3):
    for x in range(width):
        pixel = img.getpixel((x, y))
        img.putpixel((x, y), (pixel[0]//2, pixel[1]//2, pixel[2]//2))

# Layer 7: Add glitch blocks
for _ in range(30):
    x = random.randint(0, width-100)
    y = random.randint(0, height-30)
    w = random.randint(20, 100)
    h = random.randint(5, 30)
    # Copy a random block and shift it
    block = img.crop((x, y, x+w, y+h))
    offset = random.randint(-50, 50)
    img.paste(block, (x+offset, y))

# Enhance colors
enhancer = ImageEnhance.Color(img)
img = enhancer.enhance(1.5)

enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(1.3)

# Try to load fonts
try:
    font_huge = ImageFont.truetype("arial.ttf", 100)
    font_large = ImageFont.truetype("arial.ttf", 70)
    font_medium = ImageFont.truetype("arial.ttf", 40)
    font_small = ImageFont.truetype("arial.ttf", 30)
except Exception:
    font_huge = ImageFont.load_default()
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Create text with multiple layers
draw = ImageDraw.Draw(img)

# Main title with glow effect
title = "MOST POWERFUL"
subtitle = "AI UPGRADE!"

# Draw glow layers
for offset in range(10, 0, -1):
    alpha = 255 - (offset * 25)
    draw.text((width/2 + offset, 150 + offset), title, font=font_large, fill=(0, 0, 0), anchor='mm')
    draw.text((width/2 - offset, 150 - offset), title, font=font_large, fill=(0, 0, 0), anchor='mm')

# Draw main text with gradient effect
for i in range(len(title)):
    x = width/2 - len(title)*20 + i*40
    hue = i / len(title)
    try:
        r = int(255 * (1 + math.sin(hue * 6.28)) / 2)
        g = int(255 * (1 + math.sin(hue * 6.28 + 2.09)) / 2)
        b = int(255 * (1 + math.sin(hue * 6.28 + 4.18)) / 2)
    except (ValueError, OverflowError):
        r, g, b = 255, 0, 0
    draw.text((x, 150), title[i], font=font_large, fill=(r, g, b), anchor='mm')

# Draw subtitle with neon effect
for offset in range(5, 0, -1):
    draw.text((width/2 + offset, 270 + offset), subtitle, font=font_huge, fill=(0, 0, 0), anchor='mm')
draw.text((width/2, 270), subtitle, font=font_huge, fill=(255, 255, 0), anchor='mm')

# Draw brand name
brand = "HYPERNEXUS"
for offset in range(3, 0, -1):
    draw.text((width/2 + offset, 380 + offset), brand, font=font_medium, fill=(0, 0, 0), anchor='mm')
draw.text((width/2, 380), brand, font=font_medium, fill=(0, 255, 255), anchor='mm')

# Draw features
features = "Local-First • Persistent Memory • Zero Downtime"
draw.text((width/2, 440), features, font=font_small, fill=(255, 255, 255), anchor='mm')

# Draw URL with fire effect
url = "hypernexus.site"
for i in range(len(url)):
    x = width/2 - len(url)*8 + i*16
    r = random.randint(200, 255)
    g = random.randint(100, 200)
    b = 0
    draw.text((x, 520), url[i], font=font_small, fill=(r, g, b), anchor='mm')

# Save
output_path = os.path.join(os.path.dirname(__file__), 'hypernexus_poster.jpg')
img.save(output_path, 'JPEG', quality=95)
print(f"EXTREME OG image saved to {output_path}")
