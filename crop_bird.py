import os
import numpy as np
from PIL import Image
from scipy.ndimage import label

src = r"d:\AI game\words_land\assets\bird_sheet.png.png"
out_dir = r"d:\AI game\words_land\assets"

img = Image.open(src).convert("RGBA")
W, H = img.size
print(f"Sheet size: {W}x{H}")

# Define coordinates based on the detected grid lines
# Vertical: 448-450, Horizontal: 599-601
# We crop slightly inside to avoid the grid lines completely
quadrants = {
    "bird_happy":    (5, 5, 443, 593),
    "bird_goodjob":  (455, 5, 891, 593),
    "bird_sad":      (5, 607, 443, 1161),
    "bird_greeting": (455, 607, 891, 1161)
}

def clean_quadrant(cropped_img):
    # Convert to numpy array
    arr = np.array(cropped_img) # shape (H, W, 4)
    h, w, c = arr.shape
    
    # 1. Floodfill from the corners to find the white background
    # Let's define "near-white" as R > 220, G > 220, B > 220
    is_white = (arr[:, :, 0] > 220) & (arr[:, :, 1] > 220) & (arr[:, :, 2] > 220)
    
    # Simple BFS flood-fill to find all connected background pixels starting from corners
    background = np.zeros((h, w), dtype=bool)
    queue = []
    # Add corners and edges to queue
    for x in range(w):
        queue.append((0, x))
        queue.append((h - 1, x))
    for y in range(h):
        queue.append((y, 0))
        queue.append((y, w - 1))
        
    for r, c_idx in queue:
        if is_white[r, c_idx] and not background[r, c_idx]:
            background[r, c_idx] = True
            
    # Run BFS
    head = 0
    while head < len(queue):
        r, c_idx = queue[head]
        head += 1
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c_idx + dc
            if 0 <= nr < h and 0 <= nc < w:
                if is_white[nr, nc] and not background[nr, nc]:
                    background[nr, nc] = True
                    queue.append((nr, nc))
                    
    # 2. Foreground is everything not background
    foreground = ~background
    
    # 3. Label connected components of the foreground
    labeled, num_features = label(foreground)
    if num_features == 0:
        return cropped_img
        
    # Find the largest connected component (the bird)
    sizes = np.bincount(labeled.ravel())
    # sizes[0] is background, so ignore it
    sizes[0] = 0
    largest_label = sizes.argmax()
    
    # 4. Create new array where only the largest component is kept, and all else is transparent background
    new_arr = arr.copy()
    mask = (labeled == largest_label)
    new_arr[~mask] = [255, 255, 255, 0] # Make non-bird pixels fully transparent
    
    # Make floodfilled background fully transparent as well
    new_arr[background] = [255, 255, 255, 0]
    
    # Convert back to PIL Image
    cleaned_img = Image.fromarray(new_arr, "RGBA")
    return cleaned_img

for name, box in quadrants.items():
    cropped = img.crop(box)
    cleaned = clean_quadrant(cropped)
    
    # Auto-trim transparent edges
    bbox = cleaned.getbbox()
    if bbox:
        cleaned = cleaned.crop(bbox)
        
    out_path = os.path.join(out_dir, f"{name}.png")
    cleaned.save(out_path, "PNG")
    print(f"Saved: {out_path} ({cleaned.size[0]}x{cleaned.size[1]})")

print("Done!")
