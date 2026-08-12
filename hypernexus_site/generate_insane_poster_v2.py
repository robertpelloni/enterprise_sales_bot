from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math
import random
import os

# Create INSANE psychedelic background
width, height = 1200, 630
img = Image.new('RGB', (width, height))
draw = ImageDraw.Draw(img)

# Layer 1: Deep space nebula background with MORE waves
for y in range(height):
    for x in range(width):
        angle = math.atan2(y - height/2, x - width/2)
        dist = math.sqrt((x - width/2)**2 + (y - height/2)**2)
        
        # Multiple overlapping waves for insane effect
        wave1 = math.sin(dist / 20 + x / 80) * 0.6
        wave2 = math.cos(angle * 5 + dist / 40) * 0.4
        wave3 = math.sin(x / 30 + y / 60) * 0.3
        wave4 = math.cos(dist / 15 + angle * 2) * 0.2
        
        # Rainbow nebula colors - MORE vibrant
        try:
            r = int(180 + 75 * math.sin(wave1 + wave2 + x / 80))
            g = int(180 + 75 * math.sin(wave2 + wave3 + y / 100))
            b = int(180 + 75 * math.sin(wave3 + wave4 + dist / 60))
        except (ValueError, OverflowError):
            r, g, b = 180, 180, 180
        
        img.putpixel((x, y), (r, g, b))

# Layer 2: Add MORE electric lightning bolts
for _ in range(50):
    x1 = random.randint(0, width)
    y1 = random.randint(0, height)
    for _ in range(random.randint(8, 25)):
        x2 = x1 + random.randint(-200, 200)
        y2 = y1 + random.randint(-100, 100)
        # Draw lightning with glow
        for thickness in range(10, 0, -1):
            color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
            draw.line([(x1, y1), (x2, y2)], fill=color, width=thickness)
        x1, y1 = x2, y2

# Layer 3: Add neon grid
for i in range(0, width, 30):
    draw.line([(i, 0), (i, height)], fill=(0, 255, 255, 40), width=2)
for i in range(0, height, 30):
    draw.line([(0, i), (width, i)], fill=(255, 0, 255, 40), width=2)

# Layer 4: Add MORE floating particles
for _ in range(1500):
    x = random.randint(0, width)
    y = random.randint(0, height)
    size = random.randint(2, 8)
    color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
    draw.ellipse([x, y, x+size, y+size], fill=color)

# Apply blur for glow effect
img = img.filter(ImageFilter.GaussianBlur(radius=4))

# Layer 5: Add chromatic aberration (RGB split) - MORE extreme
r, g, b = img.split()
r = r.transform(r.size, Image.AFFINE, (1, 0, 8, 0, 1, 0))
b = b.transform(b.size, Image.AFFINE, (1, 0, -8, 0, 1, 0))
img = Image.merge('RGB', (r, g, b))

