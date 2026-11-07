# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 09:43:33 2026

@author: zz1405
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# ========== Font settings ==========
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

# ========== Categories ==========
categories = [
    'Carbon diversion',
    'Digestion optimization',
    'Co-digestion',
    'Demand reduction',
    'Energy system integration'
]

# ========== Binary classification (YES / NO) ==========
facility_data = [
    {
        'Facility': 'Point Loma',
        'Categories': [
            'Carbon diversion',
            'Demand reduction',
            'Energy system integration'
        ]
    },

    {
        'Facility': 'Sheboygan',
        'Categories': [
            'Digestion optimization',
            'Co-digestion',
            'Demand reduction',
            'Energy system integration'
        ]
    },

    {
        'Facility': 'East Bay MUD',
        'Categories': [
            'Digestion optimization',
            'Co-digestion',
            'Demand reduction',
            'Energy system integration'
        ]
    },

    {
        'Facility': 'Strass im Zillertal',
        'Categories': [
            'Carbon diversion',
            'Digestion optimization',
            'Co-digestion',
            'Demand reduction',
            'Energy system integration'
        ]
    },

    {
        'Facility': 'Marselisborg',
        'Categories': [
            'Carbon diversion',
            'Digestion optimization',
            'Demand reduction',
            'Energy system integration'
        ]
    },

    {
        'Facility': 'Ejby Mølle',
        'Categories': [
            'Carbon diversion',
            'Digestion optimization',
            'Demand reduction',
            'Energy system integration'
        ]
    },

    {
        'Facility': 'Grevesmühlen',
        'Categories': [
            'Digestion optimization',
            'Demand reduction',
            'Energy system integration'
        ]
    }
]

# ========== Build matrix ==========
facility_names = []
matrix = []

for f in facility_data:
    facility_names.append(f['Facility'])
    row = [cat in f['Categories'] for cat in categories]
    matrix.append(row)

df = pd.DataFrame(
    matrix,
    index=facility_names,
    columns=categories
)

# ============================================================
# Manuscript color palette
# ============================================================

COLOR_PINK = '#E7B4C5'
COLOR_GREEN = '#9ACBAA'
COLOR_TERRACOTTA = '#BC825F'
COLOR_BLUE = '#81B8DC'
COLOR_COOL_GREY = '#AEB9BE'

# Category mapping
colors = {
    'Carbon diversion': COLOR_PINK,
    'Digestion optimization': COLOR_GREEN,
    'Co-digestion': COLOR_TERRACOTTA,
    'Demand reduction': COLOR_BLUE,
    'Energy system integration': COLOR_COOL_GREY
}

# ========== Plot ==========
fig, ax = plt.subplots(
    figsize=(10, 12)
)

y_pos = np.arange(
    len(facility_names)
)

circle_radius = 0.2

# ========== Draw circles ==========
for i, (facility, row) in enumerate(df.iterrows()):

    for j, (category, has_strategy) in enumerate(row.items()):

        x = j * 1.4
        y = i

        if has_strategy:

            circle = Circle(
                (x, y),
                circle_radius,
                facecolor=colors[category],
                edgecolor='#555555',
                linewidth=1.0
            )

        else:

            circle = Circle(
                (x, y),
                circle_radius,
                facecolor='white',
                edgecolor='#777777',
                linewidth=1.2
            )

        ax.add_patch(circle)

# ========== Axis ==========
ax.set_yticks(
    y_pos
)

ax.set_yticklabels(
    facility_names,
    fontsize=22
)

ax.set_xticks(
    [
        i * 1.4
        for i in range(len(categories))
    ]
)

ax.set_xticklabels(
    categories,
    rotation=30,
    ha='right',
    fontsize=22
)

ax.set_xlim(
    -0.8,
    (len(categories) - 1) * 1.4 + 0.8
)

ax.set_ylim(
    -0.8,
    len(facility_names) - 0.2
)

ax.set_aspect(
    'equal'
)

# ========== Clean spines ==========
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)

ax.spines['left'].set_color(
    '#555555'
)

ax.tick_params(
    axis='x',
    length=0
)

ax.tick_params(
    axis='y',
    length=0
)

# ========== Grid lines ==========
for i in range(len(facility_names)):

    ax.axhline(
        y=i - 0.5,
        color='#E0E0E0',
        linewidth=0.8,
        zorder=0
    )

# ========== Layout ==========
plt.tight_layout()

plt.show()