from PIL import Image
import os

# Optimize HyperNexus poster
print("Optimizing HyperNexus poster...")
img = Image.open('C:/Users/hyper/workspace/marketing_agent/hypernexus_site/hypernexus_poster.jpg')
img = img.resize((1200, 630), Image.Resampling.LANCZOS)
img.save('C:/Users/hyper/workspace/marketing_agent/hypernexus_site/hypernexus_poster_optimized.jpg', 'JPEG', quality=75, optimize=True)
print(f"Original: {os.path.getsize('C:/Users/hyper/workspace/marketing_agent/hypernexus_site/hypernexus_poster.jpg')} bytes")
print(f"Optimized: {os.path.getsize('C:/Users/hyper/workspace/marketing_agent/hypernexus_site/hypernexus_poster_optimized.jpg')} bytes")

# Optimize TormentNexus poster
print("\nOptimizing TormentNexus poster...")
img = Image.open('C:/Users/hyper/workspace/marketing_agent/tormentnexus_site/hypernexus_poster.jpg')
img = img.resize((1200, 630), Image.Resampling.LANCZOS)
img.save('C:/Users/hyper/workspace/marketing_agent/tormentnexus_site/og-image-optimized.png', 'PNG', optimize=True)
print(f"Original: {os.path.getsize('C:/Users/hyper/workspace/marketing_agent/tormentnexus_site/hypernexus_poster.jpg')} bytes")
print(f"Optimized: {os.path.getsize('C:/Users/hyper/workspace/marketing_agent/tormentnexus_site/og-image-optimized.png')} bytes")

print("\nDone!")
