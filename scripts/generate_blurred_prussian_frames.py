import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

base_frame_path = "scratch/ip_5_0s.png"
artifact_dir = r"C:\Users\User\.gemini\antigravity-ide\brain\68093872-fe44-473c-9451-d99fdc6f75c1"

base_img = Image.open(base_frame_path).convert("RGBA")

CANVAS_W = 1080
CANVAS_H = 1920

MARGIN_X = 54  # 5%
MARGIN_Y = 96  # 5%

INNER_W = CANVAS_W - (MARGIN_X * 2)  # 972
INNER_H = CANVAS_H - (MARGIN_Y * 2)  # 1728

# Resize the video frame to 972x1728
inner_resized = base_img.resize((INNER_W, INNER_H), Image.Resampling.LANCZOS)

# -------------------------------------------------------------------------
# VARIATION 1: Seamless Feathered Inner Edge (Soft Prussian Melt into Black)
# The frame is rich Prussian blue, and the inner border is feathered with a
# 40px Gaussian blur mask so it dissolves naturally into the video's black background.
# -------------------------------------------------------------------------
# Background: Pure black to deep Prussian gradient
bg1 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
# Create Prussian blue frame overlay
prussian_overlay1 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 49, 83, 255)) # #003153

# Cutout mask with heavily blurred feather
cutout_mask = Image.new("L", (CANVAS_W, CANVAS_H), 255)
mask_draw = ImageDraw.Draw(cutout_mask)
# Draw rounded inner rect with inset
mask_draw.rounded_rectangle(
    (MARGIN_X + 15, MARGIN_Y + 15, MARGIN_X + INNER_W - 15, MARGIN_Y + INNER_H - 15),
    radius=24,
    fill=0
)
# Heavy blur on the mask so the Prussian blue frame softly dissolves inward
feathered_mask1 = cutout_mask.filter(ImageFilter.GaussianBlur(35))
prussian_overlay1.putalpha(feathered_mask1)

var1 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
# Paste video centered
var1.paste(inner_resized, (MARGIN_X, MARGIN_Y))
# Composite the feathered Prussian frame on top so the blue softly bleeds over the video edges into black
var1 = Image.alpha_composite(var1, prussian_overlay1)
var1.convert("RGB").save(os.path.join(artifact_dir, "prussian_blur_opt1_feather_melt.png"), quality=95)
print("Variation 1 generated.")


# -------------------------------------------------------------------------
# VARIATION 2: Atmospheric Prussian Smoke Blur (Black Vignette + Luminous Blue)
# The outer margins start in deep black, softly blooming into radiant Prussian
# blue, then softly blurring into the black core of the video.
# -------------------------------------------------------------------------
var2 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 5, 12, 255))

# Create a glowing Prussian ring
glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow)
glow_draw.rounded_rectangle(
    (MARGIN_X - 10, MARGIN_Y - 10, MARGIN_X + INNER_W + 10, MARGIN_Y + INNER_H + 10),
    radius=40,
    outline=(0, 75, 128, 255), # Luminous Prussian
    width=60
)
glow = glow.filter(ImageFilter.GaussianBlur(50))
var2 = Image.alpha_composite(var2, glow)

# Feathered inner video mask so the video edges are soft
video_mask = Image.new("L", (INNER_W, INNER_H), 0)
vmask_draw = ImageDraw.Draw(video_mask)
vmask_draw.rounded_rectangle((10, 10, INNER_W - 10, INNER_H - 10), radius=28, fill=255)
video_mask = video_mask.filter(ImageFilter.GaussianBlur(18))

inner2 = inner_resized.copy()
inner2.putalpha(video_mask)
var2.paste(inner2, (MARGIN_X, MARGIN_Y), inner2)
var2.convert("RGB").save(os.path.join(artifact_dir, "prussian_blur_opt2_atmospheric_bloom.png"), quality=95)
print("Variation 2 generated.")


