"""Shared chart style: restrained, one message per chart."""
import matplotlib as mpl

INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"
BLUE = "#2a78d6"     # cash
ORANGE = "#eb6834"   # bonds / redemptions
AQUA = "#1baf7a"     # capital / subscriptions
SHADE = "#f1f0ec"


def apply():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.edgecolor": INK_2,
        "axes.labelcolor": INK_2,
        "axes.titlecolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "lines.linewidth": 2.0,
        "legend.frameon": False,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })


def source_note(fig, text):
    fig.text(0.01, -0.02, text, ha="left", va="top", fontsize=8, color=INK_2)


def save(fig, path):
    """Save a PNG for the README and a vector SVG of the same figure for publication."""
    from pathlib import Path
    path = Path(path)
    fig.savefig(path)
    fig.savefig(path.with_suffix(".svg"))