# Layer 6: Add scanlines (VHS effect)
for y in range(0, height, 2):
    for x in range(width):
        pixel = img.getpixel((x, y))
        img.putpixel((x, y), (pixel[0]//2, pixel[1]//2, pixel[2]//2))

# Layer 7: Add MORE glitch blocks
for _ in range(80):
    x = random.randint(0, width-200)
    y = random.randint(0, height-60)
    w = random.randint(40, 200)
    h = random.randint(15, 60)
    block = img.crop((x, y, x+w, y+h))
    offset = random.randint(-100, 100)
    img.paste(block, (x+offset, y))

# Enhance colors - MORE vibrant
enhancer = ImageEnhance.Color(img)
img = enhancer.enhance(2.5)

enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(1.8)

# Try to load fonts - BIGGER sizes
try:
    font_huge = ImageFont.truetype("arial.ttf", 160)
    font_large = ImageFont.truetype("arial.ttf", 120)
    font_medium = ImageFont.truetype("arial.ttf", 70)
    font_small = ImageFont.truetype("arial.ttf", 40)
except Exception:
    font_huge = ImageFont.load_default()
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Create text with multiple layers
draw = ImageDraw.Draw(img)

def draw_text_with_outline(draw, position, text, font, fill, outline_color=(0, 0, 0), outline_width=4):
    """Draw text with black outline"""
    x, y = position
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color, anchor='mm')
    # Draw main text
    draw.text(position, text, font=font, fill=fill, anchor='mm')

def draw_rainbow_text(draw, position, text, font, outline_width=4):
    """Draw text with each letter a different color and black outline"""
    x, y = position
    # Calculate total width
    total_width = len(text) * 80  # Approximate width per character
    start_x = x - total_width // 2
    
    # Rainbow colors for each letter
    colors = [
        (255, 0, 0),      # Red
        (255, 127, 0),    # Orange
        (255, 255, 0),    # Yellow
        (0, 255, 0),      # Green
        (0, 0, 255),      # Blue
        (75, 0, 130),     # Indigo
        (148, 0, 211),    # Violet
        (255, 0, 127),    # Pink
        (0, 255, 255),    # Cyan
        (255, 0, 255),    # Magenta
    ]
    
    for i, char in enumerate(text):
        if char == ' ':
            continue
        char_x = start_x + i * 80
        color = colors[i % len(colors)]
        draw_text_with_outline(draw, (char_x, y), char, font, color, outline_width=outline_width)

# Draw "MOST" with rainbow colors - HUGE
draw_rainbow_text(draw, (width//2, 80), "MOST", font_huge)

# Draw "POWERFUL" with rainbow colors - HUGE
draw_rainbow_text(draw, (width//2, 220), "POWERFUL", font_huge)

# Draw "AI UPGRADE!" with fire effect - BIG
subtitle = "AI UPGRADE!"
for offset in range(25, 0, -1):
    draw.text((width/2 + offset, 370 + offset), subtitle, font=font_large, fill=(0, 0, 0), anchor='mm')
    draw.text((width/2 - offset, 370 - offset), subtitle, font=font_large, fill=(0, 0, 0), anchor='mm')

# Draw subtitle with fire gradient and black outline
for i in range(len(subtitle)):
    x = width/2 - len(subtitle)*35 + i*70
    r = random.randint(200, 255)
    g = random.randint(100, 200)
    b = 0
    draw_text_with_outline(draw, (x, 370), subtitle[i], font_large, (r, g, b))

# Draw HYPER in cyan with black outline
hyper_text = "HYPER"
for offset in range(15, 0, -1):
    draw.text((width/2 - 180 + offset, 480 + offset), hyper_text, font=font_medium, fill=(0, 0, 0), anchor='mm')
    draw.text((width/2 - 180 - offset, 480 - offset), hyper_text, font=font_medium, fill=(0, 0, 0), anchor='mm')
draw_text_with_outline(draw, (width/2 - 180, 480), hyper_text, font_medium, (0, 255, 255))

# Draw NEXUS in magenta with black outline
nexus_text = "NEXUS"
for offset in range(15, 0, -1):
    draw.text((width/2 + 180 + offset, 480 + offset), nexus_text, font=font_medium, fill=(0, 0, 0), anchor='mm')
    draw.text((width/2 + 180 - offset, 480 - offset), nexus_text, font=font_medium, fill=(0, 0, 0), anchor='mm')
draw_text_with_outline(draw, (width/2 + 180, 480), nexus_text, font_medium, (255, 0, 255))

# Draw features with black outline
features = "Local-First • Persistent Memory • Zero Downtime"
draw_text_with_outline(draw, (width//2, 560), features, font_small, (255, 255, 255))

# Save with HIGH quality
output_path = os.path.join(os.path.dirname(__file__), 'hypernexus_poster.jpg')
img.save(output_path, 'JPEG', quality=95)
print(f"INSANE OG image saved to {output_path}")
print(f"File size: {os.path.getsize(output_path)} bytes")
