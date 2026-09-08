"""Animate the fifteen-panel agent scaling figure used by the project page.

The published PNG remains the source of truth. All fifteen plot interiors are
revealed in sync along their token axes while the legend, titles, axes, and
labels stay fixed. The final frame reproduces the static figure.
"""

from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "static" / "images" / "main_results_15panel.png"
OUTPUT = ROOT / "static" / "images" / "main_results_15panel.gif"

OUTPUT_WIDTH = 1600
DRAW_FRAMES = 42
HOLD_FRAMES = 13
FRAME_DURATION_MS = 90

# Plot interiors in the 2007 x 896 source image. Masks stop just above each
# x-axis so that chart furniture remains stable while the data are revealed.
COLUMN_BOUNDS = (
    (153, 460),
    (528, 833),
    (903, 1208),
    (1278, 1584),
    (1654, 1961),
)
ROW_BOUNDS = (
    (136, 328),
    (366, 549),
    (580, 774),
)


def eased(progress):
    return progress * progress * (3.0 - 2.0 * progress)


def build_animation():
    source = Image.open(SOURCE).convert("RGB")
    scale = OUTPUT_WIDTH / source.width
    output_height = round(source.height * scale)
    base = source.resize((OUTPUT_WIDTH, output_height), Image.Resampling.LANCZOS)
    columns = [tuple(round(value * scale) for value in pair) for pair in COLUMN_BOUNDS]
    rows = [tuple(round(value * scale) for value in pair) for pair in ROW_BOUNDS]

    frames = []
    for frame_index in range(DRAW_FRAMES):
        progress = eased(frame_index / (DRAW_FRAMES - 1))
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        for left, right in columns:
            reveal_x = round(left + progress * (right - left))
            if reveal_x >= right:
                continue
            for top, bottom in rows:
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
