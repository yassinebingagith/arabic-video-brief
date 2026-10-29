"""Exercise normal V1/V2 production rendering with synthetic media, without APIs."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from arabic_video_brief.config import Settings
from arabic_video_brief.media import render_video
from arabic_video_brief.media_tools import resolve_media_tools
from arabic_video_brief.v2.editorial import V2EditorialPackage,HookCandidate
from arabic_video_brief.v2.renderer import render_v2_video


def main():
    tools=resolve_media_tools()
    (ROOT/".runtime").mkdir(exist_ok=True)
    root=Path(tempfile.mkdtemp(prefix="python-whiteboard-",dir=ROOT/".runtime"))
    source=root/"source.mp4"
    subprocess.run([tools["FFMPEG_BIN"],"-v","error","-f","lavfi","-i","testsrc2=s=640x360:r=10:d=5","-c:v","libx264","-pix_fmt","yuv420p",str(source)],check=True)
    settings=replace(Settings(),fps=10,page_duration=1.8,cta_duration=1,duration=4.6,
                     first_page_duration_v2=1.8,page_duration_v2=1.2,conclusion_duration=1,duration_v2=6.4)
    text="تظهر الكلمات بهدوء، ثم تتضح <hl>الفكرة الأساسية</hl> أمام القارئ، وتبقى <hl>العبارة المهمة</hl> ظاهرة."
    question="أي فكرة تستحق أن تمنحها المزيد من وقتك؟"
    results=[]
    for version in ("v1","v2"):
        output=root/version/"CapCut_1080p_smoke.mp4"
        if version=="v1":
            details=render_video(source,None,text,text,{"start_seconds":0},output,settings,
                metadata={"title":"Synthetic fixture","id":"smoke"},post_title="تجربة الكتابة العربية",ending_question=question)
        else:
            editorial=V2EditorialPackage("تجربة الكتابة العربية",text,[text]*4,HookCandidate("","","","",{},0,""),question,[],"احفظها لتقرأها لاحقاً","التفاصيل في الوصف",{})
            details=render_v2_video(source,None,editorial,{"start_seconds":0},output,settings,metadata={"title":"Synthetic fixture","id":"smoke"})
        assert details["renderer"]=="python-whiteboard"
        project=output.parent/details["render_project"]
        data=json.loads((project/"project.json").read_text(encoding="utf-8"))
        assert len(data["pages"])==(2 if version=="v1" else 4)
        assert all((project/file).is_file() for file in data["assets"].values())
        assert (project/"render.py").is_file()
        recipe=project/"pages/page-1/motion.json"
        page=json.loads(recipe.read_text(encoding="utf-8"))
        counts=[]
        for t in [.1,page["words"][-1]["end"]+.05]:
            raw=subprocess.check_output([tools["FFMPEG_BIN"],"-v","error","-ss",str(t),"-i",str(project/"pages/page-1.mkv"),"-frames:v","1","-f","rawvideo","-pix_fmt","rgb24","-"])
            array=np.frombuffer(raw,np.uint8).reshape(page["height"],page["width"],3)
            counts.append(int((array.min(axis=2)>160).sum()))
        assert counts[1]>counts[0]+150
        probe=json.loads(subprocess.check_output([tools["FFPROBE_BIN"],"-v","error","-show_streams","-show_format","-of","json",str(output)]))
        assert probe["format"]["tags"]["major_brand"]=="mp42"
        assert probe["format"]["tags"].get("comment")=="CapCut"
        assert next(s for s in probe["streams"] if s["codec_type"]=="video")["tags"].get("encoder")=="CapCut"
        assert abs(float(probe["format"]["duration"])-(4.6 if version=="v1" else 6.4))<.05
        results.append({"version":version,"output":str(output),"renderer":details["renderer"],"page_render_seconds":details["page_render_seconds"],"progressive_white_pixels":counts})
    (root/"result.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    print(json.dumps({"passed":True,"results":results}))


if __name__=="__main__":
    main()
