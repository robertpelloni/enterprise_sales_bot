from PIL import Image
import os

# Optimize TormentNexus poster as JPEG (smaller file size)
print("Optimizing TormentNexus poster as JPEG...")
img = Image.open(
    "C:/Users/hyper/workspace/marketing_agent/tormentnexus_site/hypernexus_poster.jpg"
)
img = img.resize((1200, 630), Image.Resampling.LANCZOS)
img.save(
    "C:/Users/hyper/workspace/marketing_agent/tormentnexus_site/og-image-optimized.jpg",
    "JPEG",
    quality=75,
    optimize=True,
)
print(
    f"Original: {os.path.getsize('C:/Users/hyper/workspace/marketing_agent/tormentnexus_site/hypernexus_poster.jpg')} bytes"
)
print(
    f"Optimized: {os.path.getsize('C:/Users/hyper/workspace/marketing_agent/tormentnexus_site/og-image-optimized.jpg')} bytes"
)

print("\nDone!")
