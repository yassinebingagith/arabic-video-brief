import re
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from arabic_video_brief.config import get_settings
from arabic_video_brief.media import _display_text, _wrap_rtl, _shape_line, _balance_wrap, sanitize_display_text

settings = get_settings()

font_path = settings.font_path
avatar_path = Path("assets/brand/profile_avatar.jpg")
banner_path = Path("assets/brand/youtube_banner.jpg")
frame_path = Path("scratch/ip_5_0s.png")
if not frame_path.exists():
    frame_path = Path("scratch/test_v2_render_1s.png")

source_frame = Image.open(frame_path).convert("RGB")
raw_video_crop = source_frame.crop((0, 0, 1080, 608))

avatar_img = Image.open(avatar_path).convert("RGBA")
banner_img = Image.open(banner_path).convert("RGBA")

title_text = "5 مستويات للتعافي من الصدمة: من الانهيار إلى النمو بعد الصدمة"
page_text = "يخرج البعض من حوادث أو خيانات أو حروب لا يعودوا منها إلا عالقين في لحظة الصدمة إلى الأبد، بينما يمر البعض الآخر بنفس التجربة ثم يصبحون بعد سنوات أهدأ وأحكم وأقدر على مواجهة الحياة"

def make_rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask

# =========================================================================
# CONCEPT 1: Brand Cushion (24px Margin, Neon Cyan-Gold Glow Trim, Glass Cards)
# =========================================================================
print("Rendering Concept 1: Brand Cushion...")
c1 = Image.new("RGBA", (1080, 1920), (5, 12, 21, 255))
d1 = ImageDraw.Draw(c1)

# Radial subtle ambient glow from center-top
for y in range(1920):
    ratio = y / 1920
    r = int(5 + 8 * ratio)
    g = int(12 + 15 * ratio)
    b = int(21 + 25 * ratio)
    d1.line([(0, y), (1080, y)], fill=(r, g, b, 255))

# Outer Margin Cushion (24px padding around 9:16 canvas)
m = 24
outer_box = (m, m, 1080 - m, 1920 - m)

# 3-Layer Gradient Neon Border (Electric Cyan #1AC8ED to Warm Gold #E8BC66)
for glow_i in range(5, 0, -1):
    alpha = int(45 / glow_i)
    d1.rounded_rectangle(
        (outer_box[0] - glow_i, outer_box[1] - glow_i, outer_box[2] + glow_i, outer_box[3] + glow_i),
        radius=36 + glow_i,
        outline=(26, 200, 237, alpha),
        width=1,
    )
d1.rounded_rectangle(outer_box, radius=36, outline=(26, 200, 237, 220), width=3)
# Corner Gold Accent Brackets on Outer Cushion
bracket_len = 60
# Top-Left
d1.line([(m + 10, m), (m + 10 + bracket_len, m)], fill=(245, 197, 24, 255), width=4)
d1.line([(m, m + 10), (m, m + 10 + bracket_len)], fill=(245, 197, 24, 255), width=4)
# Bottom-Right
d1.line([(1080 - m - 10 - bracket_len, 1920 - m), (1080 - m - 10, 1920 - m)], fill=(245, 197, 24, 255), width=4)
d1.line([(1080 - m, 1920 - m - 10 - bracket_len), (1080 - m, 1920 - m - 10)], fill=(245, 197, 24, 255), width=4)

# Top Video Container (1024 x 630 with r=28)
v_w, v_h = 1032, 630
v_x, v_y = m + 12, m + 16
vid_resized = raw_video_crop.resize((v_w, v_h), Image.Resampling.LANCZOS)
v_mask = make_rounded_mask((v_w, v_h), 28)
c1.paste(vid_resized, (v_x, v_y), v_mask)
d1.rounded_rectangle((v_x, v_y, v_x + v_w, v_y + v_h), radius=28, outline=(232, 188, 102, 160), width=2)

