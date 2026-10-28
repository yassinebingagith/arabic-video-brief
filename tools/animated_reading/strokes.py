"""Derive invisible writing-mask strokes from the existing Arabic font.

These paths are reveal guides only. The visible text remains native shaped SVG
text; a final mask rectangle restores its complete original glyph edges.
"""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw


def thin(binary):
    """Zhang–Suen thinning, with both deletion passes per iteration."""
    im = np.pad(binary.astype(np.uint8), 1)
    for _ in range(70):
        changed = False
        for second in (False, True):
            c = im[1:-1, 1:-1]
            ring = [im[:-2, 1:-1], im[:-2, 2:], im[1:-1, 2:], im[2:, 2:],
                    im[2:, 1:-1], im[2:, :-2], im[1:-1, :-2], im[:-2, :-2]]
            n = sum(ring)
            transitions = sum(((ring[i] == 0) & (ring[(i+1) % 8] == 1)).astype(np.uint8) for i in range(8))
            if second:
                branch = (ring[0]*ring[2]*ring[6] == 0) & (ring[0]*ring[4]*ring[6] == 0)
            else:
                branch = (ring[0]*ring[2]*ring[4] == 0) & (ring[2]*ring[4]*ring[6] == 0)
            remove = (c == 1) & (n >= 2) & (n <= 6) & (transitions == 1) & branch
            if remove.any():
                c[remove] = 0
                changed = True
        if not changed:
            break
    return im[1:-1, 1:-1]


def writing_strokes(text, font, visual_text, width, line_height):
    image = Image.new("L", (math.ceil(width)+24, line_height+24))
    ImageDraw.Draw(image).text((12, 0), visual_text, font=font, fill=255)
    skeleton = thin(np.asarray(image) > 64)
    pixels = {(int(x), int(y)) for y, x in np.argwhere(skeleton)}
    if not pixels:
        return []
    adjacent = {}
    for x, y in pixels:
        neighbors = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == dy == 0 or (x+dx, y+dy) not in pixels:
                    continue
                # Avoid triangular branches where an orthogonal route exists.
                if dx and dy and ((x+dx, y) in pixels or (x, y+dy) in pixels):
                    continue
                neighbors.append((x+dx, y+dy))
        adjacent[(x, y)] = neighbors
    visited = set()
    chains = []

    def edge(a, b):
        return tuple(sorted((a, b)))

    def trace(a, b):
        chain = [a, b]
        visited.add(edge(a, b))
        while len(adjacent[b]) == 2:
            following = next((p for p in adjacent[b] if p != a and edge(b, p) not in visited), None)
            if following is None:
                break
            a, b = b, following
            visited.add(edge(a, b))
            chain.append(b)
        return chain

    starts = sorted(pixels, key=lambda p: (-p[0], -p[1]))
    for a in starts:
        if len(adjacent[a]) != 2:
            if not adjacent[a]:
                chains.append([a, (a[0]+.1, a[1])])
            for b in adjacent[a]:
                if edge(a, b) not in visited:
                    chains.append(trace(a, b))
    for a in starts:
        for b in adjacent[a]:
            if edge(a, b) not in visited:
                chains.append(trace(a, b))
    # Trace the font's strokes from the right of each Arabic word toward its left.
    chains.sort(key=lambda chain: (-max(p[0] for p in chain), -len(chain)))
    result = []
    for chain in chains:
        if chain[0][0] < chain[-1][0]:
            chain.reverse()
        length = sum(math.dist(a, b) for a, b in zip(chain, chain[1:]))
        # Simplification changes the invisible guide, never the visible font.
        points = np.array(chain, np.float32).reshape(-1, 1, 2)
        points = cv2.approxPolyDP(points, .55, False).reshape(-1, 2)
        if len(points) == 1:
            points = np.array([points[0], points[0] + [.1, 0]])
        path = "M" + " L".join(f"{float(x)-12:.2f},{float(y):.2f}" for x, y in points)
        result.append({"d": path, "length": round(max(length, .1), 3)})
    return result
