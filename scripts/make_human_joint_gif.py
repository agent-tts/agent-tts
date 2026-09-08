"""Build the animated human-agent joint-Elo figure used by the project page.

The published PNG remains the source of truth. This script keeps its axes,
titles, legends, and labels fixed while revealing all three panels from left
to right, so the final animation frame exactly reproduces the static figure.
"""

from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "static" / "images" / "ale_joint.png"
OUTPUT = ROOT / "static" / "images" / "ale_joint.gif"

OUTPUT_WIDTH = 1600
DRAW_FRAMES = 42
HOLD_FRAMES = 12
FRAME_DURATION_MS = 90

# Plot interiors and terminal-label boxes in the 2659 x 885 source image.
# Keeping them separate prevents one panel's mask from touching the next y-axis.
SOURCE_PANELS = (
    (330, 262, 951, 739),
    (1096, 262, 1717, 739),
    (1862, 262, 2484, 739),
)
SOURCE_LABELS = (
    (952, 262, 980, 739),
    (1718, 262, 1748, 739),
    (2485, 262, 2570, 739),
)


def eased(progress):
    return progress * progress * (3.0 - 2.0 * progress)


def scaled_panels(scale):
    return tuple(tuple(round(value * scale) for value in panel) for panel in SOURCE_PANELS)


def build_animation():
    source = Image.open(SOURCE).convert("RGB")
    scale = OUTPUT_WIDTH / source.width
    output_height = round(source.height * scale)
    base = source.resize((OUTPUT_WIDTH, output_height), Image.Resampling.LANCZOS)
    panels = scaled_panels(scale)
    labels = tuple(tuple(round(value * scale) for value in box) for box in SOURCE_LABELS)

    frames = []
    for frame_index in range(DRAW_FRAMES):
        progress = eased(frame_index / (DRAW_FRAMES - 1))
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        for left, top, right, bottom in panels:
            reveal_x = round(left + progress * (right - left))
            if reveal_x < right:
                draw.rectangle((reveal_x, top, right, bottom), fill="white")
        if progress < 1:
            for box in labels:
                draw.rectangle(box, fill="white")
        frames.append(frame)

    frames.extend(frames[-1].copy() for _ in range(HOLD_FRAMES))
    palette = base.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
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
