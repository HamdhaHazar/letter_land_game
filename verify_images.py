import os
from PIL import Image

out_dir = r"d:\AI game\words_land\assets"
images = ["bird_happy.png", "bird_goodjob.png", "bird_sad.png", "bird_greeting.png"]

for name in images:
    path = os.path.join(out_dir, name)
    if os.path.exists(path):
        img = Image.open(path)
        w, h = img.size
        print(f"--- {name} ({w}x{h}) ---")
        # Check top row of pixels
        top_pixels = [img.getpixel((x, 0)) for x in range(w)]
        non_trans_top = [x for x, p in enumerate(top_pixels) if p[3] > 0]
        print(f"Non-transparent pixels in top row: {len(non_trans_top)} (indices: {non_trans_top[:20]}...)")
        
        # Check right column of pixels
        right_pixels = [img.getpixel((w-1, y)) for y in range(h)]
        non_trans_right = [y for y, p in enumerate(right_pixels) if p[3] > 0]
        print(f"Non-transparent pixels in rightmost column: {len(non_trans_right)} (indices: {non_trans_right[:20]}...)")
