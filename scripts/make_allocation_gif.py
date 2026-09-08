"""Animate the token-scaling panels in the allocation figure.

The published PNG remains the source of truth. The top-right single-session
self-Elo panel and bottom-left allocation joint-Elo panel are revealed in sync
along their token axes. The other two panels and all chart furniture remain
fixed, and the final frame reproduces the static figure.
"""

from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "static" / "images" / "allocation_main.png"
OUTPUT = ROOT / "static" / "images" / "allocation_main.gif"

OUTPUT_WIDTH = 1576
DRAW_FRAMES = 42
HOLD_FRAMES = 13
FRAME_DURATION_MS = 90

# Animated plot interiors in the 1576 x 1136 source image. Each mask stops
# just above the x-axis, so axes and tick labels remain fixed.
SOURCE_PANELS = (
    (773, 116, 1540, 461),   # top-right: single-session self-Elo
    (149, 678, 920, 1023),  # bottom-left: allocation joint-Elo
)


def eased(progress):
    return progress * progress * (3.0 - 2.0 * progress)


def build_animation():
    source = Image.open(SOURCE).convert("RGB")
    scale = OUTPUT_WIDTH / source.width
    output_height = round(source.height * scale)
    base = source.resize((OUTPUT_WIDTH, output_height), Image.Resampling.LANCZOS)
    panels = [
        tuple(round(value * scale) for value in panel)
        for panel in SOURCE_PANELS
    ]

    frames = []
    for frame_index in range(DRAW_FRAMES):
        progress = eased(frame_index / (DRAW_FRAMES - 1))
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        for left, top, right, bottom in panels:
            reveal_x = round(left + progress * (right - left))
            if reveal_x < right:
                draw.rectangle((reveal_x, top, right, bottom), fill="white")
        frames.append(frame)

    frames.extend(frames[-1].copy() for _ in range(HOLD_FRAMES))
    palette = base.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    indexed = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in frames
    ]
    indexed[0].save(
        OUTPUT,
        save_all=True,
        append_images=indexed[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        optimize=True,
    )
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    build_animation()
