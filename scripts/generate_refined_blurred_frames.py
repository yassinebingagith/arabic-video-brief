import os
from PIL import Image, ImageDraw, ImageFilter

base_frame_path = "scratch/ip_5_0s.png"
artifact_dir = r"C:\Users\User\.gemini\antigravity-ide\brain\68093872-fe44-473c-9451-d99fdc6f75c1"

base_img = Image.open(base_frame_path).convert("RGBA")

CANVAS_W = 1080
CANVAS_H = 1920

MARGIN_X = 54  # 5%
MARGIN_Y = 96  # 5%

INNER_W = CANVAS_W - (MARGIN_X * 2)  # 972
INNER_H = CANVAS_H - (MARGIN_Y * 2)  # 1728

inner_resized = base_img.resize((INNER_W, INNER_H), Image.Resampling.LANCZOS)

# -------------------------------------------------------------------------
# OPTION 1: "Prussian Airbrush Melt" (Seamless Fade at 5% Boundary)
# Rich classic Prussian Blue (#00365C) in the 5% margin area that airbrushes /
# dissolves smoothly into the black canvas with a 45px Gaussian feather.
# -------------------------------------------------------------------------
opt1 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
opt1.paste(inner_resized, (MARGIN_X, MARGIN_Y))

overlay1 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 56, 96, 255)) # Rich Prussian Blue
mask1 = Image.new("L", (CANVAS_W, CANVAS_H), 255)
d1 = ImageDraw.Draw(mask1)
# Create inner transparent window, feathered heavily
d1.rounded_rectangle(
    (MARGIN_X + 15, MARGIN_Y + 15, CANVAS_W - MARGIN_X - 15, CANVAS_H - MARGIN_Y - 15),
    radius=25,
    fill=0
)
mask1 = mask1.filter(ImageFilter.GaussianBlur(38))
overlay1.putalpha(mask1)
opt1 = Image.alpha_composite(opt1, overlay1)
opt1.convert("RGB").save(os.path.join(artifact_dir, "prussian_blur_v1_airbrush_melt.png"), quality=95)
print("Option 1 saved.")


# -------------------------------------------------------------------------
# OPTION 2: "Radiant Prussian Glow" (Atmospheric Backlit Blue Fog)
# A luminous Prussian blue aura (#004C82) centered around the 5% perimeter
# that softly blurs inward into the black video and outward to deep black edges.
# -------------------------------------------------------------------------
opt2 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))

glow2 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
d2 = ImageDraw.Draw(glow2)
# Draw thick Prussian stroke right on the boundary
d2.rounded_rectangle(
    (MARGIN_X, MARGIN_Y, CANVAS_W - MARGIN_X, CANVAS_H - MARGIN_Y),
    radius=30,
    outline=(0, 80, 138, 255),
    width=70
)
glow2 = glow2.filter(ImageFilter.GaussianBlur(60))
opt2 = Image.alpha_composite(opt2, glow2)

# Soft feather for inner video so boundary is silky smooth
vmask2 = Image.new("L", (INNER_W, INNER_H), 0)
ImageDraw.Draw(vmask2).rounded_rectangle((10, 10, INNER_W - 10, INNER_H - 10), radius=22, fill=255)
vmask2 = vmask2.filter(ImageFilter.GaussianBlur(12))

inner2 = inner_resized.copy()
inner2.putalpha(vmask2)
opt2.paste(inner2, (MARGIN_X, MARGIN_Y), inner2)
opt2.convert("RGB").save(os.path.join(artifact_dir, "prussian_blur_v2_radiant_glow.png"), quality=95)
print("Option 2 saved.")


# -------------------------------------------------------------------------
# OPTION 3: "Prussian Ombre Fade" (Linear Gradient into Pitch Black)
# Solid Prussian Blue at the extreme screen margins (#003358) that smoothly
# fades into pitch black towards the inner content across a 60px gradient transition.
# -------------------------------------------------------------------------
opt3 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
opt3.paste(inner_resized, (MARGIN_X, MARGIN_Y))

overlay3 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 64, 110, 255)) # Vibrant Prussian
mask3 = Image.new("L", (CANVAS_W, CANVAS_H), 255)
d3 = ImageDraw.Draw(mask3)
d3.rectangle((MARGIN_X + 5, MARGIN_Y + 5, CANVAS_W - MARGIN_X - 5, CANVAS_H - MARGIN_Y - 5), fill=0)
mask3 = mask3.filter(ImageFilter.GaussianBlur(52))
overlay3.putalpha(mask3)
opt3 = Image.alpha_composite(opt3, overlay3)
opt3.convert("RGB").save(os.path.join(artifact_dir, "prussian_blur_v3_ombre_fade.png"), quality=95)
print("Option 3 saved.")


# -------------------------------------------------------------------------
# OPTION 4: "Deep Midnight Prussian Blur" (Subtle, Cinematic Velvet Dissolve)
# Deeper classical Prussian (#002846) with a tighter 24px feather.
# Retains maximum black depth while ensuring the frame is non-destructive and seamless.
# -------------------------------------------------------------------------
opt4 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
opt4.paste(inner_resized, (MARGIN_X, MARGIN_Y))

overlay4 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 46, 78, 255))
mask4 = Image.new("L", (CANVAS_W, CANVAS_H), 255)
d4 = ImageDraw.Draw(mask4)
d4.rounded_rectangle(
    (MARGIN_X + 8, MARGIN_Y + 8, CANVAS_W - MARGIN_X - 8, CANVAS_H - MARGIN_Y - 8),
    radius=18,
    fill=0
)
mask4 = mask4.filter(ImageFilter.GaussianBlur(26))
overlay4.putalpha(mask4)
opt4 = Image.alpha_composite(opt4, overlay4)
opt4.convert("RGB").save(os.path.join(artifact_dir, "prussian_blur_v4_midnight_velvet.png"), quality=95)
print("Option 4 saved.")

print("All 4 final blurred options successfully saved!")
