from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random
import os
import numpy as np

# Create INSANE psychedelic background - OPTIMIZED with numpy
width, height = 1200, 630

# Generate nebula background using numpy (100x faster than pixel-by-pixel)
y_coords, x_coords = np.mgrid[0:height, 0:width]
angle = np.arctan2(y_coords - height / 2, x_coords - width / 2)
dist = np.sqrt((x_coords - width / 2) ** 2 + (y_coords - height / 2) ** 2)

# Multiple overlapping waves
wave1 = np.sin(dist / 20 + x_coords / 80) * 0.6
wave2 = np.cos(angle * 5 + dist / 40) * 0.4
wave3 = np.sin(x_coords / 30 + y_coords / 60) * 0.3
wave4 = np.cos(dist / 15 + angle * 2) * 0.2

# Rainbow nebula colors
r = (180 + 75 * np.sin(wave1 + wave2 + x_coords / 80)).astype(np.uint8)
g = (180 + 75 * np.sin(wave2 + wave3 + y_coords / 100)).astype(np.uint8)
b = (180 + 75 * np.sin(wave3 + wave4 + dist / 60)).astype(np.uint8)

# Stack into RGB array
pixels = np.stack([r, g, b], axis=-1)
img = Image.fromarray(pixels)
draw = ImageDraw.Draw(img)

# Layer 2: Add electric lightning bolts
for _ in range(50):
    x1, y1 = random.randint(0, width), random.randint(0, height)
    for _ in range(random.randint(8, 25)):
        x2 = x1 + random.randint(-200, 200)
        y2 = y1 + random.randint(-100, 100)
        color = (
            random.randint(200, 255),
            random.randint(200, 255),
            random.randint(200, 255),
        )
        draw.line([(x1, y1), (x2, y2)], fill=color, width=10)
        x1, y1 = x2, y2

# Layer 3: Add neon grid (using line drawing, not per-pixel)
for i in range(0, width, 30):
    draw.line([(i, 0), (i, height)], fill=(0, 255, 255), width=2)
for i in range(0, height, 30):
    draw.line([(0, i), (width, i)], fill=(255, 0, 255), width=2)

# Layer 4: Add floating particles (batch drawing)
for _ in range(1500):
    x, y = random.randint(0, width), random.randint(0, height)
    size = random.randint(2, 8)
    color = (
        random.randint(200, 255),
        random.randint(200, 255),
        random.randint(200, 255),
    )
    draw.ellipse([x, y, x + size, y + size], fill=color)

# Apply blur for glow effect
img = img.filter(ImageFilter.GaussianBlur(radius=4))

# Layer 5: Add chromatic aberration (RGB split) - using numpy for speed
img_array = np.array(img)
r_channel = np.roll(img_array[:, :, 0], 8, axis=1)
b_channel = np.roll(img_array[:, :, 2], -8, axis=1)
img_array[:, :, 0] = r_channel
img_array[:, :, 2] = b_channel
img = Image.fromarray(img_array)

# Layer 6: Add scanlines (VHS effect) - using numpy slicing (much faster)
img_array = np.array(img)
img_array[::2] = img_array[::2] // 2  # Darken every other row
img = Image.fromarray(img_array)

# Layer 7: Add glitch blocks
for _ in range(80):
    x = random.randint(0, width - 200)
    y = random.randint(0, height - 60)
    w = random.randint(40, 200)
    h = random.randint(15, 60)
    block = img.crop((x, y, x + w, y + h))
    offset = random.randint(-100, 100)
    img.paste(block, (x + offset, y))

# Enhance colors
img = ImageEnhance.Color(img).enhance(2.5)
img = ImageEnhance.Contrast(img).enhance(1.8)

# Load fonts - Impact for chunky letters
try:
    font_huge = ImageFont.truetype("impact.ttf", 180)
    font_large = ImageFont.truetype("impact.ttf", 130)
    font_medium = ImageFont.truetype("impact.ttf", 80)
    font_small = ImageFont.truetype("arial.ttf", 40)
