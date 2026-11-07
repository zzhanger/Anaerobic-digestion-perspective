# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 21:34:54 2026

@author: zz1405
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from matplotlib.ticker import ScalarFormatter


# ============================================================
# Global formatting
# ============================================================

plt.rcParams.update({
    "font.family": "Arial",
    "axes.unicode_minus": False,
    "axes.labelsize": 26,
    "xtick.labelsize": 22,
    "ytick.labelsize": 22,
    "legend.fontsize": 24,
    "pdf.fonttype": 42,
    "ps.fonttype": 42
})


# ============================================================
# Manuscript color palette
# ============================================================

COLOR_PINK = "#E7B4C5"       # warm
COLOR_GREEN = "#9ACBAA"      # cool
COLOR_BLUE = "#81B8DC"       # cool
COLOR_WARM_GREY = "#D3CBC8"  # neutral warm

COLOR_DARK = "#3A3A3A"
COLOR_AXIS = "#555555"


# ============================================================
# 1. Load revised reference-model results
# ============================================================

print("Loading reference electricity-recovery model...")

REFERENCE_CSV = (
    Path(__file__).resolve().parent
    / "Electricity recovery potential reference line.csv"
)

if not REFERENCE_CSV.exists():
    raise FileNotFoundError(
        f"Reference CSV not found: {REFERENCE_CSV}\n"
        "Run 'Electricity production Reference.py' first "
        "(make sure its main() executes)."
    )

ref_df = pd.read_csv(REFERENCE_CSV)


# Prevent accidentally plotting an outdated reference CSV.
_expected_at_100 = 0.0006398402625 * 100  # Table S1 benchmark
# [FIX] Float-safe comparison instead of exact .eq(100).
mask_100 = np.isclose(ref_df["BOD5_mg_L"], 100.0)
_actual_at_100 = ref_df.loc[mask_100, "Electricity_kWh_m3"]
if _actual_at_100.empty or not np.isclose(
    _actual_at_100.iloc[0], _expected_at_100, rtol=0.002
):
    raise ValueError(
        "Reference CSV does not match Table S1.\n"
        "Run 'Electricity production Reference.py' first "
        "(ensure its main() executes)."
    )


ref_df = (
    ref_df
    .rename(columns={
        "BOD5_mg_L": "BOD",
        "Electricity_kWh_m3": "E_potential_kWh"
    })
    .sort_values("BOD")
    .dropna(subset=["BOD", "E_potential_kWh"])
)


# ============================================================
# 2. Energy-neutral / energy-positive facilities
# ============================================================
# `value` is the reported electricity recovery potential in kWh m^-3.

facility_data = [
    {"Facility": "Point Loma (U.S.)",               "BOD": 255, "value": 0.210152859},
    {"Facility": "Sheboygan (U.S.)",                "BOD": 167, "value": 0.489632991},
    {"Facility": "EBMUD (U.S.)",                    "BOD": 380, "value": 0.507265522},
    {"Facility": "Strass im Zillertal (Austria)",   "BOD": 291, "value": 0.280383091},
    {"Facility": "Marselisborg (Denmark)",          "BOD": 470, "value": 0.500271971},
    {"Facility": "Ejby Mølle (Denmark)",            "BOD": 250, "value": 0.492106290},
    {"Facility": "Grevesmühlen (Germany)",          "BOD": 500, "value": 0.307628798},
]

facility_df = pd.DataFrame(facility_data)


# ============================================================
# 3. Create figure
# ============================================================

fig, ax = plt.subplots(figsize=(15, 10))


# ============================================================
# 4. Typical WWTP electricity-demand range
# ============================================================

demand_lower = 0.25
demand_upper = 0.60

ax.axhspan(
    demand_lower, demand_upper,
    color=COLOR_WARM_GREY, alpha=0.50, zorder=0,
)

for y in [demand_lower, demand_upper]:
    ax.axhline(
        y, color="#8A8A8A", linestyle=":",
        linewidth=1.2, zorder=1,
    )


# ============================================================
# 5. Reference electricity-recovery curve
# ============================================================

ax.plot(
    ref_df["BOD"], ref_df["E_potential_kWh"],
    color=COLOR_DARK, linewidth=2.6,
    linestyle="--", zorder=4,
)

# Interpolator for regional guide lines.
# Ref data range is 100-550; regional bounds lie inside it.
ref_interp = interp1d(
    ref_df["BOD"], ref_df["E_potential_kWh"],
    kind="linear", bounds_error=False, fill_value="extrapolate",
)


# ============================================================
# 6. Representative regional influent BOD5 ranges
# ============================================================

regions = [
    {"name": "Asia",          "range_text": "100–150",
     "BOD_min": 100, "BOD_max": 150, "y": 0.030, "color": COLOR_PINK},
    {"name": "North America", "range_text": "160–300",
     "BOD_min": 160, "BOD_max": 300, "y": 0.047, "color": COLOR_GREEN},
    {"name": "Europe",        "range_text": "130–530",
     "BOD_min": 130, "BOD_max": 530, "y": 0.064, "color": COLOR_BLUE},
]

