from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

# Create psychedelic background
width, height = 1200, 630
img = Image.new('RGB', (width, height))
draw = ImageDraw.Draw(img)

# Create rainbow psychedelic background
for y in range(height):
    for x in range(width):
        # Create swirling rainbow pattern
        angle = math.atan2(y - height/2, x - width/2)
        dist = math.sqrt((x - width/2)**2 + (y - height/2)**2)
        
        # Rainbow colors with psychedelic swirl
        hue = (angle / (2 * math.pi) + dist / 200 + x / 500) % 1.0
        saturation = 0.8 + 0.2 * math.sin(dist / 50)
        value = 0.6 + 0.4 * math.sin(dist / 100 + x / 200)
        
        # Convert HSV to RGB
        h = hue * 6
        i = int(h)
        f = h - i
        p = value * (1 - saturation)
        q = value * (1 - saturation * f)
        t = value * (1 - saturation * (1 - f))
        
        if i == 0:
            r, g, b = value, t, p
        elif i == 1:
            r, g, b = q, value, p
        elif i == 2:
            r, g, b = p, value, t
        elif i == 3:
            r, g, b = p, q, value
        elif i == 4:
            r, g, b = t, p, value
        else:
            r, g, b = value, p, q
        
        img.putpixel((x, y), (int(r * 255), int(g * 255), int(b * 255)))

# Add glow effect
img = img.filter(ImageFilter.GaussianBlur(radius=2))

# Try to load fonts
try:
    font_large = ImageFont.truetype("arial.ttf", 80)
    font_medium = ImageFont.truetype("arial.ttf", 48)
    font_small = ImageFont.truetype("arial.ttf", 36)
    font_tiny = ImageFont.truetype("arial.ttf", 28)
except Exception:
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()
    font_tiny = ImageFont.load_default()

# Create text overlay with dark background for readability
overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)

# Dark semi-transparent background for text
overlay_draw.rectangle((100, 150, width-100, height-150), fill=(0, 0, 0, 180))

# Convert to RGBA for compositing
img = img.convert('RGBA')
img = Image.alpha_composite(img, overlay)

# Draw text
draw = ImageDraw.Draw(img)

# Title with rainbow effect
title = "MOST POWERFUL AI UPGRADE!"
# Draw shadow
draw.text((width/2 + 3, 223), title, font=font_large, fill=(0, 0, 0, 200), anchor='mm')
# Draw main text
draw.text((width/2, 220), title, font=font_large, fill=(255, 255, 255, 255), anchor='mm')

# Subtitle
subtitle = "HYPERNEXUS"
draw.text((width/2 + 2, 332), subtitle, font=font_medium, fill=(0, 0, 0, 200), anchor='mm')
draw.text((width/2, 330), subtitle, font=font_medium, fill=(0, 255, 255, 255), anchor='mm')

# Features
features = "Local-First • Persistent Memory • Zero Downtime"
draw.text((width/2 + 2, 412), features, font=font_small, fill=(0, 0, 0, 200), anchor='mm')
draw.text((width/2, 410), features, font=font_small, fill=(255, 255, 0, 255), anchor='mm')

# URL
url = "hypernexus.site"
draw.text((width/2 + 2, 492), url, font=font_tiny, fill=(0, 0, 0, 200), anchor='mm')
draw.text((width/2, 490), url, font=font_tiny, fill=(255, 255, 255, 200), anchor='mm')

# Convert back to RGB
img = img.convert('RGB')

# Save
output_path = os.path.join(os.path.dirname(__file__), 'hypernexus_poster.jpg')
img.save(output_path, 'JPEG', quality=95)
print(f"Psychedelic OG image saved to {output_path}")
