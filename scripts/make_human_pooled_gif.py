"""Animate the pooled human self-Elo figure used by the project page.

The published PNG remains the source of truth. The animation keeps the title,
legend, axes, and labels fixed while revealing both curves from 1h to 8d, so
the final frame exactly reproduces the static figure.
"""

from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "static" / "images" / "human_ahc_pooled.png"
OUTPUT = ROOT / "static" / "images" / "human_ahc_pooled.gif"

OUTPUT_WIDTH = 1200
DRAW_FRAMES = 40
HOLD_FRAMES = 12
FRAME_DURATION_MS = 90

# Plot interior in the 1398 x 950 source image. The mask stops above the
# x-axis, leaving all chart furniture visible throughout the animation.
SOURCE_PLOT = (225, 175, 1367, 765)


def eased(progress):
    return progress * progress * (3.0 - 2.0 * progress)


def build_animation():
    source = Image.open(SOURCE).convert("RGB")
    scale = OUTPUT_WIDTH / source.width
    output_height = round(source.height * scale)
    base = source.resize((OUTPUT_WIDTH, output_height), Image.Resampling.LANCZOS)
    left, top, right, bottom = (round(value * scale) for value in SOURCE_PLOT)

    frames = []
    for frame_index in range(DRAW_FRAMES):
        progress = eased(frame_index / (DRAW_FRAMES - 1))
        reveal_x = round(left + progress * (right - left))
        frame = base.copy()
        if reveal_x < right:
            ImageDraw.Draw(frame).rectangle(
                (reveal_x, top, right, bottom), fill="white"
            )
        frames.append(frame)

    frames.extend(frames[-1].copy() for _ in range(HOLD_FRAMES))
    palette = base.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
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
