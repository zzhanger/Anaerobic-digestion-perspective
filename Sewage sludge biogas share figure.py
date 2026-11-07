# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 11:04:19 2026

@author: zz1405
"""


import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ========== 设置字体 ==========
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.grid'] = False

# Read data
df = pd.read_csv('Sewage sludge biogas share and upgrade figure.csv')

# Check required columns exist
required_cols = [
    'Country',
    'Number of WWTP (secondary and above)',
    'AD adoption rate',
    'Sewage sludge biogas share (%)',
    'Biogas upgrade rate (%)',
    'Biogas for power, heat, and other uses',
    'Biogas wasted'
]

for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in the CSV file.")

# Clean data
df_clean = df[required_cols].dropna().copy()

for col in required_cols:
    if col != 'Country':
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

df_clean = df_clean.dropna()

# Sort by AD adoption rate
df_sorted_a = (
    df_clean
    .sort_values('AD adoption rate', ascending=False)
    .reset_index(drop=True)
)

countries_all = df_sorted_a['Country'].tolist()
n_countries = len(df_sorted_a)

# ========== Color palette matched to Figure 4 ==========
color_ad = '#D3CBC8'        # warm grey/taupe
color_sludge = '#9ACBAA'    # green
color_upgrade = '#81B8DC'   # blue
color_chp = '#E7B4C5'       # pink
color_wasted = '#AEB5B8'    # neutral grey

# ========== 创建三个子图 ==========
fig, (ax_left, ax_mid, ax_right) = plt.subplots(
    1, 3,
    figsize=(30, 20)
)

# ========== Panel a - AD adoption rate ==========
y_positions = np.arange(n_countries)
bar_height = 0.7

ad_rates = df_sorted_a['AD adoption rate'].values

ax_left.barh(
    y_positions,
    ad_rates,
    height=bar_height,
    color=color_ad,
    alpha=0.95,
    linewidth=0,
    zorder=2
)

# 添加数字标注
for i, (idx, row) in enumerate(df_sorted_a.iterrows()):

    ad_rate = row['AD adoption rate']
    wwtp_count = row['Number of WWTP (secondary and above)']

    if ad_rate > 10:
        ax_left.text(
            ad_rate / 2,
            i,
            f'{ad_rate:.0f}%',
            ha='center',
            va='center',
            fontsize=32,
            fontweight='bold',
            color='#333333'
        )

    ax_left.text(
        ad_rate + (max(ad_rates) * 0.02),
        i,
        f'({wwtp_count:,})',
        ha='left',
        va='center',
        fontsize=28,
        color='#555555'
    )

ax_left.set_xlabel(
    'Major WWTPs with AD (%)',
    fontsize=32
)

ax_left.tick_params(
    axis='x',
    labelsize=28
)

ax_left.set_xlim(
    0,
    max(ad_rates) * 1.3
)

ax_left.set_yticks(y_positions)

ax_left.set_yticklabels(
    countries_all,
    fontsize=32
)

ax_left.set_ylim(
    -0.5,
    n_countries - 0.5
)

ax_left.invert_yaxis()

# ========== Panel b - Sludge biogas share ==========
biogas_shares = []

for country in countries_all:

    val = df_sorted_a[
        df_sorted_a['Country'] == country
    ]['Sewage sludge biogas share (%)'].values

    biogas_shares.append(
        val[0] if len(val) > 0 else np.nan
    )

ax_mid.barh(
    y_positions,
    biogas_shares,
    color=color_sludge,
    height=0.7,
    linewidth=0.5,
    edgecolor='white',
    alpha=0.95
)

for i, share in enumerate(biogas_shares):

    if not np.isnan(share) and share > 10:

        ax_mid.text(
            share / 2,
            i,
            f'{share:.0f}%',
            ha='center',
            va='center',
            fontsize=32,
            fontweight='bold',
            color='#163A25'
        )

ax_mid.set_xlabel(
    'Share of national biogas production\n'
    'derived from sewage sludge (%)',
    fontsize=32,
    labelpad=20
)

ax_mid.set_ylabel('')
ax_mid.set_yticklabels([])

ax_mid.set_ylim(
    -0.5,
    n_countries - 0.5
)

ax_mid.invert_yaxis()

ax_mid.tick_params(
    axis='x',
    labelsize=28
)

max_share = max(
    [s for s in biogas_shares if not np.isnan(s)],
    default=0
)

ax_mid.set_xlim(
    0,
    max_share * 1.3 if max_share > 0 else 100
)

# ========== Panel c - Utilization pathways ==========
upgrade_vals = []
chp_vals = []
flared_vals = []

for country in countries_all:

    row = df_sorted_a[
        df_sorted_a['Country'] == country
    ]

    if len(row) > 0:

        upgrade_vals.append(
            row['Biogas upgrade rate (%)'].values[0]
        )

        chp_vals.append(
            row['Biogas for power, heat, and other uses'].values[0]
        )

        flared_vals.append(
            row['Biogas wasted'].values[0]
        )

    else:
        upgrade_vals.append(np.nan)
        chp_vals.append(np.nan)
        flared_vals.append(np.nan)

upgrade_vals_plot = [
    0 if np.isnan(x) else x
    for x in upgrade_vals
]

chp_vals_plot = [
    0 if np.isnan(x) else x
    for x in chp_vals
]

flared_vals_plot = [
    0 if np.isnan(x) else x
    for x in flared_vals
]

bars_upgrade = ax_right.barh(
    y_positions,
    upgrade_vals_plot,
    height=0.7,
    color=color_upgrade,
    label='Biomethane upgrading',
    linewidth=0.5,
    edgecolor='white'
)

bars_chp = ax_right.barh(
    y_positions,
    chp_vals_plot,
    height=0.7,
    left=upgrade_vals_plot,
    color=color_chp,
    label='Heat and power',
    linewidth=0.5,
    edgecolor='white'
)

bars_flared = ax_right.barh(
    y_positions,
    flared_vals_plot,
    height=0.7,
    left=[
        u + c
        for u, c in zip(
            upgrade_vals_plot,
            chp_vals_plot
        )
    ],
    color=color_wasted,
    label='Unused',
    linewidth=0.5,
    edgecolor='white'
)

# 添加数字标注
for i in range(n_countries):

    has_data = not (
        np.isnan(upgrade_vals[i])
        and np.isnan(chp_vals[i])
        and np.isnan(flared_vals[i])
    )

    has_any_value = (
        upgrade_vals_plot[i] > 0
        or chp_vals_plot[i] > 0
        or flared_vals_plot[i] > 0
    )

    if not has_data or not has_any_value:

        ax_right.text(
            50,
            i,
            'No data',
            ha='right',
            va='center',
            fontsize=28,
            color='#999999',
            fontweight='bold'
        )

    else:

        if (
            not np.isnan(upgrade_vals[i])
            and upgrade_vals_plot[i] > 10
        ):
            ax_right.text(
                upgrade_vals_plot[i] / 2,
                i,
                f'{upgrade_vals_plot[i]:.0f}%',
                ha='center',
                va='center',
                fontsize=32,
                color='#173F59',
                fontweight='bold'
            )

        if (
            not np.isnan(chp_vals[i])
            and chp_vals_plot[i] > 10
        ):
            ax_right.text(
                upgrade_vals_plot[i]
                + chp_vals_plot[i] / 2,
                i,
                f'{chp_vals_plot[i]:.0f}%',
                ha='center',
                va='center',
                fontsize=32,
                color='#5A2740',
                fontweight='bold'
            )

        if (
            not np.isnan(flared_vals[i])
            and flared_vals_plot[i] > 10
        ):
            ax_right.text(
                upgrade_vals_plot[i]
                + chp_vals_plot[i]
                + flared_vals_plot[i] / 2,
                i,
                f'{flared_vals_plot[i]:.0f}%',
                ha='center',
                va='center',
                fontsize=32,
                color='#333333',
                fontweight='bold'
            )

ax_right.set_xlabel(
    'Primary biogas utilization pathways (%)',
    fontsize=32,
    labelpad=15
)

ax_right.set_ylabel('')
ax_right.set_yticks(y_positions)
ax_right.set_yticklabels([])

ax_right.set_ylim(
    -0.5,
    n_countries - 0.5
)

ax_right.invert_yaxis()

ax_right.set_xlim(
    0,
    105
)

ax_right.tick_params(
    axis='x',
    labelsize=28
)

ax_right.legend(
    loc='lower center',
    bbox_to_anchor=(0.5, 1.02),
    ncol=3,
    fontsize=32,
    frameon=False
)

# ========== 调整布局 ==========
plt.tight_layout()

plt.subplots_adjust(
    wspace=0.08,
    top=0.94,
    bottom=0.12,
    left=0.08,
    right=0.95
)

plt.show()