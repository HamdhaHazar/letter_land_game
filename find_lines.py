from PIL import Image

src = r"d:\AI game\words_land\assets\bird_sheet.png.png"
img = Image.open(src).convert("RGBA")
W, H = img.size
print(f"Sheet size: {W}x{H}")

# Check columns for dark vertical lines (grid divider)
# Look around middle W // 2
for x in range(W // 2 - 20, W // 2 + 20):
    # Sample some pixels along y
    column_pixels = [img.getpixel((x, y)) for y in range(0, H, 10)]
    dark_pixels = [p for p in column_pixels if p[0] < 50 and p[1] < 50 and p[2] < 50]
    if len(dark_pixels) > 50:
        print(f"Potential vertical line at x = {x}")

# Check rows for dark horizontal lines (grid divider)
# Look around middle H // 2
for y in range(H // 2 - 20, H // 2 + 20):
    row_pixels = [img.getpixel((x, y)) for x in range(0, W, 10)]
    dark_pixels = [p for p in row_pixels if p[0] < 50 and p[1] < 50 and p[2] < 50]
    if len(dark_pixels) > 50:
        print(f"Potential horizontal line at y = {y}")
