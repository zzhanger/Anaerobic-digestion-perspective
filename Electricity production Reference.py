"""Figure 3a reference curve and Table S2 OAT sensitivity, both using Table S1.
Run this file before Energy recovery potentials.py.
Outputs are written beside this script.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
BOD5_VALUES = np.arange(100, 551, 10)
BOD5_SENSITIVITY = 100.0  # Table S2: 100 mg/L, NOT 300 mg/L

# Exact Table S1 reference assumptions.
# Units: LHV kWh/m3 CH4; biogas m3/kg VS destroyed.
REFERENCE = {
    'TSS_BOD_ratio': 0.94,
    'eta_primary_BOD': 0.30,
    'eta_primary_TSS': 0.60,
    'VS_ratio_primary': 0.75,
    'eta_CAS_BOD': 0.90,
    'Y_WAS': 0.45,
    'eta_VS_primary': 0.55,
    'eta_VS_WAS': 0.35,
    'Y_biogas': 0.85,
    'CH4_fraction': 0.65,
    'CV_CH4': 9.97,
    'eta_elec': 0.35,
}

# Only parameters with a low/high range in Table S1 are varied in Table S2.
# CH4 low == reference (0.65) as stated in Table S1: low case has zero effect.
SENSITIVITY = {
    'TSS/BOD$_5$ ratio': ('TSS_BOD_ratio', 0.80, 1.10),
    'Primary TSS capture': ('eta_primary_TSS', 0.50, 0.70),
    'Primary sludge VS/TSS': ('VS_ratio_primary', 0.65, 0.80),
    'Observed WAS yield': ('Y_WAS', 0.35, 0.55),
    'Primary sludge VS destruction': ('eta_VS_primary', 0.45, 0.65),
    'WAS VS destruction': ('eta_VS_WAS', 0.25, 0.45),
    'Biogas yield': ('Y_biogas', 0.75, 1.12),
    'CH$_4$ fraction': ('CH4_fraction', 0.65, 0.70),
    'CHP electrical efficiency': ('eta_elec', 0.30, 0.40),
}


def calculate_electricity(BOD5, **overrides):
    p = REFERENCE.copy()
    unknown = set(overrides) - set(p)
    if unknown:
        raise ValueError(f'Unknown parameters: {sorted(unknown)}')
    p.update(overrides)
    bod = float(BOD5) / 1000.0  # mg/L -> kg/m3
    tss_in = bod * p['TSS_BOD_ratio']
    vs_primary = tss_in * p['eta_primary_TSS'] * p['VS_ratio_primary']
    bod_removed_primary = bod * p['eta_primary_BOD']
    bod_removed_CAS = (bod - bod_removed_primary) * p['eta_CAS_BOD']
    vs_secondary = bod_removed_CAS * p['Y_WAS']  # VSS ~= VS for WAS
    vs_destroyed_primary = vs_primary * p['eta_VS_primary']
    vs_destroyed_WAS = vs_secondary * p['eta_VS_WAS']
    vs_destroyed = vs_destroyed_primary + vs_destroyed_WAS
    biogas = vs_destroyed * p['Y_biogas']
    methane = biogas * p['CH4_fraction']
    electricity = methane * p['CV_CH4'] * p['eta_elec']
    return {
        'BOD5_mg_L': float(BOD5),
        'TSS_influent_kg_m3': tss_in,
        'VS_primary_kg_m3': vs_primary,
        'VS_secondary_kg_m3': vs_secondary,
        'VS_total_kg_m3': vs_primary + vs_secondary,
        'VS_destroyed_primary_kg_m3': vs_destroyed_primary,
        'VS_destroyed_WAS_kg_m3': vs_destroyed_WAS,
        'VS_destroyed_kg_m3': vs_destroyed,
        'Biogas_m3_m3': biogas,
        'CH4_m3_m3': methane,
        'Electricity_kWh_m3': electricity,
    }


def build_reference_table():
    """Figure 3a reference curve."""
    reference_df = pd.DataFrame(
        [calculate_electricity(b) for b in BOD5_VALUES]
    )
    reference_df.to_csv(
        OUT / 'Electricity recovery potential reference line.csv',
        index=False,
    )
    return reference_df


def build_sensitivity_table():
    """Table S2 OAT sensitivity at BOD5 = 100 mg/L."""
    base = calculate_electricity(BOD5_SENSITIVITY)['Electricity_kWh_m3']
    records = []
    for name, (variable, low, high) in SENSITIVITY.items():
        for case, value in [
            ('low', low),
            ('base', REFERENCE[variable]),
            ('high', high),
        ]:
            e = calculate_electricity(
                BOD5_SENSITIVITY, **{variable: value}
            )['Electricity_kWh_m3']
            records.append({
                'Parameter': name,
                'Variable': variable,
                'Case': case,
                'Parameter_value': value,
                'Electricity_kWh_m3': e,
                'Change_from_base_pct': (e / base - 1) * 100,
            })
    sensitivity_df = pd.DataFrame(records)
    sensitivity_df.to_csv(
        OUT / 'Electricity recovery sensitivity Table S2.csv',
        index=False,
    )
    return base, sensitivity_df


def build_tornado_table(base, sensitivity_df):
    """Collapse sensitivity results into a tornado table."""
    tornado = []
    for name, (variable, low, high) in SENSITIVITY.items():
        rows = (
            sensitivity_df[sensitivity_df['Parameter'] == name]
            .set_index('Case')
        )
        low_pct = float(rows.loc['low', 'Change_from_base_pct'])
        high_pct = float(rows.loc['high', 'Change_from_base_pct'])
        tornado.append({
            'Parameter': name,
            'Base_value': REFERENCE[variable],
            'Low_value': low,
            'High_value': high,
            'Low_electricity_kWh_m3': float(rows.loc['low', 'Electricity_kWh_m3']),
            'Base_electricity_kWh_m3': base,
            'High_electricity_kWh_m3': float(rows.loc['high', 'Electricity_kWh_m3']),
            'Low_change_pct': low_pct,
            'High_change_pct': high_pct,
            'Sensitivity_span_pct': high_pct - low_pct,
            'Sensitivity_magnitude': max(abs(low_pct), abs(high_pct)),
        })
    tornado_df = pd.DataFrame(tornado).sort_values(
        'Sensitivity_magnitude', ascending=True
    )
    tornado_df.to_csv(OUT / 'Electricity recovery tornado data.csv', index=False)
    return tornado_df


def plot_tornado(tornado_df):
    """Tornado plot. Bars are drawn from 0 to the signed change."""
    fig, ax = plt.subplots(figsize=(12, 7))
    y = np.arange(len(tornado_df))

    # [FIX] Low bar goes from Low_change_pct back to 0:
    #        width = -Low_change_pct, left = Low_change_pct.
    #        This is correct regardless of sign (Low and High may share a sign).
    low = tornado_df['Low_change_pct'].to_numpy()
    high = tornado_df['High_change_pct'].to_numpy()

    ax.barh(y, -low, left=low, height=0.55, label='Low', color='#B0C4DE')
    ax.barh(y,  high, left=0.0, height=0.55, label='High', color='#6B8E23')

    ax.axvline(0, color='#333333', linewidth=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels(tornado_df['Parameter'], fontsize=13)
    ax.set_xlabel('Change in electricity recovery potential (%)', fontsize=15)
    ax.set_title(
        f'Parameter sensitivity at influent BOD$_5$ = '
        f'{BOD5_SENSITIVITY:g} mg L$^{{-1}}$'
    )
    ax.legend(frameon=False, loc='lower right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', linestyle=':', linewidth=0.7, alpha=0.3)
    plt.tight_layout()

    # [ADD] Save figure beside script so it can be reused in the manuscript.
    fig.savefig(OUT / 'Electricity recovery tornado.png', dpi=300,
                bbox_inches='tight')
    plt.close(fig)


def main():
    reference_df = build_reference_table()
    base, sensitivity_df = build_sensitivity_table()
    tornado_df = build_tornado_table(base, sensitivity_df)

    print(f'Figure 3a: 100 mg/L = '
          f'{calculate_electricity(100)["Electricity_kWh_m3"]:.6f} kWh/m3')
    print(f'Figure 3a: 500 mg/L = '
          f'{calculate_electricity(500)["Electricity_kWh_m3"]:.6f} kWh/m3')
    print(f'Table S2 baseline at {BOD5_SENSITIVITY:g} mg/L = '
          f'{base:.6f} kWh/m3')
    print(
        tornado_df[['Parameter', 'Low_change_pct', 'High_change_pct']]
        .to_string(index=False)
    )

    plot_tornado(tornado_df)
    print(f'\nOutputs written to: {OUT}')


# [FIX] Previously main() was never called, so no CSV/figure was produced.
if __name__ == '__main__':
    main()