from pathlib import Path
import pytest

from arabic_video_brief.media_tools import resolve_media_tools


def test_missing_tools_have_setup_instruction(monkeypatch):
    for key in ("FFMPEG_BINARY","FFMPEG_BIN","FFPROBE_BINARY","FFPROBE_BIN"):
        monkeypatch.delenv(key,raising=False)
    monkeypatch.setattr("shutil.which",lambda _:None)
    with pytest.raises(RuntimeError,match="setup.py"):
        resolve_media_tools(download=False)


def test_explicit_paths_with_spaces(tmp_path,monkeypatch):
    for key in ("FFMPEG_BIN","FFPROBE_BIN"):
        monkeypatch.delenv(key,raising=False)
    paths=[]
    for name in ("ffmpeg","ffprobe"):
        file=tmp_path / "another users tools" / name
        file.parent.mkdir(exist_ok=True)
        file.write_text("fixture")
        paths.append(file.resolve())
    monkeypatch.setenv("FFMPEG_BINARY",str(paths[0]))
    monkeypatch.setenv("FFPROBE_BINARY",str(paths[1]))
    assert resolve_media_tools(download=False)=={"FFMPEG_BIN":str(paths[0]),"FFPROBE_BIN":str(paths[1])}


def test_invalid_override_is_reported(tmp_path,monkeypatch):
    monkeypatch.setenv("FFMPEG_BINARY",str(tmp_path / "missing ffmpeg"))
    with pytest.raises(RuntimeError,match="FFMPEG_BINARY"):
        resolve_media_tools(download=False)
