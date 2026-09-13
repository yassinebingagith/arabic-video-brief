import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import numpy as np

# Ensure fonts and assets exist
font_path = Path("assets/NotoSansArabic-SemiBold.ttf")
avatar_path = Path("assets/brand/profile_avatar.jpg")
banner_path = Path("assets/brand/youtube_banner.jpg")
frame_path = Path("scratch/ip_5_0s.png")

if not frame_path.exists():
    frame_path = Path("scratch/test_v2_render_1s.png")

source_frame = Image.open(frame_path).convert("RGB")
# The raw top video is 1080x608 or 1080x760
raw_video_crop = source_frame.crop((0, 0, 1080, 608))

avatar_img = Image.open(avatar_path).convert("RGBA")
banner_img = Image.open(banner_path).convert("RGBA")

# Colors
C_GOLD = "#F5C518"
C_BRAND_GOLD = "#E8BC66"
C_CYAN = "#1AC8ED"
C_CYAN_DEEP = "#0E7490"
C_NAVY_BG = "#050C15"
C_CARD_BG = (10, 20, 32, 220)

font_title = ImageFont.truetype(str(font_path), 32)
font_body = ImageFont.truetype(str(font_path), 46)
font_badge = ImageFont.truetype(str(font_path), 22)

scratch = Path("scratch/mockups")
scratch.mkdir(parents=True, exist_ok=True)
artifact_dir = Path(r"C:\Users\User\.gemini\antigravity-ide\brain\68093872-fe44-473c-9451-d99fdc6f75c1")

sample_p1 = "يخرج البعض من حوادث أو خيانات أو حروب لا يعودوا منها إلا عالقين في لحظة الصدمة إلى الأبد، بينما يمر البعض الآخر بنفس التجربة ثم يصبحون بعد سنوات أهدأ وأحكم وأقدر على مواجهة الحياة"

# Helper: rounded rectangle mask
def make_rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask

# Helper: simple RTL arabic text display (reversed for PIL default bidi without reshaper)
def rtl_text(text):
    import unicodedata
    # Basic word-level reverse for mockups
    words = text.split()
    return " ".join(reversed(words))

# =========================================================================
# CONCEPT 1: Brand Cushion (28px Margin, Neon Cyan-Gold Gradient Frame, Rounded Panels)
# =========================================================================
c1 = Image.new("RGBA", (1080, 1920), C_NAVY_BG)
draw1 = ImageDraw.Draw(c1)

# Subtle background gradient from #050C15 to #0B1928
for y in range(1920):
    r = int(5 + (11 - 5) * (y / 1920))
    g = int(12 + (25 - 12) * (y / 1920))
    b = int(21 + (40 - 21) * (y / 1920))
    draw1.line([(0, y), (1080, y)], fill=(r, g, b, 255))

# Outer Gradient Cushion Frame (Margin: 24px from edges)
margin = 24
outer_box = (margin, margin, 1080 - margin, 1920 - margin)
# Multi-layer glowing border
for i in range(4, 0, -1):
    alpha = int(70 / i)
    draw1.rounded_rectangle((outer_box[0] - i, outer_box[1] - i, outer_box[2] + i, outer_box[3] + i), radius=36 + i, outline=(26, 200, 237, alpha), width=1)
draw1.rounded_rectangle(outer_box, radius=36, outline=(26, 200, 237, 240), width=3)

# Top Video Container (inside margin: 1080 - 48 = 1032 width, h=620, r=28)
v_w, v_h = 1032, 620
v_x, v_y = margin + 12, margin + 16
scaled_vid = raw_video_crop.resize((v_w, v_h), Image.Resampling.LANCZOS)
v_mask = make_rounded_mask((v_w, v_h), 28)
c1.paste(scaled_vid, (v_x, v_y), v_mask)

# Video Border + Glow
draw1.rounded_rectangle((v_x, v_y, v_x + v_w, v_y + v_h), radius=28, outline=(232, 188, 102, 180), width=2)

