"""
charts.py — Matplotlib chart widgets embedded in PyQt6.
"""

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QSizePolicy

DARK_BG   = "#1c2128"
TEXT_COL  = "#e6edf3"
MUTED_COL = "#8b949e"

PALETTE = [
    "#58a6ff", "#3fb950", "#d29922",
    "#f85149", "#bc8cff",
]


class BaseChart(FigureCanvas):
    def __init__(self, width: int = 5, height: int = 4, dpi: int = 96):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=DARK_BG)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _style_axes(self, ax):
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors=MUTED_COL, labelsize=9)
        ax.spines[:].set_color("#30363d")
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color(MUTED_COL)


class BarChartWidget(BaseChart):
    """Vertical bar chart of votes per candidate."""

    def __init__(self):
        super().__init__(width=5, height=3)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout(pad=1.5)
        self._names: list[str] = []
        self._values: list[int] = []

    def update_data(self, candidate_map: dict[int, str], totals: dict[int, int]) -> None:
        self.ax.clear()
        self._names  = [candidate_map.get(i, f"C{i}") for i in sorted(candidate_map)]
        self._values = [totals.get(i, 0) for i in sorted(candidate_map)]

        bars = self.ax.bar(self._names, self._values, color=PALETTE, edgecolor="none", width=0.55)

        # value labels on top of bars
        for bar, val in zip(bars, self._values):
            if val > 0:
                self.ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.15,
                    str(val),
                    ha="center", va="bottom",
                    color=TEXT_COL, fontsize=9, fontweight="bold",
                )

        self.ax.set_title("Votes per Candidate", color=TEXT_COL, fontsize=11, pad=8)
        self.ax.set_ylabel("Votes", color=MUTED_COL, fontsize=9)
        self._style_axes(self.ax)
        self.ax.set_ylim(0, max(self._values or [1]) + 1)
        self.fig.tight_layout(pad=1.5)
        self.draw()


class PieChartWidget(BaseChart):
    """Pie chart showing vote distribution."""

    def __init__(self):
        super().__init__(width=4, height=3)
        self.ax = self.fig.add_subplot(111)

    def update_data(self, candidate_map: dict[int, str], totals: dict[int, int]) -> None:
        self.ax.clear()
        names  = [candidate_map.get(i, f"C{i}") for i in sorted(candidate_map)]
        values = [totals.get(i, 0) for i in sorted(candidate_map)]

        if sum(values) == 0:
            self.ax.text(
                0.5, 0.5, "No votes yet",
                transform=self.ax.transAxes,
                ha="center", va="center",
                color=MUTED_COL, fontsize=11,
            )
            self.ax.axis("off")
        else:
            wedges, texts, autotexts = self.ax.pie(
                values,
                labels=names,
                colors=PALETTE,
                autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
                startangle=140,
                wedgeprops={"edgecolor": DARK_BG, "linewidth": 2},
            )
            for t in texts:
                t.set_color(TEXT_COL)
                t.set_fontsize(8)
            for at in autotexts:
                at.set_color(DARK_BG)
                at.set_fontsize(8)
                at.set_fontweight("bold")

        self.ax.set_title("Vote Distribution", color=TEXT_COL, fontsize=11, pad=8)
        self.ax.set_facecolor(DARK_BG)
        self.fig.tight_layout(pad=1.0)
        self.draw()
