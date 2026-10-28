import json
from pathlib import Path

import pytest

from arabic_video_brief.render_runtime import load_render_runtime


def write_runtime(root):
    root.mkdir(parents=True,exist_ok=True)
    binaries=root / "node_modules" / "fixture tools"
    binaries.mkdir(parents=True)
    runtime={"PROJECT_ROOT":str(root.resolve())}
    for key in ("NODE_BIN","CHROME_BIN","FFMPEG_BIN","FFPROBE_BIN","HYPERFRAMES_CLI","GSAP_JS"):
        file=binaries / key
        file.write_text("fixture")
        runtime[key]=str(file.resolve())
    (root / ".runtime").mkdir()
    (root / ".runtime/render-runtime.json").write_text(json.dumps(runtime))
    return runtime


def test_missing_renderer_has_install_instruction(tmp_path):
    with pytest.raises(RuntimeError,match="setup.py"):
        load_render_runtime(tmp_path)


def test_renderer_uses_its_own_checkout_in_path_with_spaces(tmp_path,monkeypatch):
    for key in ("CHROME_BIN","FFMPEG_BIN","FFPROBE_BIN"):
        monkeypatch.delenv(key,raising=False)
    root=tmp_path / "another users project"
    expected=write_runtime(root)
    assert load_render_runtime(root)==expected


def test_moved_checkout_requires_refresh(tmp_path):
    root=tmp_path / "checkout"
    data=write_runtime(root)
    data["PROJECT_ROOT"]=str(tmp_path / "old checkout")
    (root / ".runtime/render-runtime.json").write_text(json.dumps(data))
    with pytest.raises(RuntimeError,match="moved"):
        load_render_runtime(root)


def test_invalid_tool_override_is_reported(tmp_path,monkeypatch):
    write_runtime(tmp_path)
    monkeypatch.setenv("CHROME_BIN",str(tmp_path / "missing browser"))
    with pytest.raises(RuntimeError,match="CHROME_BIN"):
        load_render_runtime(tmp_path)
