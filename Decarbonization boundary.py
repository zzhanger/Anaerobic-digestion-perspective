# -*- coding: utf-8 -*-
"""
AD Electricity Displacement vs Methane Leakage Boundary Analysis
计算电力替代减排与甲烷泄漏排放相等时的临界条件
并标注各国电网碳排放强度

核心不等式:
V_CH4 * ρ_CH4 * GWP * a <= V_CH4 * (1-a) * CV_CH4 * MJ_to_kWh * η_ele * b

参数约定（纯甲烷，25°C, 1 atm）:
    ρ_CH4  = 0.657 kg/m³      （25°C 纯 CH4 密度）
    CV_CH4 = 32.8  MJ/m³      （25°C 纯 CH4 低位热值 LHV）
    GWP    = 28               （AR5, 100-yr）
    η_ele  = 0.38
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# Font settings
# ============================================================

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.rm'] = 'Arial'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42


# ============================================================
# Parameters  [FIX] 统一为纯甲烷热值
# ============================================================

d_CH4 = 0.657                 # kg/m³, 纯 CH4 @ 25°C, 1 atm
GWP_CH4 = 28                  # AR5, 100-yr
CALORIFIC_VALUE_CH4 = 32.8    # MJ/m³, 纯 CH4 LHV @ 25°C  (was 21.4 = 沼气值)
MJ_to_kWh = 0.2778            # 1 MJ = 1/3.6 kWh
eta_ele = 0.38

LHS_coef = d_CH4 * GWP_CH4
RHS_coef = CALORIFIC_VALUE_CH4 * MJ_to_kWh * eta_ele

KG_TO_G = 1000


# ============================================================
# Manuscript color palette
# ============================================================

COLOR_PINK = '#D98FA8'
COLOR_TERRACOTTA = '#BC825F'
COLOR_GREEN = '#82B996'
COLOR_BLUE = '#6FA7CB'
COLOR_COOL_GREY = '#AEB9BE'
COLOR_WARM_GREY = '#D3CBC8'

COLOR_DARK = '#3C5667'
COLOR_CHARCOAL = '#404040'


# ============================================================
# Climate-benefit colors
# ============================================================

# Pink = avoided grid emissions exceed methane leakage emissions
# Grey = methane leakage emissions exceed avoided grid emissions
COLOR_DISPLACEMENT_DOMINATES = "#D98FA8"        # pink
COLOR_LEAKAGE_DOMINATES = "#C9CED1"     # cool grey


# ============================================================
# Regional trajectory colors
# ============================================================

region_colors = {

    'Ontario (Canada)': '#4F8FB5',
    'Sweden': '#4F8260',
    'France': '#B45F7A',
    'Denmark': '#A96F4F',
    'Netherlands': '#8F536C',
    'Germany': '#6B8F70',

    'North (China)': '#A65F3F',
    'South (China)': '#D18A67',
    'Japan': '#6F8FA3',

    'US average': '#315F7A',
    'PJM / West (US)': '#A84F70',
    'PJM / Commonwealth Edison (US)': '#755B70',
    'NPCC / New England (US)': '#397766',
    'NPCC / Upstate New York (US)': '#769F83',
    'Midcontinent / Central (US)': '#824F3B'
}


# ============================================================
# Break-even boundary
# ============================================================

a_range_log = np.logspace(
    np.log10(0.001),
    np.log10(99.9),
    500
)

a_range_decimal = a_range_log / 100

b_critical_g = (
    (LHS_coef * a_range_decimal)
    /
    (RHS_coef * (1 - a_range_decimal))
    *
    KG_TO_G
)


# ============================================================
# [ADD] 2% leakage boundary, computed from current parameters
# (used for right-panel fill and reference line)
# ============================================================

def critical_b_g(a_percent):
    """Critical grid carbon intensity (g CO2e/kWh) at given leakage a (%)."""
    a_dec = a_percent / 100.0
    b_kg = (LHS_coef * a_dec) / (RHS_coef * (1 - a_dec))
    return b_kg * KG_TO_G


BOUNDARY_2PCT = critical_b_g(2.0)   # ≈ 108 g CO2e/kWh with pure-CH4 LHV
print(f"[info] Break-even grid intensity at 2% leakage = "
      f"{BOUNDARY_2PCT:.1f} g CO2e/kWh")


# ============================================================
# Right-panel data
# ============================================================

regions = [
    'Ontario (Canada)',
    'Sweden',
    'France',
    'Denmark',
    'Netherlands',
    'Germany',

    'North (China)',
    'South (China)',
    'Japan',

    'US average',
    'PJM / West (US)',
    'PJM / Commonwealth Edison (US)',
    'NPCC / New England (US)',
    'NPCC / Upstate New York (US)',
    'Midcontinent / Central (US)'
]


years = [2025, 2030, 2035]


data_raw = {

    'Ontario (Canada)': {2025: 38, 2030: None, 2035: None},
    'Sweden':           {2025: 7,  2030: None, 2035: None},
    'France':           {2025: 43, 2030: None, 2035: None},
    'Denmark':          {2025: 76, 2030: None, 2035: None},
    'Netherlands':       {2025: 235, 2030: None, 2035: None},
    'Germany':          {2025: 298, 2030: None, 2035: None},

    'North (China)':    {2025: 678.67, 2030: 621.33, 2035: 484.17},
    'South (China)':    {2025: 305.8,  2030: 245.6,  2035: 179.8},
    'Japan':            {2025: 280.00, 2030: 200.00, 2035: 36.00},

    'US average':       {2025: 318, 2030: 233, 2035: 137},
    'PJM / West (US)':  {2025: 465, 2030: 393, 2035: 205},
    'PJM / Commonwealth Edison (US)': {2025: 126, 2030: 119, 2035: 53},
    'NPCC / New England (US)':        {2025: 194, 2030: 72,  2035: 68},
    'NPCC / Upstate New York (US)':   {2025: 96,  2030: 69,  2035: 52},
    'Midcontinent / Central (US)':    {2025: 600, 2030: 465, 2035: 164}
}


# ============================================================
# Font sizes
# ============================================================

FONT_SIZE_TITLE = 26
FONT_SIZE_LABEL = 26
FONT_SIZE_TICK = 24
FONT_SIZE_ANNOTATION = 20


# ============================================================
# Create figure
# ============================================================

fig = plt.figure(figsize=(20, 12))


# ============================================================
# LEFT PANEL
# ============================================================

ax_left = plt.subplot(1, 2, 1)


# --- Break-even boundary ---
ax_left.plot(
    a_range_log,
    b_critical_g,
    color=COLOR_CHARCOAL,
    linewidth=2.7,
    linestyle='-',
    label='Leakage-displacement balance',
    zorder=5
)


# --- Electricity displacement dominates (PINK) ---
ax_left.fill_between(
    a_range_log,
    b_critical_g,
    2000,
    alpha=0.58,
    color=COLOR_DISPLACEMENT_DOMINATES,
    label='Displacement credit > leakage penalty',
    zorder=0
)


# --- Methane leakage dominates (GREY) ---
ax_left.fill_between(
    a_range_log,
    1,
    b_critical_g,
    alpha=0.58,
    color=COLOR_LEAKAGE_DOMINATES,
    label='Leakage penalty > displacement credit',
    zorder=0
)


# --- Axis scales ---
ax_left.set_xscale('log')
ax_left.set_yscale('linear')

# --- Axis ranges ---
ax_left.set_xlim(0.01, 71)
ax_left.set_ylim(1, 800)

# --- Axis labels ---
ax_left.set_xlabel(
    r'Methane leakage rate (%)',
    fontsize=FONT_SIZE_LABEL
)

ax_left.set_ylabel(
    r'Grid carbon intensity (g CO$_2$e/kWh)',
    fontsize=FONT_SIZE_LABEL
)


# --- X ticks ---
x_ticks = [0.01, 0.02, 0.05,
           0.1, 0.2, 0.5,
           1, 2, 5,
           10, 20, 50, 70]

x_labels = ['0.01', '0.02', '0.05',
            '0.1', '0.2', '0.5',
            '1.0', '2.0', '5.0',
            '10', '20', '50', '70']

ax_left.set_xticks(x_ticks)
ax_left.set_xticklabels(x_labels, fontsize=FONT_SIZE_TICK, rotation=45)


# --- Y ticks ---
y_ticks = [0, 50, 100, 150,
           200, 250, 300, 350,
           400, 450, 500, 550,
           600, 650, 700, 750, 800]

y_labels = ['0', '50', '100', '150',
            '200', '250', '300', '350',
            '400', '450', '500', '550',
            '600', '650', '700', '750', '800']

ax_left.set_yticks(y_ticks)
ax_left.set_yticklabels(y_labels, fontsize=FONT_SIZE_TICK)


# --- 2% reference line ---
ax_left.axvline(
    x=2,
    color=COLOR_CHARCOAL,
    linestyle='--',
    linewidth=1.3,
    alpha=0.85,
    zorder=4
)


# --- Legend ---
ax_left.legend(
    loc='upper left',
    fontsize=FONT_SIZE_ANNOTATION,
    framealpha=0.92,
    facecolor='white',
    edgecolor='#D0D0D0'
)


# ============================================================
# RIGHT PANEL
# ============================================================

ax_right = plt.subplot(1, 2, 2, sharey=ax_left)


# --- Electricity displacement dominates (PINK) ---
ax_right.fill_between(
    [2024, 2036],
    BOUNDARY_2PCT,    # [FIX] was 166
    800,
    alpha=0.58,
    color=COLOR_DISPLACEMENT_DOMINATES,
    zorder=0
)


# --- Methane leakage dominates (GREY) ---
ax_right.fill_between(
    [2024, 2036],
    1,
    BOUNDARY_2PCT,    # [FIX] was 166
    alpha=0.58,
    color=COLOR_LEAKAGE_DOMINATES,
    zorder=0
)


# ============================================================
# Regional trajectories
# ============================================================

for region in regions:

    region_data = data_raw[region]

    valid_years = [y for y in years if region_data[y] is not None]
    valid_values = [region_data[y] for y in valid_years]

    if valid_years:

        ax_right.plot(
            valid_years,
            valid_values,
            marker='o',
            markersize=7,
            markeredgecolor='white',
            markeredgewidth=0.8,
            linewidth=2.6,
            color=region_colors[region],
            zorder=5
        )

        if 2025 in valid_years:

            idx_2025 = valid_years.index(2025)

            x_pos = valid_years[idx_2025]
            y_pos = valid_values[idx_2025]

            # ------------------------------------------------
            # Default offsets
            # ------------------------------------------------
            horizontal_offset = 0.5
            vertical_offset = 0

            # ------------------------------------------------
            # Manual adjustments
            # ------------------------------------------------
            if region == 'Ontario (Canada)':
                horizontal_offset = 2.2
                vertical_offset = -10

            elif region == 'Sweden':
                vertical_offset = -8
            elif region == 'Germany':
                horizontal_offset = 2.2

            elif region == 'France':
                horizontal_offset = 2.2
                vertical_offset = 12

            elif region == 'Denmark':
                vertical_offset = -8

            elif region == 'North (China)':
                vertical_offset = -10

            elif region == 'South (China)':
                vertical_offset = 20

            elif region == 'US average':
                vertical_offset = 40

            elif region == 'PJM / West (US)':
                vertical_offset = 10

            elif region == 'Midcontinent / Central (US)':
                vertical_offset = -10

            # ------------------------------------------------
            # Annotation
            # ------------------------------------------------
            ax_right.annotate(
                region,
                xy=(x_pos, y_pos),
                xytext=(
                    x_pos + horizontal_offset,
                    y_pos + vertical_offset
                ),
                fontsize=FONT_SIZE_ANNOTATION,
                color=region_colors[region],
                weight='bold',
                alpha=1.0,
                bbox=dict(
                    boxstyle='round,pad=0.20',
                    facecolor='white',
                    alpha=0.88,
                    edgecolor='none'
                ),
                arrowprops=dict(
                    arrowstyle='-',
                    color=region_colors[region],
                    alpha=0.80,
                    lw=0.9
                ),
                zorder=10
            )


# --- Right-panel X axis ---
ax_right.set_xlabel('Year', fontsize=FONT_SIZE_LABEL)
ax_right.set_xlim(2024, 2036)
ax_right.set_xticks(years)
ax_right.set_xticklabels(['2025', '2030', '2035'], fontsize=FONT_SIZE_TICK)


# --- Right-panel Y axis ---
ax_right.set_ylim(1, 800)
ax_right.set_yscale('linear')
ax_right.set_yticks(y_ticks)
ax_right.set_yticklabels(y_labels, fontsize=FONT_SIZE_TICK)


# --- 2% leakage boundary ---
ax_right.axhline(
    y=BOUNDARY_2PCT,   # [FIX] was 166
    color=COLOR_CHARCOAL,
    linestyle='--',
    linewidth=1.3,
    alpha=0.85,
    zorder=4
)


# --- Grid ---
ax_right.grid(
    True,
    linestyle='--',
    alpha=0.22,
    color='#BFBFBF',
    axis='y',
    zorder=1
)


# ============================================================
# Spine styling
# ============================================================

for ax in [ax_left, ax_right]:

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.spines['left'].set_color('#555555')
    ax.spines['bottom'].set_color('#555555')

    ax.spines['left'].set_linewidth(1.0)
    ax.spines['bottom'].set_linewidth(1.0)

    ax.tick_params(axis='both', colors='#333333')


# ============================================================
# Layout
# ============================================================

plt.tight_layout()
plt.show()


# ============================================================
# Output summary
# ============================================================

print("=" * 80)
print("右侧子图数据汇总 (Grid Carbon Intensity, 单位: g CO₂e/kWh)")
print("=" * 80)

df_display = pd.DataFrame(index=regions, columns=years)

for region in regions:
    for year in years:
        val = data_raw[region].get(year)
        df_display.loc[region, year] = val if val is not None else 'N/A'

print(df_display.to_string())


# ============================================================
# Interpretation
# ============================================================

print("\n" + "=" * 80)
print("解读说明")
print("=" * 80)

print(f"""
使用方法:

