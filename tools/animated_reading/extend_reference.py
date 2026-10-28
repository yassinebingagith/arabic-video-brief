"""Prepare a longer comparison reference from an existing V2 export.

Only the example's middle source-video playback is slowed to fill the longer
reading window. Opening and ending play at their original speeds. New episodes
use a longer source excerpt at normal speed through the production renderer.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from arabic_video_brief.config import Settings
from arabic_video_brief.render_runtime import load_render_runtime

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--episode", type=Path, required=True)
ap.add_argument("--reference-video", type=Path, required=True)
ap.add_argument("--output", type=Path, required=True)
args = ap.parse_args()
output = args.output.resolve()
if output.exists():
    raise ValueError("Preserve existing references; choose a new output path.")
output.parent.mkdir(parents=True, exist_ok=True)
runtime = load_render_runtime()
manifest = json.loads((args.episode / "manifest.json").read_text(encoding="utf-8-sig"))
settings = Settings()
old_total = float(manifest["render"]["duration"])
old_end = old_total-settings.conclusion_duration
new_end = settings.v2_page_boundaries[-1]
new_total = new_end+settings.conclusion_duration
opening = settings.hook_duration
ratio = (new_end-opening)/(old_end-opening)
music = settings.music_dir / manifest["render"]["music_track"]
hook = output.parent / "hook-source.mp3"
shutil.copy2(args.episode / "hook-voice.mp3", hook)
hook_info = json.loads(subprocess.check_output([runtime["FFPROBE_BIN"], "-v", "error", "-show_entries", "format=duration", "-of", "json", str(hook)]))
voice_duration = max(2, min(10.5, float(hook_info["format"]["duration"])))
seed = sum(ord(c) for c in str(manifest["metadata"].get("id") or manifest["metadata"].get("title") or "v2"))
tempo = .995+(seed % 11)*.001
filters = [
    "[0:v]split=3[opening][middle][ending]",
    f"[opening]trim=start=0:end={opening},setpts=PTS-STARTPTS,fps=30[o]",
    f"[middle]trim=start={opening}:end={old_end},setpts={ratio:.12f}*(PTS-STARTPTS),fps=30,trim=duration={new_end-opening}[m]",
    f"[ending]trim=start={old_end}:end={old_total},setpts=PTS-STARTPTS,fps=30[e]",
    "[o][m][e]concat=n=3:v=1:a=0[v]",
    f"[1:a]atempo={tempo:.4f},atrim=duration={new_end},volume='if(lt(t,{voice_duration:.5f}),0.12,min(0.70,0.12+(0.70-0.12)*(t-{voice_duration:.5f})/0.6))':eval=frame,afade=t=out:st={new_end-2}:d=2,apad=whole_dur={new_total}[music]",
    f"[2:a]volume=1.3,apad=whole_dur={new_total}[hook]",
    f"[0:a]atrim=start={old_end}:end={old_total},asetpts=PTS-STARTPTS,adelay={round(new_end*1000)}:all=1,apad=whole_dur={new_total}[outro]",
    "[music][hook][outro]amix=inputs=3:duration=first:dropout_transition=0:normalize=0,aformat=channel_layouts=stereo:sample_rates=44100[a]",
]
subprocess.run([runtime["FFMPEG_BIN"], "-hide_banner", "-loglevel", "warning",
                "-i", str(args.reference_video), "-stream_loop", "-1", "-i", str(music), "-i", str(hook),
                "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "1", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-r", "30", "-frames:v", str(round(new_total*30)),
                "-t", str(new_total), "-movflags", "+faststart", str(output)], check=True)
receipt = {"original_duration":old_total, "reading_end":new_end, "total_duration":new_total,
           "middle_video_time_scale":ratio, "music_track":music.name,
           "audio":"Existing hook reused; same selected music remixed to longer reading window; original eight-second outro shifted intact.",
           "top_video":"Example middle playback slowed; normal production extracts a longer source segment at original speed."}
output.with_suffix(".json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps({"reference":str(output), "duration":new_total}))
