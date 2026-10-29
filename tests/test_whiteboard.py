from PIL import Image
import numpy as np

from arabic_video_brief.whiteboard import partial_mask, page_frame


def test_writing_reveals_strokes_and_preserves_finished_word():
    glyph = Image.new("L", (100, 20), 255)
    word = {"strokes": [{"points": [[0, 10], [99, 10]], "length": 99}], "brush_width": 20}
    empty = np.asarray(partial_mask(word, glyph, 0))
    half = np.asarray(partial_mask(word, glyph, .5))
    full = np.asarray(partial_mask(word, glyph, 1))
    assert empty.sum() == 0
    assert 0 < half.sum() < full.sum()
    assert np.array_equal(full, np.asarray(glyph))


def test_marker_sweeps_from_right_to_left_after_writing():
    base = Image.new("RGB", (100, 40), (2, 6, 13))
    data = {"index": 2, "duration": 5, "motion": {"fade": .18}, "words": [],
            "markers": [{"start": 1, "duration": 1, "box": [10, 10, 90, 30]}]}
    before = page_frame(data, base, base, [], .9)
    half = page_frame(data, base, base, [], 1.5)
    full = page_frame(data, base, base, [], 2.5)
    assert half.getpixel((20, 20)) == before.getpixel((20, 20))
    assert half.getpixel((80, 20)) != before.getpixel((80, 20))
    assert full.getpixel((20, 20)) != before.getpixel((20, 20))


def test_completed_text_stays_visible_until_page_fade():
    base = Image.new("RGB", (40, 40))
    word = {"start": .2, "end": 1, "xy": [10, 10]}
    data = {"index": 2, "duration": 5, "motion": {"fade": .2}, "words": [word], "markers": []}
    mask = Image.new("L", (10, 10), 255)
    assert page_frame(data, base, base, [mask], .1).getpixel((12, 12)) == (0, 0, 0)
    assert page_frame(data, base, base, [mask], 1.1).tobytes() == page_frame(data, base, base, [mask], 4).tobytes()