1. 在右侧图中找到某地区某年份的碳强度值 (Y 轴)

2. 在左侧图中找到该 Y 值对应的临界泄漏率 (X 轴)

3. 比较实际泄漏率与临界泄漏率:

   - 若实际泄漏率 < 临界泄漏率
     → 电力替代所避免的排放大于甲烷泄漏排放（仅限本模型边界）

   - 若实际泄漏率 > 临界泄漏率
     → 甲烷泄漏排放大于电力替代所避免的排放（仅限本模型边界）

参数约定 (纯甲烷, 25°C, 1 atm):
   ρ_CH4  = {d_CH4} kg/m³
   CV_CH4 = {CALORIFIC_VALUE_CH4} MJ/m³ (LHV)
   GWP    = {GWP_CH4} (AR5, 100-yr)
   η_ele  = {eta_ele}
   2% 泄漏对应的临界碳强度 = {BOUNDARY_2PCT:.1f} g CO₂e/kWh
""")


# ============================================================
# Critical leakage reference values
# ============================================================

print("\n" + "=" * 80)
print("关键泄漏率对应的临界电网碳强度参考值")
print("=" * 80)

for a_ref in [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10]:
    print(f"泄漏率 {a_ref}% → 临界碳强度 = {critical_b_g(a_ref):.2f} g CO₂e/kWh")