"""Render and compose a short synthetic whiteboard example without API keys."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arabic_video_brief.render_runtime import load_render_runtime


def main():
    runtime = load_render_runtime()
    folder = Path(tempfile.mkdtemp(prefix="smoke-", dir=ROOT / ".runtime")).resolve()
    source = folder / "episode"
    source.mkdir()
    video = source / "reference.mp4"
    subprocess.run([runtime["FFMPEG_BIN"], "-v", "error", "-f", "lavfi", "-i", "color=black:s=1080x1920:r=30:d=2.5",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "2.5", "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", str(video)], check=True)
    text = "عندما تظهر الكلمات بهدوء يستطيع القارئ متابعة الفكرة. هذا مثال تجريبي لكتابة عربية مع <hl>عبارة ذهبية واضحة</hl>، ثم تبقى الكلمات ظاهرة حتى تكتمل الصفحة وتظهر <hl>الفكرة التالية</hl> بصورة مقروءة."
    (source / "summary-pages.json").write_text(json.dumps([{"text":text,"page":i+1} for i in range(4)],ensure_ascii=False),encoding="utf-8")
    (source / "post-title.txt").write_text("تجربة الكتابة العربية",encoding="utf-8")
    (source / "manifest.json").write_text(json.dumps({"render":{"version":"v2","duration":2.5},"metadata":{}}),encoding="utf-8")
    output = folder / "comparison"
    subprocess.run([sys.executable, str(ROOT / "tools/animated_reading/prepare.py"), "--source", str(source), "--out", str(output)],check=True)
    project = output / "Project"
    data_file = project / "page-data.json"
    data = json.loads(data_file.read_text(encoding="utf-8"))
    old_duration = data["duration"]
    p = data["pages"][0]
    start, end = p["writing_start"], p["writing_end"]
    retime = lambda t: round(.12+(t-start)/(end-start)*1.48,6)
    for word in p["words"]:
        word["start"],word["end"] = retime(word["start"]),retime(word["end"])
    for marker in p["markers"]:
        marker["at"],marker["duration"] = min(1.65,retime(marker["at"])),.12
    p.update(start=0,end=2,writing_start=.12,writing_end=1.6)
    data.update(duration=2,total_duration=2.5,ending_duration=.5,pages=[p])
    data_file.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    html = (project / "index.html").read_text(encoding="utf-8")
    html = html.replace(f'data-duration="{old_duration}"','data-duration="2"')
    html = re.sub(r"window\.pageData=.*?;\n",lambda _:"window.pageData="+json.dumps(data,ensure_ascii=False)+";\n",html,count=1)
    (project / "index.html").write_text(html,encoding="utf-8")
    with (folder / "render.log").open("w",encoding="utf-8") as log:
        subprocess.run([runtime["NODE_BIN"],str(ROOT / "tools/animated_reading/render.mjs"),"--project",str(project),"--quality","draft"],check=True,stdout=log,stderr=subprocess.STDOUT)
    subprocess.run([sys.executable,str(ROOT / "tools/animated_reading/compose.py"),"--folder",str(output)],check=True)
    final = output / "Preview.mp4"
    probe = json.loads(subprocess.check_output([runtime["FFPROBE_BIN"],"-v","error","-show_streams","-show_format","-of","json",str(final)]))
    stream = next(s for s in probe["streams"] if s["codec_type"]=="video")
    assert (stream["width"],stream["height"],stream["r_frame_rate"],int(stream["nb_frames"]))==(1080,1920,"30/1",75)
    assert abs(float(probe["format"]["duration"])-2.5)<.01
    assert any(s["codec_type"]=="audio" for s in probe["streams"])
    counts=[]
    for at in [.2,1.8]:
        raw=subprocess.check_output([runtime["FFMPEG_BIN"],"-v","error","-ss",str(at),"-i",str(final),"-frames:v","1","-vf","crop=1080:600:0:1000","-f","rawvideo","-pix_fmt","rgb24","-"])
        array=np.frombuffer(raw,np.uint8).reshape(600,1080,3)
        counts.append(int((array.min(axis=2)>160).sum()))
    assert counts[1]>counts[0]+150, f"Writing did not become visible: {counts}"
    receipt={"passed":True,"video":str(final),"frames":75,"duration":2.5,"progressive_white_pixels":counts}
    (folder / "result.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    print(json.dumps(receipt))


if __name__=="__main__":
    main()
