"""Animate the scaling curves in the three strategy-carousel figures.

The published PNGs remain the source of truth. Each plot interior is revealed
from left to right while titles, legends, axes, and labels stay fixed. The
final frame reproduces the corresponding static figure.
"""

from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
IMAGE_DIR = ROOT / "static" / "images"

OUTPUT_WIDTH = 1576
DRAW_FRAMES = 36
HOLD_FRAMES = 14
FRAME_DURATION_MS = 90

FIGURES = (
    (
        "optmethods_p0_elo_panels.png",
        "optmethods_p0_elo_panels.gif",
        ((242, 169, 953, 516), (1274, 169, 1980, 516)),
    ),
    (
        "ttt_p0_selfelo.png",
        "ttt_p0_selfelo.gif",
        ((214, 169, 944, 511), (1240, 169, 1971, 511)),
    ),
    (
        "qwen_size_scaling.png",
        "qwen_size_scaling.gif",
        ((191, 187, 932, 523), (1213, 187, 1954, 523)),
    ),
)


def eased(progress):
    return progress * progress * (3.0 - 2.0 * progress)


def build_animation(source_name, output_name, source_panels):
    source = Image.open(IMAGE_DIR / source_name).convert("RGB")
    scale = OUTPUT_WIDTH / source.width
    output_height = round(source.height * scale)
    base = source.resize((OUTPUT_WIDTH, output_height), Image.Resampling.LANCZOS)
    panels = [
        tuple(round(value * scale) for value in panel)
        for panel in source_panels
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
    output = IMAGE_DIR / output_name
    indexed[0].save(
        output,
        save_all=True,
        append_images=indexed[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        optimize=True,
    )
    print(f"wrote {output} ({output.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    for figure in FIGURES:
        build_animation(*figure)
