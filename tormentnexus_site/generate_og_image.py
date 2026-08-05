from PIL import Image, ImageDraw, ImageFont
import os

# Create image
width, height = 1200, 630
img = Image.new('RGB', (width, height), color='#0a0a0a')
draw = ImageDraw.Draw(img)

# Try to load a monospace font
try:
    font_large = ImageFont.truetype("arial.ttf", 72)
    font_medium = ImageFont.truetype("arial.ttf", 48)
    font_small = ImageFont.truetype("arial.ttf", 36)
    font_tiny = ImageFont.truetype("arial.ttf", 24)
except Exception:
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()
    font_tiny = ImageFont.load_default()

# Draw text
draw.text((width/2, 180), "AT LONG LAST", font=font_medium, fill='#00ff88', anchor='mm')
draw.text((width/2, 300), "THE MACHINES AWAKEN", font=font_large, fill='#ff006e', anchor='mm')
draw.text((width/2, 420), "TormentNexus", font=font_small, fill='#ffffff', anchor='mm')
draw.text((width/2, 480), "Local-First AI Control Plane", font=font_tiny, fill='#888888', anchor='mm')
draw.text((width/2, 550), "tormentnexus.site", font=font_tiny, fill='#666666', anchor='mm')

# Save
output_path = os.path.join(os.path.dirname(__file__), 'og-image.png')
img.save(output_path, 'PNG')
print(f"OG image saved to {output_path}")
