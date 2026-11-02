"""Production Python whiteboard pages and self-contained editable episode packages."""
from __future__ import annotations
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from .config import Settings
from .whiteboard_strokes import writing_strokes

ENGINE = "python-whiteboard"

DEFAULT_MOTION = {"first_delay":.45,"other_delay":.12,"final_hold":.8,"fade":.18,"marker_duration":.38}

def shaped(text):
    return get_display(arabic_reshaper.reshape(text),base_dir="R")

def write_json(file, data):
    Path(file).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

class WhiteboardProject:

    def __init__(self, output, settings, version, source, thumbnail, pages, metadata=None, selected_clip=None, title="", ending="", editorial=None, hook=None):
        self.root=Path(os.environ.get("AVBRIEF_RENDER_PROJECT",Path(output).parent / "render-project")).resolve()
        self.root.mkdir(parents=True,exist_ok=True)
        self.settings=settings
        self.ffmpeg=None
        self.aliases={}
        prior={}
        if (self.root / "project.json").is_file():
            prior=json.loads((self.root / "project.json").read_text(encoding="utf-8"))
        self.data={"schema":1,"renderer":ENGINE,"version":version,"settings":asdict(settings),
                   "motion":prior.get("motion",DEFAULT_MOTION.copy()),"pages":[],"texts":list(pages),
                   "metadata":metadata or {},"selected_clip":selected_clip or {},"title":title,"ending":ending,
                   "editorial":editorial or {},"assets":{},"font_sizes":[]}
        self.asset("font",settings.font_path,"font.ttf")
        self.asset("font_license",settings.font_path.parent / "OFL.txt","OFL.txt")
        self.asset("source",source,"source"+Path(source).suffix)
        self.asset("thumbnail",thumbnail,"thumbnail"+Path(thumbnail).suffix if thumbnail else "thumbnail.png")
        self.asset("frame",settings.brand_frame_path,"frame.png")
        self.asset("avatar",settings.brand_avatar_path,"avatar"+settings.brand_avatar_path.suffix)
        self.asset("hook",hook,"hook.mp3")
        self.bundle()

    def asset(self, key, source, name):
        if source is None or not Path(source).is_file():
            return None
        target=self.root / "assets" / name
        target.parent.mkdir(parents=True,exist_ok=True)
        source=Path(source).resolve()
        if source!=target.resolve():
            shutil.copy2(source,target)
        relative=target.relative_to(self.root).as_posix()
        self.data["assets"][key]=relative
        self.aliases[str(source)]=relative
        return target

    def bundle(self):
        source=Path(__file__).resolve().parent
        target=self.root / "engine" / "arabic_video_brief"
        if source!=target.resolve():
            shutil.copytree(source,target,dirs_exist_ok=True,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
        (self.root / "render.py").write_text(
            'from pathlib import Path\nimport sys\n'
            'sys.path.insert(0,str(Path(__file__).resolve().parent / "engine"))\n'
            'from arabic_video_brief.whiteboard import replay_project\n'
            'if __name__ == "__main__": replay_project(Path(__file__).resolve().parent)\n',encoding="utf-8")
        (self.root / "requirements.txt").write_text("Pillow>=11\nnumpy>=2\nopencv-python-headless>=4.11\narabic-reshaper>=3\npython-bidi>=0.6.6\nimageio-ffmpeg>=0.6\nstatic-ffmpeg==3.0\n",encoding="utf-8")
        (self.root / "README.md").write_text(
            "# Editable Python whiteboard episode\n\n"
            "All paths in project.json and export.json are relative to this folder. No browser or JavaScript runtime is needed.\n\n"
            "Edit the Arabic paragraphs in project.json (`texts`), title/ending, motion values, or timing settings. "
            "Run `python -m pip install -r requirements.txt` once, then `python render.py --output ../CapCut_1080p_whiteboard_rerender.mp4`. "
            "The bundled engine rebuilds layout, glyph masks, animated pages, source panel and the complete video with the original audio/export settings. "
            "Existing files require --overwrite. FFmpeg/FFprobe are discovered locally or fetched by the Python media installer.\n\n"
            "assets/ retains source footage, thumbnail, font, branding, chosen music, hook and outro when present; pages/ retains editable motion/glyph data and lossless page videos. "
            "export.json records the final compositor arguments. No .env, browser session or API credentials are bundled.\n",encoding="utf-8")

    def page(self, index, text, start, end, title=None, category=None):
        from .media import create_v2_summary_background, render_text_page
        folder=self.root / "pages" / f"page-{index}"
        folder.mkdir(parents=True,exist_ok=True)
        layout={}
        settled=folder / "settled.png"
        if self.data["version"]=="v1":
            render_text_page(text,settled,self.settings,main_title=title,
                header="فيديوهات وجب مشاهدتها على اليوتيوب" if index==1 else None,
                sub_header=f"النوع: {category}" if index==1 and category else None,_layout=layout)
        else:
            from .v2.renderer import render_v2_summary_page
            render_v2_summary_page(text,index,settled,self.settings,main_title=title,category=category,_layout=layout)
        crop=(0,self.settings.top_height,self.settings.width,self.settings.height)
        layout["base"].crop(crop).save(folder / "base.png")
        create_v2_summary_background(self.settings.width,self.settings.height,self.settings.top_height).crop(crop).save(folder / "background.png")
        draw=ImageDraw.Draw(Image.new("L",(1,1)))
        words=[]
        markers=[]
        for segments in layout["lines"]:
            for seg in segments:
                font=seg["font"]
                pieces=re.findall(r"\S+|\s+",seg["text"])
                widths=[draw.textlength(piece if piece.isspace() else shaped(piece),font=font) for piece in pieces]
                factor=seg["width"]/max(1,sum(widths))
                right=float(seg["x"]+seg["width"])
                mark_words=[]
                for piece, width in zip(pieces,widths):
                    left=right-width*factor
                    if piece.strip():
                        visual=shaped(piece)
                        box=draw.textbbox((0,0),visual,font=font)
                        glyph=Image.new("L",(max(1,box[2]-box[0]),max(1,box[3]-box[1])))
                        ImageDraw.Draw(glyph).text((-box[0],-box[1]),visual,font=font,fill=255)
                        guides=writing_strokes(piece,font,visual,width,math.ceil(layout["font_size"]*2.2))
                        for guide in guides:
                            guide["points"]=[[x-box[0],y-box[1]] for x,y in guide["points"]]
                        # Preserve original segment advances, including Arabic spacing.
                        scaled=max(1,round(glyph.width*factor))
                        if scaled!=glyph.width:
                            glyph=glyph.resize((scaled,glyph.height),Image.Resampling.LANCZOS)
                            for guide in guides:
                                guide["points"]=[[x*factor,y] for x,y in guide["points"]]
                        name=f"word-{len(words):03}.png"
                        glyph.save(folder/name)
                        words.append({"text":piece,"mask":name,"xy":[round(left+box[0]*factor),round(seg["y"]+box[1]-self.settings.top_height)],
                                      "strokes":guides,"brush_width":max(6,round(font.size*.29))})
                        mark_words.append(len(words)-1)
                    right=left
                if seg["is_hl"] and mark_words:
                    box=draw.textbbox((seg["x"],seg["y"]),seg["vis"],font=font)
                    markers.append({"words":mark_words,"box":[round(box[0]-10),round(box[1]-2-self.settings.top_height),round(box[2]+10),round(box[3]+4-self.settings.top_height)]})
        duration = round(end - start, 6)
        motion=self.data["motion"]
        is_v2 = (self.data.get("version") == "v2")
        if is_v2:
                        # V2: Instant Paragraph Fade + Highlighter Sweep
            # Pre-wrapped paragraph laid out in full; all words start at 0.0 with locked positions
            for word in words:
                word.update(start=0.0, end=0.0)
            # Highlighter sweep: starts at 1.5s, animates RTL across key phrase over 0.6s
            marker_start = 1.5
            marker_dur = 0.6
            for marker_index, marker in enumerate(markers):
                marker.update(start=marker_start, duration=marker_dur)
                for n in marker["words"]:
                    words[n]["marker"] = marker_index
        else:
            delay=min(motion["first_delay"] if index==1 else motion["other_delay"],duration*.15)
            finish=duration-min(motion["final_hold"],duration*.2)
            weights=[max(1,len(re.sub(r"[^\w]","",w["text"])))**.5+(.8 if re.search(r"[.،؛؟!]$",w["text"]) else 0) for w in words]
            cursor=delay
            for word,weight in zip(words,weights):
                slot=(finish-delay)*weight/max(1,sum(weights))
                word.update(start=round(cursor,6),end=round(cursor+slot*.85,6))
                cursor+=slot
            for marker_index,marker in enumerate(markers):
                marker.update(start=round(words[marker["words"][-1]]["end"]+.03,6),duration=min(motion["marker_duration"],duration*.12))
                for n in marker["words"]:
                    words[n]["marker"]=marker_index
        data={"schema":1,"renderer":ENGINE,"version":self.data.get("version","v1"),"index":index,"text":text,"start":start,"end":end,"duration":duration,
              "fps":self.settings.fps,"width":self.settings.width,"height":self.settings.height-self.settings.top_height,
              "font_size":layout["font_size"],"words":words,"markers":markers,"motion":motion}
        write_json(folder / "motion.json",data)
        target=self.root / "pages" / f"page-{index}.mkv"
        started=time.perf_counter()
        render_page(folder / "motion.json",target,self.ffmpeg)
        self.data["pages"].append({"text":text,"start":start,"end":end,"motion":(folder/"motion.json").relative_to(self.root).as_posix(),"video":target.relative_to(self.root).as_posix(),"render_seconds":round(time.perf_counter()-started,3)})
        self.data["font_sizes"].append(layout["font_size"])
        self.save()
        return target

    def save(self):
        write_json(self.root/"project.json",self.data)

    def finish(self, command, output, top, ending, music, outro):
        self.data["final_video"] = Path(output).name
        self.asset("top_panel",top,"top-panel.mp4")
        self.asset("ending_image",ending,"ending.png")
        self.asset("music",music,"music/"+Path(music).name if music else "music/unused")
        self.asset("outro",outro,"outro"+Path(outro).suffix if outro else "outro.mp3")
        args=[]
        for arg in command[1:]:
            if arg==str(output):
                args.append("{output}")
            elif arg in self.aliases:
                args.append(self.aliases[arg])
            else:
                try:
                    file=Path(arg)
                    args.append(file.relative_to(self.root).as_posix() if file.is_absolute() and file.is_relative_to(self.root) else arg)
                except (ValueError,OSError):
                    args.append(arg)
        write_json(self.root/"export.json",{"renderer":ENGINE,"arguments":args,"note":"Final codec, metadata and audio parameters are recorded without modification."})
        self.save()

    def details(self):
        return {"renderer":ENGINE,"render_project":"render-project","project_file":"render-project/project.json",
                "page_render_seconds":sum(p["render_seconds"] for p in self.data["pages"])}

def create_brain_mask(size=(72, 76)):
    """Generate minimalist antialiased brain silhouette mask with cerebral cortex convolutions."""
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((w*0.12, h*0.22, w*0.50, h*0.78), fill=255)
    draw.ellipse((w*0.20, h*0.10, w*0.50, h*0.48), fill=255)
    draw.ellipse((w*0.16, h*0.42, w*0.49, h*0.88), fill=255)
    draw.ellipse((w*0.26, h*0.68, w*0.47, h*0.94), fill=255)
    draw.ellipse((w*0.50, h*0.22, w*0.88, h*0.78), fill=255)
    draw.ellipse((w*0.50, h*0.10, w*0.80, h*0.48), fill=255)
    draw.ellipse((w*0.51, h*0.42, w*0.84, h*0.88), fill=255)
    draw.ellipse((w*0.53, h*0.68, w*0.74, h*0.94), fill=255)
    draw.ellipse((w*0.43, h*0.82, w*0.57, h*0.98), fill=255)
    draw.line([(w*0.50, h*0.08), (w*0.50, h*0.86)], fill=0, width=int(scale*3))
    draw.arc((w*0.22, h*0.26, w*0.44, h*0.44), start=120, end=330, fill=0, width=int(scale*2.5))
    draw.arc((w*0.18, h*0.46, w*0.42, h*0.66), start=100, end=300, fill=0, width=int(scale*2.5))
    draw.arc((w*0.26, h*0.62, w*0.46, h*0.80), start=80, end=270, fill=0, width=int(scale*2.5))
    draw.arc((w*0.56, h*0.26, w*0.78, h*0.44), start=210, end=60, fill=0, width=int(scale*2.5))
    draw.arc((w*0.58, h*0.46, w*0.82, h*0.66), start=240, end=80, fill=0, width=int(scale*2.5))
    draw.arc((w*0.54, h*0.62, w*0.74, h*0.80), start=270, end=100, fill=0, width=int(scale*2.5))
    return mask.resize(size, Image.Resampling.LANCZOS)

def get_brain_mask(size=(72, 76), asset_path=None):
    if asset_path and Path(asset_path).is_file():
        try:
            return Image.open(asset_path).convert("L").resize(size, Image.Resampling.LANCZOS)
        except Exception:
            pass
    asset_file = Path("assets/brand/brain_mask.png")
    if asset_file.is_file():
        try:
            return Image.open(asset_file).convert("L").resize(size, Image.Resampling.LANCZOS)
        except Exception:
            pass
    return create_brain_mask(size)

def draw_v2_progress_indicator(frame, data, t, brain_mask, brain_outline, font):
    page_idx = data.get("index", 1)
    duration = data.get("duration", 10.8)
    slide_p = min(1.0, max(0.0, t / max(1e-6, duration)))
    global_p = min(1.0, max(0.0, ((page_idx - 1) + slide_p) / 5.0))
    bw, bh = 72, 76
    cx = data.get("width", 1080) // 2
    bx = cx - bw // 2
    by = 760  # Lifted up from 882 to clear lower vertical margin and follow button (absolute Y=1520)
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    # 1. Unfilled brain silhouette
    unfilled = Image.new("RGBA", (bw, bh), (255, 255, 255, 28))
    overlay.paste(unfilled, (bx, by), brain_mask)
    # 2. Smooth vertical gold fill bottom-to-top synced frame-by-frame
    fill_h = round(bh * global_p)
    if fill_h > 0:
        box_m = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(box_m).rectangle((0, bh - fill_h, bw, bh), fill=255)
        act = ImageChops.multiply(brain_mask, box_m)
        gold = Image.new("RGBA", (bw, bh), (255, 215, 0, 240))
        overlay.paste(gold, (bx, by), act)
        meniscus_y = bh - fill_h
        glow_bar = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        ImageDraw.Draw(glow_bar).line([(6, meniscus_y), (bw - 6, meniscus_y)], fill=(255, 248, 190, 190), width=2)
        glow_bar = ImageChops.multiply(glow_bar, act.convert("RGBA"))
        overlay.alpha_composite(glow_bar, (bx, by))
    # 3. Soft outline
    outl = Image.new("RGBA", (bw, bh), (255, 230, 140, 140))
    overlay.paste(outl, (bx, by), brain_outline)
    # 4. Slide timer progress bar: underneath the brain
    bar_w, bar_h = 320, 4
    bar_x = cx - bar_w // 2
    bar_y = 848  # Lifted up from 970 (absolute Y=1608)
    draw_ov.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=2, fill=(255, 255, 255, 35))
    act_w = round(bar_w * slide_p)
    if act_w > 0:
        draw_ov.rounded_rectangle((bar_x, bar_y, bar_x + act_w, bar_y + bar_h), radius=2, fill=(255, 215, 0, 235))
    # 5. Arabic page badge: "1 / 5", "2 / 5", etc.
    badge_text = f"{page_idx} / 5"
    if font:
        bbox = draw_ov.textbbox((0, 0), badge_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    else:
        tw, th = 40, 16
    pad_x, pad_y = 12, 4
    badge_w = tw + pad_x * 2
    badge_h = th + pad_y * 2
    badge_x = cx - badge_w // 2
    badge_y = 862  # Lifted up from 984 (absolute Y=1622)
    draw_ov.rounded_rectangle((badge_x, badge_y, badge_x + badge_w, badge_y + badge_h), radius=badge_h // 2,
                             fill=(15, 23, 42, 190), outline=(255, 215, 0, 130), width=1)
    if font:
        draw_ov.text((badge_x + pad_x - bbox[0], badge_y + pad_y - bbox[1]), badge_text, font=font, fill=(248, 250, 252, 240))
    else:
        draw_ov.text((badge_x + pad_x, badge_y + pad_y), badge_text, fill=(248, 250, 252, 240))
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

def partial_mask(word, glyph, progress):
    if progress>=1:
        return glyph
    brush=Image.new("L",glyph.size)
    draw=ImageDraw.Draw(brush)
    remaining=progress*sum(s["length"] for s in word["strokes"])
    width=word["brush_width"]
    for stroke in word["strokes"]:
        if remaining<=0:
            break
        fraction=min(1,remaining/stroke["length"])
        points=stroke["points"]
        length=sum(math.dist(a,b) for a,b in zip(points,points[1:]))
        budget=length*fraction
        drawn=[tuple(points[0])]
        for a,b in zip(points,points[1:]):
            distance=math.dist(a,b)
            if budget>=distance:
                drawn.append(tuple(b));budget-=distance
            else:
                ratio=budget/max(distance,1e-9)
                drawn.append((a[0]+(b[0]-a[0])*ratio,a[1]+(b[1]-a[1])*ratio));break
        if len(drawn)>1:
            draw.line(drawn,fill=255,width=width,joint="curve")
            for x,y in (drawn[0],drawn[-1]):
                r=width/2;draw.ellipse((x-r,y-r,x+r,y+r),fill=255)
        remaining-=stroke["length"]
    return ImageChops.multiply(glyph,brush)

def page_frame(data, base, background, masks, t, brain_mask=None, brain_outline=None, badge_font=None):
    frame = base.copy()
    if data["index"] == 1 and t < .3:
        frame = Image.blend(background, frame, max(0, t / .3))
    is_v2 = (data.get("version") == "v2")
    if is_v2:
        p_fade = min(1.0, max(0.0, t / 0.35))
        y_off = round(12.0 * (1.0 - p_fade))
        fade_lut = [round(v * p_fade) for v in range(256)] if p_fade < 1.0 else None

        # Marker highlight background pill sweep (starts at 1.5s over 0.6s, RTL)
        for marker in data["markers"]:
            p = min(1.0, max(0.0, (t - marker["start"]) / marker["duration"]))
            if p <= 0:
                continue
            x0, y0, x1, y1 = marker["box"]
            alpha = Image.new("L", (max(1, x1 - x0), max(1, y1 - y0)))
            ImageDraw.Draw(alpha).rounded_rectangle((0, 0, alpha.width - 1, alpha.height - 1), radius=10, fill=35)
            clip = round(alpha.width * (1.0 - p))
            if clip:
                ImageDraw.Draw(alpha).rectangle((0, 0, clip - 1, alpha.height), fill=0)
            frame.paste((255, 215, 0), (x0, y0), alpha)

        # Word rendering with 12px upward slide + opacity fade + RTL gold sweep
        for i, word in enumerate(data["words"]):
            wx, wy = word["xy"]
            draw_y = wy + y_off
            mask = masks[i]
            color = (248, 250, 252)
            if "marker" in word:
                m = data["markers"][word["marker"]]
                if t >= m["start"]:
                    p_mark = min(1.0, max(0.0, (t - m["start"]) / m["duration"]))
                    mx0, my0, mx1, my1 = m["box"]
                    mW = mx1 - mx0
                    x_front = mx1 - mW * p_mark
                    wx0 = wx
                    wx1 = wx0 + mask.width
                    if x_front >= wx1:
                        wp = 0.0
                    elif x_front <= wx0:
                        wp = 1.0
                    else:
                        wp = (wx1 - x_front) / max(1.0, wx1 - wx0)
                    color = tuple(round(a + (b - a) * wp) for a, b in zip((248, 250, 252), (255, 215, 0)))
            if fade_lut:
                applied_mask = mask.point(fade_lut)
            else:
                applied_mask = mask
            frame.paste(color, (wx, draw_y), applied_mask)

        if brain_mask is not None:
            frame = draw_v2_progress_indicator(frame, data, t, brain_mask, brain_outline, badge_font)
        fade = min(0.08, data["duration"] * 0.05)
        if t > data["duration"] - fade:
            frame = Image.blend(background, frame, max(0, (data["duration"] - t) / fade))
        return frame
    else:
        for marker in data["markers"]:
            progress = min(1, max(0, (t - marker["start"]) / marker["duration"]))
            if progress <= 0:
                continue
            x0, y0, x1, y1 = marker["box"]
            alpha = Image.new("L", (max(1, x1 - x0), max(1, y1 - y0)))
            ImageDraw.Draw(alpha).rounded_rectangle((0, 0, alpha.width - 1, alpha.height - 1), radius=10, fill=35)
            clip = round(alpha.width * (1 - progress))
            if clip:
                ImageDraw.Draw(alpha).rectangle((0, 0, clip - 1, alpha.height), fill=0)
            frame.paste((255, 215, 0), (x0, y0), alpha)
        for i, word in enumerate(data["words"]):
            if t < word["start"]:
                continue
            progress = min(1, max(0, (t - word["start"]) / max(1e-6, word["end"] - word["start"])))
            mask = masks[i] if progress >= 1 else partial_mask(word, masks[i], progress)
            color = (248, 250, 252)
            if "marker" in word:
                m = data["markers"][word["marker"]]
                p = min(1, max(0, (t - m["start"]) / m["duration"]))
                color = tuple(round(a + (b - a) * p) for a, b in zip(color, (255, 215, 0)))
            frame.paste(color, tuple(word["xy"]), mask)
        fade = min(data["motion"]["fade"], data["duration"] * .1)
        if t > data["duration"] - fade:
            frame = Image.blend(background, frame, max(0, (data["duration"] - t) / fade))
        return frame

def render_page(recipe, output, ffmpeg):
    folder=Path(recipe).parent
    data=json.loads(Path(recipe).read_text(encoding="utf-8"))
    base=Image.open(folder/"base.png").convert("RGB")
    background=Image.open(folder/"background.png").convert("RGB")
    masks=[Image.open(folder/w["mask"]).convert("L") for w in data["words"]]
    is_v2 = (data.get("version") == "v2")
    brain_mask = None
    brain_outline = None
    badge_font = None
    if is_v2:
        brain_mask = get_brain_mask((72, 76))
        brain_outline = brain_mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.8))
        font_file = folder.parent.parent / "assets" / "font.ttf"
        if not font_file.is_file():
            font_file = Path("assets/NotoSansArabic-SemiBold.ttf")
        if font_file.is_file():
            try:
                badge_font = ImageFont.truetype(str(font_file), 18)
            except Exception:
                badge_font = None
    log=Path(output).with_suffix(".log")
    command=[ffmpeg,"-hide_banner","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f'{data["width"]}x{data["height"]}',"-r",str(data["fps"]),"-i","pipe:0",
             "-an","-c:v","ffv1","-level","3","-g","1","-pix_fmt","bgr0","-y",str(output)]
    with log.open("wb") as stderr:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=stderr,stdout=subprocess.DEVNULL)
        try:
            for frame in range(round(data["duration"]*data["fps"])):
                process.stdin.write(page_frame(data,base,background,masks,frame/data["fps"],brain_mask,brain_outline,badge_font).tobytes())
            process.stdin.close()
            if process.wait()!=0:
                raise RuntimeError(f"Whiteboard encode failed: {log.read_text(errors='replace')[-2000:]}")
        except BaseException:
            if process.poll() is None:
                process.terminate();process.wait()
            raise

