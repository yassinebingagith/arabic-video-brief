"""Discover FFmpeg/FFprobe or install their portable Python-managed binaries."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


def _tool(names, command):
    for name in names:
        value=os.environ.get(name)
        if value:
            file=shutil.which(value) or str(Path(value).expanduser().resolve())
            if not Path(file).is_file():
                raise RuntimeError(f"Configured {name} does not exist: {file}")
            return file
    return shutil.which(command)


def resolve_media_tools(download=True):
    ffmpeg=_tool(("FFMPEG_BINARY","FFMPEG_BIN"),"ffmpeg")
    ffprobe=_tool(("FFPROBE_BINARY","FFPROBE_BIN"),"ffprobe")
    if not ffmpeg or not ffprobe:
        if not download:
            raise RuntimeError("FFmpeg and FFprobe are required. Run python scripts/setup.py.")
        try:
            from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise
            installed_ffmpeg,installed_ffprobe=get_or_fetch_platform_executables_else_raise()
            ffmpeg=ffmpeg or installed_ffmpeg
            ffprobe=ffprobe or installed_ffprobe
        except (ImportError,OSError,RuntimeError) as error:
            raise RuntimeError("Media tools are unavailable. Run python scripts/setup.py, or install FFmpeg and FFprobe on PATH.") from error
    return {"FFMPEG_BIN":str(Path(ffmpeg).resolve()),"FFPROBE_BIN":str(Path(ffprobe).resolve())}


def check_media_tools():
    tools=resolve_media_tools()
    versions={}
    for key,file in tools.items():
        result=subprocess.run([file,"-version"],check=True,capture_output=True,text=True,timeout=30)
        versions[key]=(result.stdout or result.stderr).splitlines()[0]
    return {"ready":True,"tools":tools,"versions":versions}