except Exception:
    try:
        font_huge = ImageFont.truetype("arialbd.ttf", 180)
        font_large = ImageFont.truetype("arialbd.ttf", 130)
        font_medium = ImageFont.truetype("arialbd.ttf", 80)
        font_small = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font_huge = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

draw = ImageDraw.Draw(img)


def draw_text_with_outline(
    draw, position, text, font, fill, outline_color=(0, 0, 0), outline_width=5
):
    """Draw text with thick black outline"""
    x, y = position
    # Draw outline using single pass with offset loop
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text(
                    (x + dx, y + dy), text, font=font, fill=outline_color, anchor="mm"
                )
    draw.text(position, text, font=font, fill=fill, anchor="mm")


def draw_rainbow_text(draw, position, text, font, outline_width=5):
    """Draw text with each letter a different color and thick black outline"""
    x, y = position
    total_width = len(text) * 100
    start_x = x - total_width // 2

    colors = [
        (255, 0, 0),
        (255, 127, 0),
        (255, 255, 0),
        (0, 255, 0),
        (0, 0, 255),
        (75, 0, 130),
        (148, 0, 211),
        (255, 0, 127),
        (0, 255, 255),
        (255, 0, 255),
    ]

    for i, char in enumerate(text):
        if char == " ":
            continue
        char_x = start_x + i * 100
        color = colors[i % len(colors)]
        draw_text_with_outline(
            draw, (char_x, y), char, font, color, outline_width=outline_width
        )


# Draw "MOST" with rainbow colors
draw_rainbow_text(draw, (width // 2, 80), "MOST", font_huge)

# Draw "POWERFUL" with rainbow colors
draw_rainbow_text(draw, (width // 2, 230), "POWERFUL", font_huge)

# Draw "AI UPGRADE!" with fire effect
subtitle = "AI UPGRADE!"
for offset in range(25, 0, -1):
    draw.text(
        (width / 2 + offset, 380 + offset),
        subtitle,
        font=font_large,
        fill=(0, 0, 0),
        anchor="mm",
    )
    draw.text(
        (width / 2 - offset, 380 - offset),
        subtitle,
        font=font_large,
        fill=(0, 0, 0),
        anchor="mm",
    )

for i in range(len(subtitle)):
    x = width / 2 - len(subtitle) * 40 + i * 80
    r = random.randint(200, 255)
    g = random.randint(100, 200)
    draw_text_with_outline(draw, (x, 380), subtitle[i], font_large, (r, g, 0))

# Draw HYPER in cyan
hyper_text = "HYPER"
for offset in range(15, 0, -1):
    draw.text(
        (width / 2 - 200 + offset, 500 + offset),
        hyper_text,
        font=font_medium,
        fill=(0, 0, 0),
        anchor="mm",
    )
    draw.text(
        (width / 2 - 200 - offset, 500 - offset),
        hyper_text,
        font=font_medium,
        fill=(0, 0, 0),
        anchor="mm",
    )
draw_text_with_outline(
    draw, (width / 2 - 200, 500), hyper_text, font_medium, (0, 255, 255)
)

# Draw NEXUS in magenta
nexus_text = "NEXUS"
for offset in range(15, 0, -1):
    draw.text(
        (width / 2 + 200 + offset, 500 + offset),
        nexus_text,
        font=font_medium,
        fill=(0, 0, 0),
        anchor="mm",
    )
    draw.text(
        (width / 2 + 200 - offset, 500 - offset),
        nexus_text,
        font=font_medium,
        fill=(0, 0, 0),
        anchor="mm",
    )
draw_text_with_outline(
    draw, (width / 2 + 200, 500), nexus_text, font_medium, (255, 0, 255)
)

# Draw features
features = "Local-First • Persistent Memory • Zero Downtime"
draw_text_with_outline(draw, (width // 2, 580), features, font_small, (255, 255, 255))

# Save
output_path = os.path.join(os.path.dirname(__file__), "hypernexus_poster.jpg")
img.save(output_path, "JPEG", quality=95)
print(f"CHUNKY OG image saved to {output_path}")
print(f"File size: {os.path.getsize(output_path)} bytes")
