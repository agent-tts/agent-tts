"""Build the animated teaser used by the project page.

Axes, labels, and legends remain fixed while the agent and human Elo curves
grow from left to right. The final frame matches the full paper result.
"""

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from plot_style import (
    G_BLUE,
    G_GREEN,
    G_RED,
    G_YELLOW,
    HUMAN_DARK,
    HUMAN_SOFT,
    INK,
    REF_DASH,
    REF_GREY,
    apply_style,
    apply_tier,
    finalize_headers,
    header_legend,
    lighten,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "data"
OUTPUT = ROOT / "static" / "images" / "main-figure.gif"

ANCHOR = 1000.0
AGENT_RUN_END_H = 24.0
X_END_H = 264.0
DRAW_FRAMES = 42
HOLD_FRAMES = 12

COLORS = {
    "kimi": apply_tier(G_YELLOW, "medium"),
    "codex": apply_tier(G_BLUE, "medium"),
    "claude": apply_tier(G_RED, "medium"),
    "gemini": apply_tier(G_GREEN, "medium"),
}
SYSTEMS = tuple(COLORS)
JOINT_ORDER = ("human-top10", "human-top50", "codex", "claude")
JOINT_STYLES = {
    "human-top10": dict(color=HUMAN_DARK, marker="o", lw=2.4, ms=4.5, ls="-", label="Top-10 humans"),
    "human-top50": dict(color=HUMAN_SOFT, marker="o", lw=2.2, ms=4.2, ls="-", label="Top-50 humans"),
    "codex": dict(color=COLORS["codex"], marker="s", lw=1.8, ms=4.2, ls="--", label="GPT-5.5"),
    "claude": dict(color=COLORS["claude"], marker="^", lw=1.8, ms=4.5, ls="--", label="Opus 4.8"),
}


def read_agent_curves():
    curves = defaultdict(list)
    with (DATA / "teaser_selfelo_ci.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            curves[row["agent"]].append(
                tuple(float(row[key]) for key in ("checkpoint", "elo", "lo95", "hi95"))
            )
    for rows in curves.values():
        rows.sort()
    return curves


def read_joint_curves():
    curves = defaultdict(list)
    with (DATA / "ahc014_joint_elo.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            curves[row["source"]].append((float(row["cp_hours"]), float(row["elo"])))
    for rows in curves.values():
        rows.sort()
    return curves


def sampling_reference(x, x0):
    return ANCHOR + 400.0 * math.log10(x / x0)


def eased(progress):
    return progress * progress * (3.0 - 2.0 * progress)


def log_prefix(rows, progress):
    """Return a left-to-right prefix with one interpolated endpoint."""
    if progress <= 0:
        return [rows[0]]
    if progress >= 1:
        return rows

    logs = [math.log10(row[0]) for row in rows]
    target = logs[0] + progress * (logs[-1] - logs[0])
    prefix = [row for row, value in zip(rows, logs) if value <= target]
    upper = next(i for i, value in enumerate(logs) if value > target)
    lower = upper - 1
    mix = (target - logs[lower]) / (logs[upper] - logs[lower])
    interpolated = tuple(
        10**target if i == 0 else rows[lower][i] + mix * (rows[upper][i] - rows[lower][i])
        for i in range(len(rows[0]))
    )
    return [*prefix, interpolated]


def canvas_image(fig):
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba()).copy()
    return Image.fromarray(rgba).convert("RGB")


def build_animation():
    apply_style()
    agent_curves = read_agent_curves()
    joint_curves = read_joint_curves()

    fig, (ax_agent, ax_joint) = plt.subplots(
        1, 2, figsize=(9.6, 3.55), dpi=110, constrained_layout=True
    )
    fig.get_layout_engine().set(wspace=0.11)
    fig.patch.set_facecolor("white")

    agent_lines = {}
    for name in SYSTEMS:
        (agent_lines[name],) = ax_agent.plot(
            [], [], color=COLORS[name], linewidth=2.0, solid_capstyle="round", zorder=3
        )
    (reference_line,) = ax_agent.plot([], [], color=REF_GREY, linestyle=REF_DASH, linewidth=1.5, zorder=2)

    ax_agent.set_xscale("log")
    ax_agent.set_xlim(8.2e4, 1.15e8)
    ax_agent.set_xticks([1e5, 1e6, 1e7, 1e8])
    ax_agent.set_xticklabels(["100K", "1M", "10M", "100M"])
    ax_agent.minorticks_off()
    ax_agent.set_xlabel("Agent token budget", fontsize=12)
    ax_agent.set_ylabel("self-Elo", fontsize=12)
    ax_agent.set_title("Agents on four benchmarks")
    ax_agent.set_ylim(950, 2250)
    ax_agent.set_yticks([1000, 1400, 1800, 2200])

    joint_lines = {}
    extension_lines = {}
    for name in JOINT_ORDER:
        style = JOINT_STYLES[name]
        (joint_lines[name],) = ax_joint.plot(
            [], [], markeredgecolor="white", markeredgewidth=0.8,
            solid_capstyle="round", zorder=4, **style
        )
        if name in ("codex", "claude"):
            (extension_lines[name],) = ax_joint.plot(
                [], [], linestyle="--", lw=1.5,
                color=lighten(style["color"], 0.45), zorder=1
            )

    ax_joint.axvline(AGENT_RUN_END_H, color="grey", linewidth=1.2, alpha=0.35, zorder=0)
    ax_joint.annotate(
        "agent runs end", (AGENT_RUN_END_H, 2035), fontsize=8, color="grey",
        rotation=90, va="top", ha="right"
    )
    ax_joint.set_xscale("log")
    ax_joint.set_xlim(0.85, X_END_H * 1.6)
    ax_joint.set_xticks([1, 4, 24, 96, 264])
    ax_joint.set_xticklabels(["1h", "4h", "1d", "4d", "11d"])
    ax_joint.minorticks_off()
    ax_joint.set_xlabel("Wall-clock time in contest", fontsize=12)
    ax_joint.set_ylabel("joint-Elo", fontsize=12)
    ax_joint.set_title("Humans vs. agents on AHC014")
    ax_joint.set_ylim(930, 2060)
    ax_joint.set_yticks([1000, 1250, 1500, 1750, 2000])

    header_legend(ax_agent, [
        ("Kimi K2.7", COLORS["kimi"]),
        ("GPT-5.5", COLORS["codex"]),
        ("Opus 4.8", COLORS["claude"]),
        ("Gemini 3.5 Flash", COLORS["gemini"]),
    ], ncol=2, legend_size=9.5)
    header_legend(ax_joint, [
        (JOINT_STYLES[name]["label"], JOINT_STYLES[name]["color"], JOINT_STYLES[name]["marker"])
        for name in JOINT_ORDER
    ], ncol=2, legend_size=9.5)
    finalize_headers(fig)

    fills = []
    frames = []
    for frame_index in range(DRAW_FRAMES):
        progress = eased(frame_index / (DRAW_FRAMES - 1))
        for fill in fills:
            fill.remove()
        fills = []

        for name in SYSTEMS:
            rows = log_prefix(agent_curves[name], progress)
            xs, ys, lows, highs = zip(*rows)
            agent_lines[name].set_data(xs, ys)
            fills.append(ax_agent.fill_between(
                xs, lows, highs, color=COLORS[name], alpha=0.12, linewidth=0, zorder=2
            ))

        agent_x = [row[0] for row in agent_curves[SYSTEMS[0]]]
        ref_end = 10 ** (
            math.log10(agent_x[0]) + progress * (math.log10(agent_x[-1]) - math.log10(agent_x[0]))
        )
        reference_line.set_data(
            [agent_x[0], ref_end],
            [ANCHOR, sampling_reference(ref_end, agent_x[0])],
        )

        for name in JOINT_ORDER:
            rows = log_prefix(joint_curves[name], progress)
            joint_lines[name].set_data([row[0] for row in rows], [row[1] for row in rows])

        for name, line in extension_lines.items():
            if progress < 1:
                line.set_data([], [])
                continue
            points = joint_curves[name]
            (x1, y1), (x0, y0) = points[-2], points[-1]
            slope = (y0 - y1) / (math.log10(x0) - math.log10(x1))
            y_end = y0 + slope * (math.log10(X_END_H) - math.log10(x0))
            line.set_data([x0, X_END_H], [y0, y_end])

        frames.append(canvas_image(fig))

    frames.extend([frames[-1].copy() for _ in range(HOLD_FRAMES)])
    palette = frames[-1].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(
        OUTPUT,
        save_all=True,
        append_images=indexed[1:],
        duration=90,
        loop=0,
        disposal=2,
        optimize=True,
    )
    plt.close(fig)
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    build_animation()
