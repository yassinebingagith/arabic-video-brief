"""Prepare an editable, page-only Hyperframes comparison from an existing V2 export."""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import sys
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from PIL import Image, ImageDraw, ImageFont
from arabic_video_brief.config import Settings
from arabic_video_brief.render_runtime import load_render_runtime
from arabic_video_brief.media import (
    _balance_wrap, _display_text, create_v2_summary_background,
    infer_category, wrap_v2_text_with_highlights,
)
from strokes import writing_strokes


def font(size, weight=700):
    f = ImageFont.truetype(str(Settings().font_path), size)
    f.set_variation_by_axes([weight, 100])
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reference-video", type=Path, help="Reuse a previously copied local reference.")
    args = ap.parse_args()
    runtime = load_render_runtime()
    source = args.source.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Use an empty output folder; existing comparisons are preserved.")
    project = out / "Project"
    project.mkdir(parents=True)
    (out / "Source").mkdir()
    videos = list(source.glob("*.mp4"))
    if len(videos) != 1:
        raise ValueError("The reference folder must contain exactly one MP4.")
    shutil.copy2(args.reference_video or videos[0], out / "Source" / "reference.mp4")
    if args.reference_video and args.reference_video.with_suffix(".json").is_file():
        shutil.copy2(args.reference_video.with_suffix(".json"), out / "reference-adjustments.json")
    pages = json.loads((source / "summary-pages.json").read_text(encoding="utf-8-sig"))
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8-sig"))
    if len(pages) != 4 or manifest.get("render", {}).get("version") != "v2":
        raise ValueError("This comparison builder currently accepts V2 only.")
    title = (source / "post-title.txt").read_text(encoding="utf-8-sig").strip()
    category = infer_category(manifest.get("metadata", {}), " ".join(p["text"] for p in pages))
    bounds = Settings().v2_page_boundaries
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    page_data = []
    markup = []

    def svg_text(text, x, y, size, weight=700, fill="#F8FAFC", anchor="start", cls="", ident="", mask=""):
        width = draw.textlength(_display_text(text), font=font(size, weight))
        mask_attribute = f'mask="url(#{mask})"' if mask else ""
        return (f'<text id="{ident}" class="{cls}" x="{x:.4f}" y="{y:.4f}" '
                f'direction="rtl" text-anchor="{anchor}" xml:space="preserve" '
                f'textLength="{width:.4f}" lengthAdjust="spacingAndGlyphs" '
                f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
                f'{mask_attribute}>'
                f'{html.escape(text)}</text>')

    for i, page in enumerate(pages):
        number = i + 1
        start, end = bounds[i:i+2]
        y = 780
        header = []
        if number == 1:
            title_font = font(38)
            for line in _balance_wrap(title, title_font, 816):
                header.append(svg_text(line, 540, y + title_font.getmetrics()[0], 38, fill="#F5C518", anchor="middle"))
                y += math.ceil(38 * 1.35)
            y += 10
            subtitle = "فيديوهات وجب مشاهدتها على اليوتيوب"
            subfont = font(28)
            header.append(svg_text(subtitle, 540, y + subfont.getmetrics()[0], 28, anchor="middle"))
            box = draw.textbbox((0, 0), _display_text(subtitle), font=subfont)
            y += box[3] - box[1] + 10
            if category:
                catfont = font(22, 500)
                cat = f"النوع: {category}"
                header.append(svg_text(cat, 540, y + catfont.getmetrics()[0], 22, 500, "#A0A0A0", "middle"))
                box = draw.textbbox((0, 0), _display_text(cat), font=catfont)
                y += box[3] - box[1] + 26
        size = 42 if number == 1 else 46
        lines = wrap_v2_text_with_highlights(page["text"], font(size), 816)
        while len(lines) > 6 and size > 34:
            size -= 2
            lines = wrap_v2_text_with_highlights(page["text"], font(size), 816)
        line_h = math.ceil(size * 1.85)
        total_h = len(lines) * line_h
        safe_bottom = 1632
        if number > 1:
            y = 760 + (safe_bottom - 760 - total_h) // 2
        elif safe_bottom - y > total_h:
            y += max(16, (safe_bottom - y - total_h) // 3)
        body = []
        marks = []
        words = []
        word_total = len(re.sub(r"</?hl>", "", page["text"]).split())
        line_records = []
        for j, line in enumerate(lines):
            line_id = f"p{number}-line{j}"
            right = 916.0
            glyphs = []
            pills = []
            for segment in re.split(r"(<hl>.*?</hl>)", line):
                if not segment:
                    continue
                highlighted = segment.startswith("<hl>")
                text = segment[4:-5] if highlighted else segment
                f = font(size, 750 if highlighted else 700)
                visual = get_display(arabic_reshaper.reshape(text), base_dir="R")
                width = draw.textlength(visual, font=f)
                x = right - width
                ident = f"p{number}-mark{len(marks)}" if highlighted else ""
                segment_words = []
                if highlighted:
                    bx = draw.textbbox((x, 0), visual, font=f)
                    pills.append(f'<rect id="{ident}" class="marker" x="{bx[0]-10:.4f}" y="{bx[1]-2}" width="{bx[2]-bx[0]+20:.4f}" height="{bx[3]-bx[1]+6}" rx="10" fill="#FFD700" fill-opacity="0.14"/>')
                pieces = re.findall(r"\S+|\s+", text)
                piece_widths = [draw.textlength(piece if piece.isspace() else _display_text(piece), font=f) for piece in pieces]
                factor = width / max(sum(piece_widths), 1)
                cursor_right = right
                for piece, piece_width in zip(pieces, piece_widths):
                    piece_left = cursor_right - piece_width * factor
                    if piece.strip():
                        word_id = f"p{number}-word{len(words)}"
                        guides = writing_strokes(piece, f, _display_text(piece), piece_width, line_h)
                        paths = []
                        stroke_records = []
                        for k, guide in enumerate(guides):
                            stroke_id = f"{word_id}-stroke{k}"
                            paths.append(f'<path id="{stroke_id}" class="write-stroke" d="{guide["d"]}" pathLength="1" fill="none" stroke="white" stroke-width="{max(6,size*.29):.3f}" stroke-linecap="round" stroke-linejoin="round"/>')
                            stroke_records.append({"id": stroke_id, "length": guide["length"]})
                        mask_id = word_id + "-mask"
                        mask = (f'<defs><mask id="{mask_id}" maskUnits="userSpaceOnUse" maskContentUnits="userSpaceOnUse" x="-14" y="-10" width="{piece_width+28:.4f}" height="{line_h+40}">'
                                f'{"".join(paths)}<rect id="{word_id}-complete" class="write-complete" x="-14" y="-10" width="{piece_width+28:.4f}" height="{line_h+40}" fill="white"/></mask></defs>')
                        segment_words.append(f'<g id="{word_id}" class="word" transform="translate({piece_left:.4f},0) scale({factor:.6f},1)">{mask}'
                                             + svg_text(piece, piece_width, f.getmetrics()[0], size, 750 if highlighted else 700, mask=mask_id) + '</g>')
                        words.append({"id": word_id, "text": piece, "line": line_id, "strokes": stroke_records})
                    cursor_right = piece_left
                if highlighted:
                    marks.append({"id": ident, "duration": .38,
                                  "phrase": text.replace("\u00a0", " "), "line": line_id, "last_word": words[-1]["id"]})
                    glyphs.append(f'<g id="{ident}-text">{"".join(segment_words)}</g>')
                else:
                    glyphs.extend(segment_words)
                right = x
            body.append(f'<div id="{line_id}" class="line" style="top:{y+j*line_h}px;height:{line_h}px"><svg viewBox="0 0 1080 {line_h}" width="1080" height="{line_h}">{"".join(pills)}{"".join(glyphs)}</svg></div>')
            line_records.append({"id": line_id, "text": re.sub(r"</?hl>", "", line).replace("\u00a0", " "),
                                 "top": y+j*line_h, "font_size": size, "left": right, "right": 916})
        original_words = re.sub(r"</?hl>", "", page["text"]).split()
        laid_out_words = re.sub(r"</?hl>", "", " ".join(lines)).split()
        if laid_out_words != original_words:
            raise ValueError("Layout lost or duplicated words.")
        if "".join(w["text"] for w in words) != "".join(original_words):
            raise ValueError("Writing schedule lost or duplicated words.")
        if any(record["left"] < 65 for record in line_records):
            raise ValueError("A line exceeds the platform-safe layout.")
        writing_start = start + (.45 if number == 1 else .12)
        writing_end = end - .8
        weights = [max(1, len(re.sub(r"[^\w]", "", w["text"]))) ** .5 + (.8 if re.search(r"[.،؛؟!]$", w["text"]) else 0) for w in words]
        cursor = writing_start
        for word, weight in zip(words, weights):
            slot = (writing_end-writing_start)*weight/sum(weights)
            word["start"] = round(cursor, 5)
            word["end"] = round(cursor + slot*.85, 5)
            cursor += slot
        for marker in marks:
            last_word = next(w for w in words if w["id"] == marker["last_word"])
            marker["at"] = round(last_word["end"] + .03, 5)
            if marker["at"] + marker["duration"] > end - .2:
                raise ValueError("Marker overlaps outgoing page fade.")
        markup.append(f'<section id="page{number}" class="page"><svg class="header" width="1080" height="1920">{"".join(header)}</svg>{"".join(body)}</section>')
        page_data.append({"id": f"page{number}", "start": start, "end": end,
                          "lines": line_records, "markers": marks, "words": words, "word_count": word_total,
                          "writing_start": writing_start, "writing_end": words[-1]["end"]})
    create_v2_summary_background().save(project / "background.png")
    shutil.copy2(Settings().font_path, project / "Arabic.ttf")
    shutil.copy2(Settings().brand_frame_path, project / "frame.png")
    shutil.copy2(runtime["GSAP_JS"], project / "gsap.min.js")
    for name in ("motion.js",):
        shutil.copy2(Path(__file__).parent / name, project / name)
    data = {"version": "v2", "duration": bounds[-1], "total_duration": Settings().duration_v2, "ending_duration": Settings().conclusion_duration, "fps": 30,
            "canvas": [1080, 1920], "page_crop": [0, 780, 1080, 1140],
            "inner_scale": .9, "inner_origin": [54, 96], "pages": page_data,
            "reference_folder": str(source), "reference_video": videos[0].name,
            "motion_style": "font-guided-whiteboard-writing", "outgoing_fade_seconds": .18}
    template = (Path(__file__).parent / "template.html").read_text(encoding="utf-8")
    template = template.replace("__PAGES__", "".join(markup)).replace("__DATA__", json.dumps(data, ensure_ascii=False))
    template = template.replace("__DURATION__", str(bounds[-1]))
    template = template.replace("__MOTION__", (Path(__file__).parent / "motion.js").read_text(encoding="utf-8"))
    (project / "index.html").write_text(template, encoding="utf-8")
    (project / "page-data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(source / "summary-pages.json", project / "summary-pages.json")
    (out / "README.md").write_text(
        "# V2 animated reading comparison\n\n"
        "Project/index.html, motion.js and page-data.json contain the editable page composition. "
        f"The 1080×1140 rendered component replaces only y=780–1920 during 0–{bounds[-1]} seconds. "
        "The source top panel and original AAC audio are reused; the ending uses the source picture. "
        "Source/reference.mp4 is an unchanged local reference copy.\n\n"
        "This is a visual comparison using existing supplied copy. No new factual review or publication is implied.\n",
        encoding="utf-8")
    print(json.dumps({"project": str(project), "duration": bounds[-1], "pages": len(page_data),
                      "lines": [len(p["lines"]) for p in page_data], "category": category}))


if __name__ == "__main__":
    main()
