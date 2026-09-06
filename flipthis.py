from PIL import Image
import math

# 1. Configuration
IMAGE_PATH = "guns.png"
TILE_SIZE = 32         # Check your sheet: is a single gun box 16, 32, or 64 pixels?
PADDING = 16           # Extra blank space added to all 4 sides of every tile to stop overlaps
ROTATION_ANGLE = -45   # Change to 45 if it spins the wrong way

# Calculate the new, larger tile cell size
NEW_TILE_SIZE = TILE_SIZE + (PADDING * 2)

# 2. Open the image
src_sheet = Image.open(IMAGE_PATH).convert("RGBA")
src_w, src_h = src_sheet.size

cols = src_w // TILE_SIZE
rows = src_h // TILE_SIZE

# Create a brand new, larger canvas to fit the padded, rotated tiles
new_w = cols * NEW_TILE_SIZE
new_h = rows * NEW_TILE_SIZE
dst_sheet = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))

# 3. Process every gun individually
for r in range(rows):
    for c in range(cols):
        # Locate old box coordinates
        left = c * TILE_SIZE
        top = r * TILE_SIZE
        right = left + TILE_SIZE
        bottom = top + TILE_SIZE
        
        # Crop the gun out
        tile = src_sheet.crop((left, top, right, bottom))
        
        # Create an expanded, blank background tile for this specific gun
        padded_tile = Image.new("RGBA", (NEW_TILE_SIZE, NEW_TILE_SIZE), (0, 0, 0, 0))
        # Center the original gun sprite inside the new larger box before spinning
        padded_tile.paste(tile, (PADDING, PADDING))
        
        # Rotate the gun inside its new, roomy box (NEAREST preserves pixel art quality)
        rotated_tile = padded_tile.rotate(ROTATION_ANGLE, resample=Image.NEAREST)
        
        # Calculate where to place it on the new, clean grid layout
        new_left = c * NEW_TILE_SIZE
        new_top = r * NEW_TILE_SIZE
        
        # Paste it down safely
        dst_sheet.paste(rotated_tile, (new_left, new_top))

# 4. Save your new, perfectly separated asset sheet
dst_sheet.save("guns_fixed_padded_45.png")
print(f"Success! Generated a clean grid sheet. New cell size to type into Godot is: {NEW_TILE_SIZE}x{NEW_TILE_SIZE}")
