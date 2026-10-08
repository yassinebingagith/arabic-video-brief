import tempfile
from pathlib import Path
from PIL import Image

from arabic_video_brief.thumbnail.sanitizer import (
    has_ai_metadata,
    sanitize_image,
    sanitize_folder_images,
)


def test_sanitize_image_strips_fake_c2pa(tmp_path: Path):
    img_path = tmp_path / "cover_facebook_4x5.png"
    im = Image.new("RGB", (200, 250), color=(100, 150, 200))
    im.save(img_path, "PNG")

    # Inject fake C2PA / OpenAI marker
    data = img_path.read_bytes()
    injected_data = data + b"caBX\x00\x00\x00\x10c2paOpenAItrainedAlgorithmicMedia"
    img_path.write_bytes(injected_data)

    assert has_ai_metadata(img_path) is True

    # Sanitize
    cleaned = sanitize_image(img_path)
    assert cleaned is True
    assert has_ai_metadata(img_path) is False

    # Verify image opens cleanly
    with Image.open(img_path) as verified_im:
        assert verified_im.size == (200, 250)


def test_sanitize_folder_images(tmp_path: Path):
    fb_path = tmp_path / "cover_facebook_4x5.png"
    im = Image.new("RGB", (100, 100), color=(20, 20, 20))
    im.save(fb_path, "PNG")
    fb_path.write_bytes(fb_path.read_bytes() + b"ChatGPTdnamec2pa")

    assert has_ai_metadata(fb_path) is True
    cleaned_list = sanitize_folder_images(tmp_path)
    assert len(cleaned_list) == 1
    assert cleaned_list[0].name == "cover_facebook_4x5.png"
    assert has_ai_metadata(fb_path) is False