# Floating metadata pill over video bottom
pill_w, pill_h = 960, 96
pill_x = (1080 - pill_w) // 2
pill_y = v_y + v_h - pill_h - 16
pill = Image.new("RGBA", (pill_w, pill_h), (10, 18, 28, 220))
p_draw = ImageDraw.Draw(pill)
p_draw.rounded_rectangle((0, 0, pill_w, pill_h), radius=24, fill=(10, 18, 28, 220), outline=(26, 200, 237, 120), width=1)
# Add small capsule logo icon
avatar_small = avatar_img.resize((64, 64), Image.Resampling.LANCZOS)
pill.paste(avatar_small, (pill_w - 80, 16), avatar_small)
c1.paste(pill, (pill_x, pill_y), pill)

# Lower Text Container (Frosted Glass Card)
c_w, c_h = 1032, 1920 - (v_y + v_h) - margin - 32
c_x, c_y = margin + 12, v_y + v_h + 20
card = Image.new("RGBA", (c_w, c_h), (8, 16, 26, 230))
cdraw = ImageDraw.Draw(card)
cdraw.rounded_rectangle((0, 0, c_w, c_h), radius=32, fill=(8, 16, 26, 230), outline=(26, 200, 237, 70), width=2)

# Decorative gold divider accent
cdraw.line([(c_w // 2 - 80, 28), (c_w // 2 + 80, 28)], fill=(245, 197, 24, 200), width=3)
c1.paste(card, (c_x, c_y), card)

c1.convert("RGB").save(scratch / "concept1_brand_cushion.png", format="PNG")
c1.convert("RGB").save(artifact_dir / "concept1_brand_cushion.png", format="PNG")
print("Concept 1 generated!")

# =========================================================================
# CONCEPT 2: Ambient Video Aurora (Dynamic 9:16 Motion Canvas, Eliminates All Borders)
# =========================================================================
c2 = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
# Scale video to fill full 1080x1920, heavily blur and tint with brand blue
bg_ambient = raw_video_crop.resize((1080, 1920), Image.Resampling.BICUBIC)
bg_ambient = bg_ambient.filter(ImageFilter.GaussianBlur(radius=45))
# Tint with brand cyan/navy
tint = Image.new("RGBA", (1080, 1920), (6, 18, 30, 190))
bg_ambient = Image.alpha_composite(bg_ambient.convert("RGBA"), tint)
c2.paste(bg_ambient, (0, 0))

draw2 = ImageDraw.Draw(c2)

# Sharp Video Window in Upper Focus Zone (Floating Glass Card)
vid_box_w, vid_box_h = 1016, 680
vid_box_x = (1080 - vid_box_w) // 2
vid_box_y = 60

# Diffuse Drop Shadow behind video
shadow = Image.new("RGBA", (vid_box_w + 40, vid_box_h + 40), (0, 0, 0, 0))
s_draw = ImageDraw.Draw(shadow)
s_draw.rounded_rectangle((20, 20, vid_box_w + 20, vid_box_h + 20), radius=32, fill=(0, 0, 0, 160))
shadow = shadow.filter(ImageFilter.GaussianBlur(16))
c2.paste(shadow, (vid_box_x - 20, vid_box_y - 20), shadow)

# Scaled sharp video
vid_sharp = raw_video_crop.resize((vid_box_w, vid_box_h), Image.Resampling.LANCZOS)
vid_mask = make_rounded_mask((vid_box_w, vid_box_h), 28)
c2.paste(vid_sharp, (vid_box_x, vid_box_y), vid_mask)
# Fine cyan/gold gradient border
draw2.rounded_rectangle((vid_box_x, vid_box_y, vid_box_x + vid_box_w, vid_box_y + vid_box_h), radius=28, outline=(26, 200, 237, 190), width=2)

# Lower Brief Floating Glass Tablet (1016 x 1060)
tab_w, tab_h = 1016, 1060
tab_x = (1080 - tab_w) // 2
tab_y = vid_box_y + vid_box_h + 30

tab_shadow = Image.new("RGBA", (tab_w + 40, tab_h + 40), (0, 0, 0, 0))
ts_draw = ImageDraw.Draw(tab_shadow)
ts_draw.rounded_rectangle((20, 20, tab_w + 20, tab_h + 20), radius=36, fill=(0, 0, 0, 180))
tab_shadow = tab_shadow.filter(ImageFilter.GaussianBlur(18))
c2.paste(tab_shadow, (tab_x - 20, tab_y - 20), tab_shadow)

tab_card = Image.new("RGBA", (tab_w, tab_h), (5, 12, 22, 235))
t_draw = ImageDraw.Draw(tab_card)
t_draw.rounded_rectangle((0, 0, tab_w, tab_h), radius=36, fill=(5, 12, 22, 235), outline=(245, 197, 24, 90), width=2)
# Add gold pill badge at top of tablet
p_badge_w, p_badge_h = 420, 48
p_badge_x = (tab_w - p_badge_w) // 2
t_draw.rounded_rectangle((p_badge_x, 24, p_badge_x + p_badge_w, 24 + p_badge_h), radius=24, fill=(245, 197, 24, 35), outline=(245, 197, 24, 160), width=1)

c2.paste(tab_card, (tab_x, tab_y), tab_card)

c2.convert("RGB").save(scratch / "concept2_ambient_aurora.png", format="PNG")
c2.convert("RGB").save(artifact_dir / "concept2_ambient_aurora.png", format="PNG")
print("Concept 2 generated!")

# =========================================================================
# CONCEPT 3: Capsule Wave Brand Identity (Integrated Ribbon & Golden Wave Accents)
# =========================================================================
c3 = Image.new("RGBA", (1080, 1920), C_NAVY_BG)
draw3 = ImageDraw.Draw(c3)

# Background deep navy gradient
for y in range(1920):
    ratio = y / 1920
    r = int(3 + (8 - 3) * ratio)
    g = int(7 + (16 - 7) * ratio)
    b = int(14 + (28 - 14) * ratio)
    draw3.line([(0, y), (1080, y)], fill=(r, g, b, 255))

# Top Video (Full width 1080 x 680 with soft bottom brand wave blend)
vid_c3 = raw_video_crop.resize((1080, 680), Image.Resampling.LANCZOS)
c3.paste(vid_c3, (0, 0))

# Seamless Wave Blend using the brand banner ribbons!
# Crop center wave ribbon from banner
b_w, b_h = banner_img.size
ribbon_crop = banner_img.crop((0, 150, b_w, 600)).resize((1080, 240), Image.Resampling.LANCZOS)
c3.paste(ribbon_crop, (0, 600), ribbon_crop)

# Subtle outer brand glow line around the entire 9:16 perimeter
draw3.rectangle((0, 0, 1079, 1919), outline=(26, 200, 237, 100), width=4)
draw3.rectangle((4, 4, 1075, 1915), outline=(245, 197, 24, 60), width=2)

# Floating Capsule Fikr Brand Pill Header at divider
brand_pill = Image.new("RGBA", (340, 72), (6, 14, 24, 240))
bp_draw = ImageDraw.Draw(brand_pill)
bp_draw.rounded_rectangle((0, 0, 340, 72), radius=36, fill=(6, 14, 24, 240), outline=(26, 200, 237, 180), width=2)
av_tiny = avatar_img.resize((56, 56), Image.Resampling.LANCZOS)
brand_pill.paste(av_tiny, (270, 8), av_tiny)
c3.paste(brand_pill, ((1080 - 340) // 2, 790), brand_pill)

c3.convert("RGB").save(scratch / "concept3_capsule_wave.png", format="PNG")
c3.convert("RGB").save(artifact_dir / "concept3_capsule_wave.png", format="PNG")
print("Concept 3 generated!")
