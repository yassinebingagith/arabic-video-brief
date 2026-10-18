import json
from pathlib import Path

import pytest
from PIL import Image

from arabic_video_brief.v3_assets import (
    accept_image,
    check_copy_digits,
    normalize_authored_copy,
    normalize_digits,
    save_image,
)


def _example_pack(root: Path) -> Path:
    pack = root / "v3"
    for name in ("instagram", "facebook", "references"):
        (pack / name).mkdir(parents=True)
    Image.new("RGB", (1280, 720), "blue").save(pack / "references/source-thumbnail.jpg")
    (pack / "references/source-transcript.txt").write_text("Original: ٢١", encoding="utf-8")
    (pack / "instagram/slide01.prompt.txt").write_text("اليوم ٢١", encoding="utf-8")
    (pack / "instagram/slide02.prompt.txt").write_text("الأيام ١–١٢", encoding="utf-8")
    (pack / "facebook/photo01.prompt.txt").write_text("الأيام ٢١–٣٥", encoding="utf-8")
    (pack / "instagram/caption.txt").write_text("عمر ٣٥", encoding="utf-8")
    (pack / "facebook/caption.txt").write_text("٢١ يوماً", encoding="utf-8")
    (pack / "production-pack.md").write_text("٢١–٣٥", encoding="utf-8")
    (pack / "script.json").write_text(json.dumps({"headline": "اليوم ٢١"}, ensure_ascii=False), encoding="utf-8")
    thumb = {"order": 1, "role": "source_thumbnail", "path": "references/source-thumbnail.jpg"}
    anchor = {"order": 2, "role": "style_anchor", "path": "instagram/slide01.png", "image_id": "ig-slide01"}
    rows = [
        {"id": "ig-slide01", "platform": "instagram", "prompt_path": "instagram/slide01.prompt.txt",
         "output_path": "instagram/slide01.png", "inputs": [thumb], "depends_on": [], "status": "prompt_ready"},
        {"id": "ig-slide02", "platform": "instagram", "prompt_path": "instagram/slide02.prompt.txt",
         "output_path": "instagram/slide02.png", "inputs": [thumb, anchor], "depends_on": ["ig-slide01"],
         "status": "pending_anchor"},
        {"id": "fb-photo01", "platform": "facebook", "prompt_path": "facebook/photo01.prompt.txt",
         "output_path": "facebook/photo01.png", "inputs": [thumb, anchor], "depends_on": ["ig-slide01"],
         "status": "pending_anchor"},
    ]
    (pack / "generation-plan.json").write_text(json.dumps({
        "mode": "v3", "execution": "manual", "anchor_id": "ig-slide01",
        "source": {"thumbnail_path": "references/source-thumbnail.jpg"}, "images": rows
    }), encoding="utf-8")
    return pack


def test_western_number_rule_and_source_preservation(tmp_path: Path):
    pack = _example_pack(tmp_path)
    assert normalize_digits("٢١–٣٥ / ۲۱-۳۵") == "21–35 / 21-35"
    assert check_copy_digits(pack)["status"] == "fail"
    result = normalize_authored_copy(pack)
    assert result["status"] == "pass"
    assert len(result["changed"]) == 7
    assert check_copy_digits(pack)["status"] == "pass"
    assert "٢١" in (pack / "references/source-transcript.txt").read_text(encoding="utf-8")
    assert (pack / "references/source-thumbnail.jpg").exists()


def test_anchor_first_registration_and_manual_acceptance(tmp_path: Path):
    pack = _example_pack(tmp_path)
    normalize_authored_copy(pack)
    source = tmp_path / "download.png"
    Image.new("RGB", (1101, 1376), "pink").save(source)
    with pytest.raises(ValueError, match="Accept and save"):
        save_image(pack, "ig-slide02", source, "chatgpt_mcp")
    first = save_image(pack, "ig-slide01", source, "chatgpt_mcp")
    assert first["status"] == "generated"
    assert (pack / "generation-sources/ig-slide01.png").read_bytes() == source.read_bytes()
    with Image.open(pack / "instagram/slide01.png") as img:
        assert img.size == (1080, 1350)
    assert json.loads((pack / "generation-plan.json").read_text())["execution"] == "chatgpt_mcp"
    with pytest.raises(ValueError, match="Visual review"):
        accept_image(pack, "ig-slide01")
    with pytest.raises(ValueError, match="already exists"):
        save_image(pack, "ig-slide01", source, "chatgpt_mcp")
    with pytest.raises(ValueError, match="Accept and save"):
        save_image(pack, "fb-photo01", source, "chatgpt_mcp")
    accept_image(pack, "ig-slide01", reviewed=True)
    saved = save_image(pack, "ig-slide02", source, "chatgpt_mcp")
    assert saved["status"] == "generated"
    save_image(pack, "fb-photo01", source, "chatgpt_mcp")
    plan = json.loads((pack / "generation-plan.json").read_text(encoding="utf-8"))
    assert [r["status"] for r in plan["images"]] == ["accepted", "generated", "generated"]
    assert plan["images"][1]["inputs"][1]["path"] == "instagram/slide01.png"


def test_reject_wrong_ratio_and_reference_tampering(tmp_path: Path):
    pack = _example_pack(tmp_path)
    normalize_authored_copy(pack)
    source = tmp_path / "wrong.png"
    Image.new("RGB", (1000, 1000)).save(source)
    with pytest.raises(ValueError, match="4:5 portrait"):
        save_image(pack, "ig-slide01", source, "manual")
    assert not (pack / "instagram/slide01.png").exists()
    plan = json.loads((pack / "generation-plan.json").read_text())
    plan["images"][0]["inputs"][0]["path"] = "../other.jpg"
    (pack / "generation-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="source thumbnail"):
        save_image(pack, "ig-slide01", source, "manual")
