import subprocess
import sys
from pathlib import Path

def generate_tracks(output_dir: Path, ffmpeg_bin: str = "ffmpeg"):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. dark_psychology_drone: Low A1 (55Hz), E2 (82.4Hz), C3 (130.8Hz) minor chord + filtered sub noise + pulse
    track1 = output_dir / "dark_psychology_drone.mp3"
    cmd1 = [
        ffmpeg_bin, "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i",
        "aevalsrc=exprs='0.28*sin(2*PI*55*t) + 0.18*sin(2*PI*110*t) + 0.12*sin(2*PI*130.81*t*(1+0.005*sin(2*PI*0.2*t))) + 0.08*sin(2*PI*164.81*t)':s=44100:d=30",
        "-f", "lavfi", "-i",
        "anoisesrc=d=30:c=pink:r=44100:a=0.04",
        "-filter_complex",
        "[1:a]lowpass=f=250,volume=1.5[noise];"
        "[0:a][noise]amix=inputs=2:weights=1.0 0.4[mix];"
        "[mix]aecho=0.8:0.88:60|120:0.4|0.3,tremolo=f=0.5:d=0.25,volume=1.2,dynaudnorm=p=0.9[out]",
        "-map", "[out]", "-t", "30", "-c:a", "libmp3lame", "-b:a", "192k", "-y", str(track1)
    ]
    
    # 2. deep_contemplation_pad: D minor / D suspended chord with evolving chorus and stereo richness
    track2 = output_dir / "deep_contemplation_pad.mp3"
    cmd2 = [
        ffmpeg_bin, "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i",
        "aevalsrc=exprs='0.22*sin(2*PI*73.42*t) + 0.15*sin(2*PI*146.83*t) + 0.12*sin(2*PI*220*t*(1+0.004*sin(2*PI*0.15*t))) + 0.09*sin(2*PI*261.63*t)':s=44100:d=30",
        "-filter_complex",
        "[0:a]chorus=0.7:0.9:55:0.4:0.25:2,aecho=0.8:0.9:200|400:0.3|0.2,lowpass=f=600,volume=1.5,dynaudnorm=p=0.9[out]",
        "-map", "[out]", "-t", "30", "-c:a", "libmp3lame", "-b:a", "192k", "-y", str(track2)
    ]

    # 3. suspense_tension: Tension-building bass pulse with high harmonic overtone and dark sub
    track3 = output_dir / "suspense_tension.mp3"
    cmd3 = [
        ffmpeg_bin, "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i",
        "aevalsrc=exprs='0.3*sin(2*PI*65.4*t*(1+0.03*sin(2*PI*2*t))) + 0.15*sin(2*PI*130.8*t) + 0.08*sin(2*PI*196*t) + 0.05*sin(2*PI*392*t*(1+0.01*sin(2*PI*0.3*t)))':s=44100:d=30",
        "-f", "lavfi", "-i",
        "anoisesrc=d=30:c=brown:r=44100:a=0.03",
        "-filter_complex",
        "[1:a]lowpass=f=180[bnoise];"
        "[0:a][bnoise]amix=inputs=2:weights=1.0 0.5[mix];"
        "[mix]flanger=delay=5:depth=2:speed=0.2,aecho=0.8:0.85:150|300:0.3|0.2,volume=1.3,dynaudnorm=p=0.9[out]",
        "-map", "[out]", "-t", "30", "-c:a", "libmp3lame", "-b:a", "192k", "-y", str(track3)
    ]

    # 4. subconscious_mind: Hypnotic low-frequency drone with binaural phase modulation
    track4 = output_dir / "subconscious_mind.mp3"
    cmd4 = [
        ffmpeg_bin, "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i",
        "aevalsrc=exprs='0.25*sin(2*PI*60*t) + 0.18*sin(2*PI*120*t*(1+0.003*sin(2*PI*0.1*t))) + 0.1*sin(2*PI*175*t) + 0.06*sin(2*PI*240*t)':s=44100:d=30",
        "-filter_complex",
        "[0:a]aecho=0.8:0.9:100|250:0.35|0.25,tremolo=f=0.8:d=0.3,lowpass=f=500,volume=1.4,dynaudnorm=p=0.9[out]",
        "-map", "[out]", "-t", "30", "-c:a", "libmp3lame", "-b:a", "192k", "-y", str(track4)
    ]

    for name, cmd in [
        ("dark_psychology_drone", cmd1),
        ("deep_contemplation_pad", cmd2),
        ("suspense_tension", cmd3),
        ("subconscious_mind", cmd4),
    ]:
        print(f"Generating {name}...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Failed {name}: {res.stderr}")
            sys.exit(1)
        print(f"Done: {name}.mp3")

if __name__ == "__main__":
    from arabic_video_brief.media import find_ffmpeg
    ffmpeg = find_ffmpeg()
    out = Path(__file__).resolve().parents[1] / "assets" / "music"
    generate_tracks(out, ffmpeg)
