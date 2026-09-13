import os
import math
from PIL import Image, ImageDraw, ImageFilter

base_frame_path = "scratch/ip_5_0s.png"
artifact_dir = r"C:\Users\User\.gemini\antigravity-ide\brain\68093872-fe44-473c-9451-d99fdc6f75c1"

if not os.path.exists(base_frame_path):
    raise FileNotFoundError(f"Missing {base_frame_path}")

base_img = Image.open(base_frame_path).convert("RGBA")

# Target dimensions
CANVAS_W = 1080
CANVAS_H = 1920

# 5% margin on each side
MARGIN_X = int(CANVAS_W * 0.05)  # 54 px
MARGIN_Y = int(CANVAS_H * 0.05)  # 96 px

INNER_W = CANVAS_W - (MARGIN_X * 2)  # 972 px
INNER_H = CANVAS_H - (MARGIN_Y * 2)  # 1728 px

# High quality lanczos resize of the exact untouched video frame
inner_resized = base_img.resize((INNER_W, INNER_H), Image.Resampling.LANCZOS)

def create_rounded_mask(width, height, radius):
    mask = Image.new("L", (width * 4, height * 4), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width * 4, height * 4), radius=radius * 4, fill=255)
    return mask.resize((width, height), Image.Resampling.LANCZOS)

# -------------------------------------------------------------
# OPTION 1: Classic Pure Prussian Blue (Clean Matte Cushion)
# -------------------------------------------------------------
opt1 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 49, 83, 255)) # Prussian Blue #003153
# Crisp corner r=12
mask1 = create_rounded_mask(INNER_W, INNER_H, radius=14)
inner1 = inner_resized.copy()
inner1.putalpha(mask1)
opt1.paste(inner1, (MARGIN_X, MARGIN_Y), inner1)
opt1.convert("RGB").save(os.path.join(artifact_dir, "prussian_opt1_matte.png"), quality=95)
print("Option 1 generated.")

# -------------------------------------------------------------
# OPTION 2: Royal Prussian with Fine Gold Hairline
# -------------------------------------------------------------
opt2 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 49, 83, 255)) # Prussian Blue #003153
mask2 = create_rounded_mask(INNER_W, INNER_H, radius=18)
inner2 = inner_resized.copy()
inner2.putalpha(mask2)
opt2.paste(inner2, (MARGIN_X, MARGIN_Y), inner2)

# Draw elegant gold hairline around inner video
draw2 = ImageDraw.Draw(opt2)
# Gold accent color matching Arabic brand headers: #E2BA5B
draw2.rounded_rectangle(
    (MARGIN_X - 1, MARGIN_Y - 1, MARGIN_X + INNER_W, MARGIN_Y + INNER_H),
    radius=19,
    outline=(226, 186, 91, 230),
    width=2
)
opt2.convert("RGB").save(os.path.join(artifact_dir, "prussian_opt2_gold_hairline.png"), quality=95)
print("Option 2 generated.")

# -------------------------------------------------------------
# OPTION 3: Atmospheric Prussian Gradient with Soft Depth Shadow
# -------------------------------------------------------------
# Radial/Linear gradient from dark midnight prussian (0, 26, 46) at edges to luminous prussian (0, 56, 95)
opt3 = Image.new("RGBA", (CANVAS_W, CANVAS_H))
# Fast gradient generation using 1D gradient resized
grad_strip = Image.new("RGBA", (1, CANVAS_H))
for y in range(CANVAS_H):
    dist_norm = abs(y - CANVAS_H/2) / (CANVAS_H/2)
    # Blend between center (0, 58, 98) and edges (0, 22, 38)
    r = 0
    g = int(58 * (1 - dist_norm) + 22 * dist_norm)
    b = int(98 * (1 - dist_norm) + 38 * dist_norm)
    grad_strip.putpixel((0, y), (r, g, b, 255))
opt3 = grad_strip.resize((CANVAS_W, CANVAS_H), Image.Resampling.BILINEAR)

# Soft drop shadow behind inner video
shadow_canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
shadow_draw = ImageDraw.Draw(shadow_canvas)
shadow_draw.rounded_rectangle(
    (MARGIN_X - 4, MARGIN_Y - 4, MARGIN_X + INNER_W + 4, MARGIN_Y + INNER_H + 4),
    radius=22,
    fill=(0, 10, 20, 180)
)
shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(14))
opt3 = Image.alpha_composite(opt3, shadow_canvas)

mask3 = create_rounded_mask(INNER_W, INNER_H, radius=18)
inner3 = inner_resized.copy()
inner3.putalpha(mask3)
opt3.paste(inner3, (MARGIN_X, MARGIN_Y), inner3)
opt3.convert("RGB").save(os.path.join(artifact_dir, "prussian_opt3_shadow_gradient.png"), quality=95)
print("Option 3 generated.")

# -------------------------------------------------------------
# OPTION 4: Studio Broadcast Prussian (Double Inset Border)
# -------------------------------------------------------------
opt4 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 42, 72, 255)) # Deep Prussian Blue
draw4 = ImageDraw.Draw(opt4)

# Inset thin cyan-tinted Prussian pinstripe halfway through margin (24px from edge)
draw4.rectangle(
    (24, 38, CANVAS_W - 24, CANVAS_H - 38),
    outline=(10, 85, 135, 160),
    width=1
)

mask4 = create_rounded_mask(INNER_W, INNER_H, radius=12)
inner4 = inner_resized.copy()
inner4.putalpha(mask4)
opt4.paste(inner4, (MARGIN_X, MARGIN_Y), inner4)

# Fine inner edge border
draw4.rounded_rectangle(
    (MARGIN_X - 1, MARGIN_Y - 1, MARGIN_X + INNER_W, MARGIN_Y + INNER_H),
    radius=13,
    outline=(20, 95, 150, 180),
    width=1
)
opt4.convert("RGB").save(os.path.join(artifact_dir, "prussian_opt4_studio_pinstripe.png"), quality=95)
print("Option 4 generated.")

print("All 4 Prussian Blue Frame options successfully created!")
