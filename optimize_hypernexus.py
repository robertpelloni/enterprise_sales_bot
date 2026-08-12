from PIL import Image
import os

# Optimize HyperNexus poster
print("Optimizing HyperNexus poster...")
img = Image.open(
    "C:/Users/hyper/workspace/marketing_agent/hypernexus_site/hypernexus_poster.jpg"
)
img = img.resize((1200, 630), Image.Resampling.LANCZOS)
img.save(
    "C:/Users/hyper/workspace/marketing_agent/hypernexus_site/hypernexus_extreme.jpg",
    "JPEG",
    quality=80,
    optimize=True,
)
print(
    f"Original: {os.path.getsize('C:/Users/hyper/workspace/marketing_agent/hypernexus_site/hypernexus_poster.jpg')} bytes"
)
print(
    f"Optimized: {os.path.getsize('C:/Users/hyper/workspace/marketing_agent/hypernexus_site/hypernexus_extreme.jpg')} bytes"
)
print("Done!")