def replay_project(root):
    import argparse
    from .media_tools import resolve_media_tools
    parser=argparse.ArgumentParser(description="Rebuild this saved Python whiteboard episode without source analysis.")
    parser.add_argument("--output",type=Path,default=root.parent/"CapCut_1080p_whiteboard_rerender.mp4")
    parser.add_argument("--overwrite",action="store_true")
    args=parser.parse_args()
    if args.output.exists() and not args.overwrite:
        parser.error("Output exists; choose another path or pass --overwrite.")
    data=json.loads((root/"project.json").read_text(encoding="utf-8"))
    assets=data["assets"]
    os.environ.update(AVBRIEF_RENDER_PROJECT=str(root),ARABIC_VIDEO_BRIEF_FONT=str(root/assets["font"]),
        ARABIC_VIDEO_BRIEF_MUSIC_DIR=str(root/"assets/music"),ARABIC_VIDEO_BRIEF_FRAME=str(root/assets.get("frame","missing-frame")),
        ARABIC_VIDEO_BRIEF_AVATAR=str(root/assets.get("avatar","missing-avatar")),
        ARABIC_VIDEO_BRIEF_OUTRO_VOICEOVER=str(root/assets.get("outro","missing-outro")),FFMPEG_BINARY=resolve_media_tools()["FFMPEG_BIN"])
    settings=Settings(**data["settings"])
    if data["version"]=="v1":
        from .media import render_video
        render_video(root/assets["source"],root/assets["thumbnail"] if assets.get("thumbnail") else None,*data["texts"],data["selected_clip"],args.output,settings,
                     metadata=data["metadata"],post_title=data["title"],ending_question=data["ending"])
    else:
        from .v2.renderer import render_v2_video
        from .v2.editorial import V2EditorialPackage,HookCandidate
        editorial=V2EditorialPackage(post_title_ar=data["title"],summary_ar=" ".join(data["texts"]),pages=data["texts"],
            hook=HookCandidate("","","","",{},0,""),conclusion_ar=data["ending"],conclusion_highlights=data["editorial"].get("conclusion_highlights",[]),
            cta_ar=data["editorial"].get("cta_ar",""),cta_description=data["editorial"].get("cta_description",""),creative_plan={})
        render_v2_video(root/assets["source"],root/assets["thumbnail"] if assets.get("thumbnail") else None,editorial,data["selected_clip"],args.output,settings,
            hook_audio_path=root/assets["hook"] if assets.get("hook") else None,metadata=data["metadata"])
    print(args.output)

def finalize_package(output):
    """Keep the portable project linked to the staged episode filename."""
    output = Path(output)
    recipe = output.parent / "render-project" / "project.json"
    data = json.loads(recipe.read_text(encoding="utf-8"))
    data["final_video"] = output.name
    write_json(recipe, data)