for region in regions:
    x_min, x_max = region["BOD_min"], region["BOD_max"]
    y, color = region["y"], region["color"]

    ax.hlines(y=y, xmin=x_min, xmax=x_max,
              color=color, linewidth=3, zorder=3)

    cap_height = 0.006
    ax.vlines([x_min, x_max],
              ymin=y - cap_height, ymax=y + cap_height,
              color=color, linewidth=2, zorder=3)

    ax.text(
        (x_min + x_max) / 1.9, y + 0.01,
        f"{region['name']}\n{region['range_text']} mg L$^{{-1}}$",
        ha="center", va="bottom", fontsize=22, color="#222222",
        bbox={
            "boxstyle": "round,pad=0.22",
            "facecolor": color, "edgecolor": "none", "alpha": 0.85,
        },
        zorder=5,
    )

    for x in [x_min, x_max]:
        y_top = float(ref_interp(x))
        ax.vlines(
            x=x, ymin=0, ymax=y_top,
            color=color, linestyle=":", linewidth=1.1,
            alpha=0.60, zorder=1,
        )


# ============================================================
# 7. Plot energy-neutral / energy-positive facilities
# ============================================================

ax.scatter(
    facility_df["BOD"], facility_df["value"],
    s=85, facecolor="#333333",
    edgecolor="white", linewidth=1.0, zorder=10,
)


# ============================================================
# 8. Facility labels
# ============================================================

label_offsets = {
    "Point Loma (U.S.)":              (18, -18),
    "Sheboygan (U.S.)":               (12, 30),
    "EBMUD (U.S.)":                   (12, 18),
    "Strass im Zillertal (Austria)":  (15, 18),
    "Marselisborg (Denmark)":         (-35, -32),
    "Ejby Mølle (Denmark)":           (16, -30),
    "Grevesmühlen (Germany)":         (-122, 18),
}

for _, row in facility_df.iterrows():
    offset = label_offsets.get(row["Facility"], (10, 10))
    ax.annotate(
        row["Facility"],
        xy=(row["BOD"], row["value"]),
        xytext=offset, textcoords="offset points",
        fontsize=22, ha="left", va="center",
        bbox={
            "boxstyle": "round,pad=0.22",
            "facecolor": "white", "edgecolor": "#777777",
            "linewidth": 0.8, "alpha": 0.92,
        },
        arrowprops={
            "arrowstyle": "-", "color": "#666666",
            "linewidth": 0.8, "shrinkA": 2, "shrinkB": 4,
        },
        zorder=12,
    )


# ============================================================
# 9. Legend
# ============================================================

legend_elements = [
    Line2D([0], [0], color=COLOR_DARK, linestyle="--", linewidth=2.6,
           label="Reference electricity recovery potential"),
    mpatches.Patch(
        facecolor=COLOR_WARM_GREY, edgecolor="none", alpha=0.50,
        label="Typical WWTP electricity demand (0.25–0.60 kWh m$^{-3}$)",
    ),
    Line2D([0], [0], marker="o", linestyle="none",
           markerfacecolor="#333333", markeredgecolor="white",
           markersize=9,
           label="Energy-neutral/positive facilities"),
]

ax.legend(
    handles=legend_elements,
    loc="upper left",
    bbox_to_anchor=(0.01, 1.02),  # [CHG] 1.05 -> 1.02 (avoids clipping)
    frameon=False,
)


# ============================================================
# 10. Axes
# ============================================================

ax.set_xlim(90, 550)
ax.set_ylim(0, 0.75)

ax.set_xlabel("Influent BOD$_5$ (mg L$^{-1}$)", fontsize=26)
ax.set_ylabel("Electricity recovery potential (kWh m$^{-3}$)", fontsize=26)


# ============================================================
# 11. Axis formatting
# ============================================================

formatter = ScalarFormatter()
formatter.set_scientific(False)
formatter.set_useOffset(False)
ax.xaxis.set_major_formatter(formatter)
ax.yaxis.set_major_formatter(formatter)


# ============================================================
# 12. Grid
# ============================================================

ax.grid(axis="both", linestyle="-", linewidth=0.6,
        alpha=0.18, zorder=0)


# ============================================================
# 13. Clean frame
# ============================================================

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(COLOR_AXIS)
ax.spines["bottom"].set_color(COLOR_AXIS)

ax.tick_params(axis="both", which="major",
               length=5, width=1, color=COLOR_AXIS)


# ============================================================
# 14. Final layout
# ============================================================

plt.tight_layout()

# [ADD] Save figure beside script (optional but useful for the manuscript).
fig.savefig(
    Path(__file__).resolve().parent
    / "Energy recovery potentials.png",
    dpi=300, bbox_inches="tight",
)

plt.show()