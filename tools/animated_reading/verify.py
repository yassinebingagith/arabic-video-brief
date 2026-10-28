"""Verify the actual comparison encode and create chronological visual-review sheets."""
import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--folder", type=Path, required=True)
args = ap.parse_args()
folder = args.folder.resolve()
runtime = json.loads(Path("F:/hyperframes-v3/config/local-runtime.json").read_text())
ffmpeg, ffprobe = runtime["FFMPEG_BIN"], runtime["FFPROBE_BIN"]
preview, source = folder / "Preview.mp4", folder / "Source/reference.mp4"
data = json.loads((folder / "Project/page-data.json").read_text(encoding="utf-8"))
total_duration = data.get("total_duration", data["duration"] + 8)
reading_end = data["duration"]
qa = folder / "Review"
qa.mkdir(exist_ok=True)


def capture(file, at):
    payload = subprocess.check_output([ffmpeg, "-v", "error", "-ss", str(at), "-i", str(file),
                                      "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"])
    return Image.open(io.BytesIO(payload)).convert("RGB")


def audio_hash(file):
    return subprocess.check_output([ffmpeg, "-v", "error", "-i", str(file), "-map", "0:a:0",
                                    "-c:a", "copy", "-f", "hash", "-hash", "sha256", "-"], text=True).strip()


probe = json.loads(subprocess.check_output([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(preview)]))
v = next(s for s in probe["streams"] if s["codec_type"] == "video")
a = next(s for s in probe["streams"] if s["codec_type"] == "audio")
errors = []
if (v["width"], v["height"], v["r_frame_rate"], int(v["nb_frames"])) != (1080, 1920, "30/1", round(total_duration*data["fps"])):
    errors.append("Unexpected video geometry/frame rate/frame count")
if abs(float(probe["format"]["duration"]) - total_duration) > .001:
    errors.append("Duration changed")
original_audio, preview_audio = audio_hash(source), audio_hash(preview)
if original_audio != preview_audio:
    errors.append("Original AAC packets changed")
comparisons = []
for t in [p["start"]+1.3 for p in data["pages"]] + [reading_end, reading_end+1.8, total_duration-.3]:
    original = np.asarray(capture(source, t)).astype(float)
    current = np.asarray(capture(preview, t)).astype(float)
    region = (slice(None), slice(None)) if t >= reading_end else (slice(0, 770), slice(None))
    delta = original[region] - current[region]
    mae = float(np.abs(delta).mean())
    psnr = float(10 * np.log10(255 ** 2 / max(float(np.square(delta).mean()), 1e-12)))
    comparisons.append({"time": t, "region": "entire ending" if t >= reading_end else "original top panel", "mean_absolute_rgb_error": round(mae, 4), "psnr_db": round(psnr, 2)})
    if mae > 3:
        errors.append(f"Preserved picture changed beyond normal encoding tolerance at {t}")

pixel_checks = []
for p in data["pages"]:
    settled_time = p.get("writing_end", p["start"]+1.3) + .04
    image = np.asarray(capture(preview, settled_time))
    counts = []
    for line in p["lines"]:
        y = round(96 + .9 * line["top"])
        region = image[y:y+66, 100:920]
        bright = (region.min(axis=2) > 160).sum()
        counts.append(int(bright))
        if bright < 150:
            errors.append(f"Encoded text missing at {line['id']}")
    pixel_checks.append({"page": p["id"], "time": settled_time, "bright_text_pixels_per_line": counts})


def sheet(name, times, crop=None, width=360):
    images = []
    for time in times:
        frame = capture(preview, time)
        if crop:
            frame = frame.crop(crop)
        frame.thumbnail((width, 1000))
        tile = Image.new("RGB", (width, frame.height+34), "#10151c")
        tile.paste(frame, (0, 34))
        ImageDraw.Draw(tile).text((10, 10), f"t = {time:.3f} s", fill="white")
        images.append(tile)
    canvas = Image.new("RGB", (sum(im.width for im in images), max(im.height for im in images)), "#10151c")
    x = 0
    for im in images:
        canvas.paste(im, (x, 0))
        x += im.width
    canvas.save(qa / name)

p1, p2 = data["pages"][:2]
sheet("01-writing-progression.png", [p1["writing_start"]+.25, p1["end"]*.25, p1["end"]*.5, p1["writing_end"]+.05], (0, 780, 1080, 1500), 540)
first_mark = data["pages"][0]["markers"][0]
sheet("02-gold-marker.png", [first_mark["at"]-.05, first_mark["at"]+.15, first_mark["at"]+.3, first_mark["at"]+.55], (480, 1285, 920, 1450), 440)
sheet("03-page-transition.png", [p1["end"]-.25,p1["end"]-.1,p1["end"],p1["end"]+.4,p1["end"]+1.3], (0, 780, 1080, 1500), 432)
sheet("04-pages-and-ending.png", [p["end"]-.35 for p in data["pages"]]+[reading_end+1.8], None, 360)
if data.get("motion_style") == "font-guided-whiteboard-writing":
    span=p2["end"]-p2["start"]
    sheet("05-written-second-page.png", [p2["start"]+.4,p2["start"]+span*.25,p2["start"]+span*.5,p2["writing_end"]+.05], (0, 780, 1080, 1500), 540)
    dom = json.loads((folder / "Project/inspection.json").read_text(encoding="utf-8"))
    box = next(o for o in dom["observations"] if "lines" in o)["lines"][0]["texts"][0]
    crop = (int(box["left"])-3, int(box["top"])+780-3, int(box["right"])+3, int(box["bottom"])+780+3)
    word = data["pages"][0]["words"][0]
    moments = [word["start"]-.05, (word["start"]+word["end"])/2, word["end"]+.06]
    ink = []
    for time in moments:
        array = np.asarray(capture(preview, time).crop(crop))
        ink.append(int((array.min(axis=2)>160).sum()))
    if not (ink[0]<ink[1]<ink[2]):
        errors.append(f"Encoded writing strokes do not accumulate ink: {ink}")
    pixel_checks.append({"word":word["text"], "times":moments, "progressive_ink_pixels":ink})
    sheet("06-letter-strokes.png", [word["start"]-.05, word["start"]+.025, (word["start"]+word["end"])/2, word["end"]+.06], crop, 220)
capture(preview, p1["writing_end"]+.05).save(qa / "poster.png")
report = {"errors": errors, "video": {"width": v["width"], "height": v["height"], "fps": v["r_frame_rate"], "frames": v["nb_frames"], "duration": probe["format"]["duration"]},
          "audio": {"codec": a["codec_name"], "sample_rate": a["sample_rate"], "channels": a["channels"], "original_packets_unchanged": original_audio == preview_audio, "sha256": preview_audio},
          "preserved_picture_comparisons": comparisons, "encoded_text_checks": pixel_checks,
          "preview_sha256": hashlib.sha256(preview.read_bytes()).hexdigest(),
          "visual_review": "Review chronological PNG sheets; machine checks do not constitute a visual verdict."}
(folder / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"errors": errors, "duration": probe["format"]["duration"], "audio_packets_unchanged": original_audio==preview_audio, "review": str(qa)}))
if errors:
    raise SystemExit(1)
