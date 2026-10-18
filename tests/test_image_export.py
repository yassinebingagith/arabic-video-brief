import json
from pathlib import Path

from PIL import Image, PngImagePlugin

from arabic_video_brief.image_export import export_posting_image, prepare_v3_images


def test_metadata_removed_without_touching_original_or_pixels(tmp_path: Path):
    source = tmp_path / "original.png"
    image = Image.new("RGBA", (12, 9), (14, 50, 230, 120))
    info = PngImagePlugin.PngInfo()
    info.add_text("Software", "Example AI generator")
    info.add_text("XML:com.adobe.xmp", "c2pa example provenance")
    image.save(source, pnginfo=info)
    before = source.read_bytes()
    output = tmp_path / "posting.png"
    result = export_posting_image(source, output)
    assert source.read_bytes() == before
    with Image.open(output) as clean:
        assert clean.info == {}
        assert clean.mode == "RGBA"
        assert clean.tobytes() == image.tobytes()
    assert result["source_sha256"] != result["output_sha256"]


def test_palette_transparency_and_orientation_are_preserved(tmp_path: Path):
    source = tmp_path / "palette.png"
    image = Image.new("P", (6, 4), 1)
    image.putpalette([0, 0, 0, 255, 20, 70] + [0] * 762)
    image.save(source, transparency=0)
    output = tmp_path / "palette-posting.png"
    export_posting_image(source, output)
    with Image.open(source) as original, Image.open(output) as clean:
        assert clean.tobytes() == original.convert("RGBA").tobytes()
    oriented = tmp_path / "rotated.png"
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (8, 3), "red").save(oriented, exif=exif)
    export_posting_image(oriented, output)
    with Image.open(output) as clean:
        assert clean.size == (3, 8)
        assert not clean.getexif()


def test_pack_exports_only_platform_images_and_reports_bad_input(tmp_path: Path):
    pack = tmp_path / "v3"
    for directory in ("instagram", "facebook", "references"):
        (pack / directory).mkdir(parents=True)
    (pack / "generation-plan.json").write_text(json.dumps({"mode": "v3"}))
    Image.new("RGB", (10, 12)).save(pack / "instagram/slide01.png")
    Image.new("RGB", (10, 12)).save(pack / "facebook/photo.png")
    Image.new("RGB", (10, 12)).save(pack / "references/source.png")
    (pack / "facebook/broken.png").write_bytes(b"not an image")
    result = prepare_v3_images(tmp_path)
    assert result["exported"] == 2
    assert result["failed"] == 1
    assert result["status"] == "partial"
    assert not (pack / "posting-ready/references").exists()
    assert (pack / "posting-ready/instagram/slide01.png").exists()