# Floating Glassmorphic RTL Badge on Video
b_w, b_h = 980, 100
b_x, b_y = (1080 - b_w) // 2, v_y + v_h - b_h - 16
badge = Image.new("RGBA", (b_w, b_h), (8, 16, 26, 225))
b_draw = ImageDraw.Draw(badge)
b_draw.rounded_rectangle((0, 0, b_w, b_h), radius=26, fill=(8, 16, 26, 225), outline=(26, 200, 237, 100), width=1)
# Add small capsule avatar
av_small = avatar_img.resize((68, 68), Image.Resampling.LANCZOS)
badge.paste(av_small, (b_w - 84, 16), av_small)
# Badge text: Title in Arabic RTL
f_badge_title = ImageFont.truetype(str(font_path), 26)
f_badge_meta = ImageFont.truetype(str(font_path), 19)
b_title_vis = _display_text("5 مستويات للتعافي من الصدمة: من الانهيار إلى النمو")
b_meta_vis = _display_text("IVEn  •  19:34 دقيقة  •  يوتيوب")
b_draw.text((b_w - 100 - b_draw.textbbox((0, 0), b_title_vis, font=f_badge_title)[2], 16), b_title_vis, font=f_badge_title, fill="#FFFFFF")
b_draw.text((b_w - 100 - b_draw.textbbox((0, 0), b_meta_vis, font=f_badge_meta)[2], 56), b_meta_vis, font=f_badge_meta, fill="#1AC8ED")
c1.paste(badge, (b_x, b_y), badge)

# Lower Brief Glassmorphic Card (1032 x 1180)
card_w, card_h = 1032, 1920 - (v_y + v_h) - m - 32
card_x, card_y = m + 12, v_y + v_h + 18
card1 = Image.new("RGBA", (card_w, card_h), (8, 15, 25, 235))
cd1 = ImageDraw.Draw(card1)
cd1.rounded_rectangle((0, 0, card_w, card_h), radius=32, fill=(8, 15, 25, 235), outline=(26, 200, 237, 60), width=2)

# Card Header Block
f_head = ImageFont.truetype(str(font_path), 32)
f_sub = ImageFont.truetype(str(font_path), 22)
f_body = ImageFont.truetype(str(font_path), 46)

h_vis = _display_text("فيديوهات وجب مشاهدتها على اليوتيوب")
s_vis = _display_text("النوع: علم النفس والنمو الذاتي")