# -------------------------------------------------------------------------
# VARIATION 3: Diffused Ambient Cushion (Blurred Frame Tinted Prussian)
# Video scaled down, placed over a heavily blurred, Prussian-tinted ambient
# field that fades seamlessly to black at the edges.
# -------------------------------------------------------------------------
# Take inner video, scale to canvas, blur heavily (radius 80)
blurred_bg = base_img.resize((CANVAS_W, CANVAS_H), Image.Resampling.BILINEAR)
blurred_bg = blurred_bg.filter(ImageFilter.GaussianBlur(75))

# Tint the blurred background deeply with Prussian Blue (#002844)
tint = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 36, 64, 200))
blurred_bg = Image.alpha_composite(blurred_bg, tint)

# Soft vignette on the blurred bg towards black on outer borders
vignette = Image.new("L", (CANVAS_W, CANVAS_H), 0)
vign_draw = ImageDraw.Draw(vignette)
vign_draw.rectangle((0, 0, CANVAS_W, CANVAS_H), fill=255)
# Inset transparent center
vign_draw.rectangle((MARGIN_X, MARGIN_Y, CANVAS_W - MARGIN_X, CANVAS_H - MARGIN_Y), fill=0)
vignette = vignette.filter(ImageFilter.GaussianBlur(60))

darkness = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 180))
darkness.putalpha(vignette)
blurred_bg = Image.alpha_composite(blurred_bg, darkness)

# Soft rounded inner video with subtle shadow
var3 = blurred_bg.copy()
# Soft feather for inner video
vmask3 = Image.new("L", (INNER_W, INNER_H), 0)
ImageDraw.Draw(vmask3).rounded_rectangle((8, 8, INNER_W - 8, INNER_H - 8), radius=20, fill=255)
vmask3 = vmask3.filter(ImageFilter.GaussianBlur(10))

inner3 = inner_resized.copy()
inner3.putalpha(vmask3)
var3.paste(inner3, (MARGIN_X, MARGIN_Y), inner3)
var3.convert("RGB").save(os.path.join(artifact_dir, "prussian_blur_opt3_ambient_diffuse.png"), quality=95)
print("Variation 3 generated.")


# -------------------------------------------------------------------------
# VARIATION 4: Deep Black-to-Prussian Soft Radial Fog (Ultra-Organic Blend)
# A pitch black canvas with soft, foggy Prussian blue framing that fades
# gradually inward and outward, creating a completely seamless zero-border transition.
# -------------------------------------------------------------------------
var4 = Image.new("RGBA", (CANVAS_W, CANVAS_H), (2, 4, 8, 255)) # Near pure black

# Prussian fog layer
fog = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
fog_draw = ImageDraw.Draw(fog)
# Frame perimeter painted in Prussian
fog_draw.rectangle((0, 0, CANVAS_W, CANVAS_H), fill=(0, 45, 78, 255))
fog_draw.rectangle((MARGIN_X + 25, MARGIN_Y + 25, CANVAS_W - MARGIN_X - 25, CANVAS_H - MARGIN_Y - 25), fill=(0, 0, 0, 0))

# Massive blur to turn the Prussian frame into a smooth smoky transition between black and blue
fog = fog.filter(ImageFilter.GaussianBlur(70))

var4 = Image.alpha_composite(var4, fog)

# Put inner video with very gentle edge feather (radius 8) so text is 100% sharp but boundary dissolves
vmask4 = Image.new("L", (INNER_W, INNER_H), 0)
ImageDraw.Draw(vmask4).rounded_rectangle((4, 4, INNER_W - 4, INNER_H - 4), radius=16, fill=255)
vmask4 = vmask4.filter(ImageFilter.GaussianBlur(6))

inner4 = inner_resized.copy()
inner4.putalpha(vmask4)
var4.paste(inner4, (MARGIN_X, MARGIN_Y), inner4)
var4.convert("RGB").save(os.path.join(artifact_dir, "prussian_blur_opt4_soft_fog_dissolve.png"), quality=95)
print("Variation 4 generated.")

print("All 4 blurred Prussian variations generated successfully!")