# Centered Gold Category Pill
cat_pill_w = 400
cat_pill_h = 44
cd1.rounded_rectangle(((card_w - cat_pill_w) // 2, 36, (card_w + cat_pill_w) // 2, 36 + cat_pill_h), radius=22, fill=(245, 197, 24, 30), outline=(245, 197, 24, 180), width=1)
s_box = cd1.textbbox((0, 0), s_vis, font=f_sub)
sw = s_box[2] - s_box[0]
cd1.text(((card_w - sw) // 2, 44), s_vis, font=f_sub, fill="#F5C518")

# Main Header
h_box = cd1.textbbox((0, 0), h_vis, font=f_head)
hw = h_box[2] - h_box[0]
cd1.text(((card_w - hw) // 2, 98), h_vis, font=f_head, fill="#FFFFFF")

# Gold accent line
cd1.line([(card_w // 2 - 60, 150), (card_w // 2 + 60, 150)], fill=(26, 200, 237, 180), width=2)

# Body Paragraph
max_text_w = card_w - 96
lines = _wrap_rtl(page_text, f_body, max_text_w)
cur_ty = 230
line_h = math.ceil(46 * 1.65)
for line in lines:
    vis_l = _shape_line(line)
    lw = cd1.textbbox((0, 0), vis_l, font=f_body)[2]
    # Right align in card with 48px padding
    tx = card_w - 48 - lw
    cd1.text((tx, cur_ty), vis_l, font=f_body, fill="#F2F4F7")
    cur_ty += line_h

# Brand Watermark Pill at Bottom of Card
b_watermark_w, b_watermark_h = 320, 52
b_watermark_x = (card_w - b_watermark_w) // 2
b_watermark_y = card_h - 76
cd1.rounded_rectangle((b_watermark_x, b_watermark_y, b_watermark_x + b_watermark_w, b_watermark_y + b_watermark_h), radius=26, fill=(14, 25, 38, 220), outline=(26, 200, 237, 120), width=1)
f_wm = ImageFont.truetype(str(font_path), 20)
wm_vis = _display_text("كبسولة فكر  •  Capsule Fikr")
wm_box = cd1.textbbox((0, 0), wm_vis, font=f_wm)
cd1.text((b_watermark_x + (b_watermark_w - (wm_box[2] - wm_box[0])) // 2, b_watermark_y + 12), wm_vis, font=f_wm, fill="#E8BC66")

c1.paste(card1, (card_x, card_y), card1)

p1_out = Path("scratch/mockups/concept1_brand_cushion.png")
c1.convert("RGB").save(p1_out, format="PNG")
c1.convert("RGB").save(Path(r"C:\Users\User\.gemini\antigravity-ide\brain\68093872-fe44-473c-9451-d99fdc6f75c1\concept1_brand_cushion.png"), format="PNG")

# =========================================================================
# CONCEPT 2: Ambient Liquid Aurora (Moving 9:16 Canvas, 100% Non-Static Video Background)
# =========================================================================
print("Rendering Concept 2: Ambient Aurora Flow...")
c2 = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
# Full 1080x1920 ambient background from video crop, heavily blurred with brand teal/blue tint
ambient_bg = raw_video_crop.resize((1080, 1920), Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(radius=55))
blue_tint = Image.new("RGBA", (1080, 1920), (6, 20, 36, 175))
ambient_composite = Image.alpha_composite(ambient_bg.convert("RGBA"), blue_tint)
c2.paste(ambient_composite, (0, 0))

d2 = ImageDraw.Draw(c2)

# Outer 9:16 glowing brand line (Soft 2px cyan cushion border)
d2.rounded_rectangle((12, 12, 1068, 1908), radius=32, outline=(26, 200, 237, 140), width=2)
d2.rounded_rectangle((16, 16, 1064, 1904), radius=28, outline=(245, 197, 24, 70), width=1)

# Upper Sharp Video (Floating Window with Soft Cyan Aura)
sw_w, sw_h = 1016, 640
sw_x = (1080 - sw_w) // 2
sw_y = 56

# Drop shadow
sh = Image.new("RGBA", (sw_w + 60, sw_h + 60), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((30, 30, sw_w + 30, sw_h + 30), radius=36, fill=(0, 0, 0, 190))
sh = sh.filter(ImageFilter.GaussianBlur(22))
c2.paste(sh, (sw_x - 30, sw_y - 30), sh)

sw_vid = raw_video_crop.resize((sw_w, sw_h), Image.Resampling.LANCZOS)
sw_mask = make_rounded_mask((sw_w, sw_h), 28)
c2.paste(sw_vid, (sw_x, sw_y), sw_mask)
d2.rounded_rectangle((sw_x, sw_y, sw_x + sw_w, sw_y + sw_h), radius=28, outline=(26, 200, 237, 180), width=2)

# Bottom video gradient blend inside the video frame itself
# Floating Badge over sharp video
b2 = Image.new("RGBA", (sw_w - 40, 88), (6, 14, 24, 220))
b2_d = ImageDraw.Draw(b2)
b2_d.rounded_rectangle((0, 0, sw_w - 40, 88), radius=24, fill=(6, 14, 24, 220), outline=(232, 188, 102, 120), width=1)
b2.paste(avatar_img.resize((56, 56), Image.Resampling.LANCZOS), (sw_w - 40 - 72, 16), avatar_img.resize((56, 56), Image.Resampling.LANCZOS))
b2_title = _display_text("5 مستويات للتعافي من الصدمة")
b2_d.text((sw_w - 40 - 88 - b2_d.textbbox((0, 0), b2_title, font=f_badge_title)[2], 14), b2_title, font=f_badge_title, fill="#FFFFFF")
b2_meta = _display_text("IVEn  •  19:34 دقيقة")
b2_d.text((sw_w - 40 - 88 - b2_d.textbbox((0, 0), b2_meta, font=f_badge_meta)[2], 50), b2_meta, font=f_badge_meta, fill="#E8BC66")
c2.paste(b2, (sw_x + 20, sw_y + sw_h - 104), b2)

# Lower Brief Floating Glass Tablet (1016 x 1110)
tab_w, tab_h = 1016, 1110
tab_x = (1080 - tab_w) // 2
tab_y = sw_y + sw_h + 30

t_sh = Image.new("RGBA", (tab_w + 60, tab_h + 60), (0, 0, 0, 0))
ImageDraw.Draw(t_sh).rounded_rectangle((30, 30, tab_w + 30, tab_h + 30), radius=40, fill=(0, 0, 0, 200))
t_sh = t_sh.filter(ImageFilter.GaussianBlur(24))
c2.paste(t_sh, (tab_x - 30, tab_y - 30), t_sh)

tablet = Image.new("RGBA", (tab_w, tab_h), (4, 11, 20, 235))
td = ImageDraw.Draw(tablet)
td.rounded_rectangle((0, 0, tab_w, tab_h), radius=36, fill=(4, 11, 20, 235), outline=(245, 197, 24, 110), width=2)

# Gold Headline Pill
td.rounded_rectangle(((tab_w - cat_pill_w) // 2, 40, (tab_w + cat_pill_w) // 2, 40 + cat_pill_h), radius=22, fill=(245, 197, 24, 30), outline=(245, 197, 24, 190), width=1)
td.text(((tab_w - sw) // 2, 48), s_vis, font=f_sub, fill="#F5C518")

td.text(((tab_w - hw) // 2, 106), h_vis, font=f_head, fill="#FFFFFF")
td.line([(tab_w // 2 - 80, 160), (tab_w // 2 + 80, 160)], fill=(26, 200, 237, 180), width=2)

# Text Body
cur_ty2 = 230
for line in lines:
    vis_l = _shape_line(line)
    lw = td.textbbox((0, 0), vis_l, font=f_body)[2]
    tx = tab_w - 48 - lw
    td.text((tx, cur_ty2), vis_l, font=f_body, fill="#FFFFFF")
    cur_ty2 += line_h

# Footer in Tablet
f_footer = ImageFont.truetype(str(font_path), 24)
ft_vis = _display_text("اقرأ الوصف لمزيد من التفاصيل والخطوات العملية  👇")
ft_box = td.textbbox((0, 0), ft_vis, font=f_footer)
td.text(((tab_w - (ft_box[2] - ft_box[0])) // 2, tab_h - 70), ft_vis, font=f_footer, fill="#1AC8ED")

c2.paste(tablet, (tab_x, tab_y), tablet)

p2_out = Path("scratch/mockups/concept2_ambient_aurora.png")
c2.convert("RGB").save(p2_out, format="PNG")
c2.convert("RGB").save(Path(r"C:\Users\User\.gemini\antigravity-ide\brain\68093872-fe44-473c-9451-d99fdc6f75c1\concept2_ambient_aurora.png"), format="PNG")

# =========================================================================
# CONCEPT 3: Capsule Cosmic Ribbon (Integrated YouTube Banner Wave & Dual Gradients)
# =========================================================================
print("Rendering Concept 3: Capsule Cosmic Ribbon...")
c3 = Image.new("RGBA", (1080, 1920), (3, 8, 15, 255))
d3 = ImageDraw.Draw(c3)

for y in range(1920):
    ratio = y / 1920
    r = int(3 + 10 * ratio)
    g = int(8 + 16 * ratio)
    b = int(15 + 30 * ratio)
    d3.line([(0, y), (1080, y)], fill=(r, g, b, 255))

# Top Video (Full width 1080 x 680)
vid_top = raw_video_crop.resize((1080, 680), Image.Resampling.LANCZOS)
c3.paste(vid_top, (0, 0))

# Seamless Brand Lightwave Ribbon from Banner!
# Banner has beautiful golden & cyan sparkles and cosmic waves
b_w, b_h = banner_img.size
ribbon = banner_img.crop((0, 140, b_w, 580)).resize((1080, 260), Image.Resampling.LANCZOS)
c3.paste(ribbon, (0, 580), ribbon)

# Dual-Gradient Cushion Border along the 9:16 perimeter
# Left & Right borders: 18px glowing cyan/gold margin cushion
d3.rectangle((0, 0, 18, 1920), fill=(10, 26, 42, 255))
d3.rectangle((1080 - 18, 0, 1080, 1920), fill=(10, 26, 42, 255))
d3.line([(18, 0), (18, 1920)], fill=(26, 200, 237, 180), width=2)
d3.line([(1080 - 18, 0), (1080 - 18, 1920)], fill=(245, 197, 24, 180), width=2)
# Top & Bottom borders
d3.rectangle((0, 0, 1080, 18), fill=(10, 26, 42, 255))
d3.rectangle((0, 1920 - 18, 1080, 1920), fill=(10, 26, 42, 255))
d3.line([(0, 18), (1080, 18)], fill=(26, 200, 237, 180), width=2)
d3.line([(0, 1920 - 18), (1080, 1920 - 18)], fill=(245, 197, 24, 180), width=2)

# Central Brand Emblem Badge bridging the ribbon
brand_emblem = Image.new("RGBA", (440, 76), (5, 12, 22, 240))
be_d = ImageDraw.Draw(brand_emblem)
be_d.rounded_rectangle((0, 0, 440, 76), radius=38, fill=(5, 12, 22, 240), outline=(26, 200, 237, 200), width=2)
av_med = avatar_img.resize((60, 60), Image.Resampling.LANCZOS)
brand_emblem.paste(av_med, (440 - 68, 8), av_med)
f_emblem = ImageFont.truetype(str(font_path), 24)
emb_vis = _display_text("كبسولة فكر  |  ملخص مرئي")
be_d.text((32, 22), emb_vis, font=f_emblem, fill="#FFFFFF")
c3.paste(brand_emblem, ((1080 - 440) // 2, 790), brand_emblem)

# Lower Content Box
cur_ty3 = 910
# Category
d3.rounded_rectangle(((1080 - cat_pill_w) // 2, cur_ty3, (1080 + cat_pill_w) // 2, cur_ty3 + cat_pill_h), radius=22, fill=(245, 197, 24, 25), outline=(245, 197, 24, 180), width=1)
d3.text(((1080 - sw) // 2, cur_ty3 + 8), s_vis, font=f_sub, fill="#F5C518")
cur_ty3 += 64

# Main Header
d3.text(((1080 - hw) // 2, cur_ty3), h_vis, font=f_head, fill="#FFFFFF")
cur_ty3 += 60

# Body Text
for line in lines:
    vis_l = _shape_line(line)
    lw = d3.textbbox((0, 0), vis_l, font=f_body)[2]
    tx = 1080 - 58 - lw
    d3.text((tx, cur_ty3), vis_l, font=f_body, fill="#FFFFFF")
    cur_ty3 += line_h

# Footer
cur_ty3 += 30
d3.text(((1080 - (ft_box[2] - ft_box[0])) // 2, cur_ty3), ft_vis, font=f_footer, fill="#1AC8ED")

p3_out = Path("scratch/mockups/concept3_capsule_wave.png")
c3.convert("RGB").save(p3_out, format="PNG")
c3.convert("RGB").save(Path(r"C:\Users\User\.gemini\antigravity-ide\brain\68093872-fe44-473c-9451-d99fdc6f75c1\concept3_capsule_wave.png"), format="PNG")

print("All 3 concepts successfully rendered with full Arabic typography!")
