# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 11:29:07 2026

@author: zz1405
"""

# -*- coding: utf-8 -*-
"""
AD+CHP vs AD+RNG Economic Model
with Policy Scenario and Sensitivity Analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# GLOBAL PLOT SETTINGS
# =============================================================================

plt.rcParams.update({
    'font.size': 16,
    'axes.labelsize': 18,
    'axes.titlesize': 20,
    'xtick.labelsize': 15,
    'ytick.labelsize': 15,
    'legend.fontsize': 14,
})


# =============================================================================
# LITERATURE-DERIVED REFERENCE DATA
# =============================================================================
# These values are treated as calibration/reference values and are NOT varied
# in the sensitivity analysis.

class LiteratureData:

    # Reference scale
    WCE = 1600
    VS_kg_per_day = 10858

    # CAPEX (USD)
    CAPEX_AD = 1879000
    CAPEX_RNG = 3266745
    CAPEX_CHP = 1880565

    # Annual OPEX (USD/year)
    OPEX_AD = 162766
    OPEX_RNG = 147086
    OPEX_CHP = 112500

    # Environmental/compliance costs (USD/year)
    ENV_CREDIT_RNG = 47000
    ENV_CREDIT_CHP = 6000

    # Financial assumptions
    PROJECT_LIFE = 20
    DISCOUNT_RATE = 0.07


# =============================================================================
# BASELINE TECHNICAL PARAMETERS
# =============================================================================

VS_DESTRUCTION = 0.55
CH4_YIELD = 0.51               # m3 CH4/kg VS destroyed
AVAILABILITY = 0.92
CH4_LHV = 9.97                 # kWh/m3 CH4
CH4_ELEC_EFF = 0.38
RNG_RECOVERY = 0.96
SCALING_EXPONENT = 0.80

# Wastewater-to-solids conversion assumptions
VS_PER_CAPITA = 0.08           # kg VS/person/day
FLOW_PER_CAPITA_GPD = 100      # gal/person/day


# =============================================================================
# CONVERSION FUNCTIONS
# =============================================================================

def vs_to_mgd(
    vs_kg_per_day,
    vs_per_capita=VS_PER_CAPITA,
    flow_per_capita_gpd=FLOW_PER_CAPITA_GPD
):

    population = vs_kg_per_day / vs_per_capita

    mgd = (
        population
        * flow_per_capita_gpd
        / 1_000_000
    )

    return mgd


def mgd_to_vs(
    mgd,
    vs_per_capita=VS_PER_CAPITA,
    flow_per_capita_gpd=FLOW_PER_CAPITA_GPD
):

    population = (
        mgd
        * 1_000_000
        / flow_per_capita_gpd
    )

    vs = population * vs_per_capita

    return vs


# =============================================================================
# POLICY SCENARIOS
# =============================================================================

class SubsidyScenarios:

    # -------------------------------------------------------------------------
    # AD + CHP
    # -------------------------------------------------------------------------

    CHP_SCENARIOS = {

        "No subsidies": {
            "capex_grant": 0.00,
            "prod_credit_usd_per_kwh": 0.00,
            "description": "No subsidies"
        },

        "ITC 30% grant": {
            "capex_grant": 0.30,
            "prod_credit_usd_per_kwh": 0.00,
            "description": "30% ITC"
        },

        "PTC 27 USD/MWh": {
            "capex_grant": 0.00,
            "prod_credit_usd_per_kwh": 0.027,
            "description": "$27/MWh PTC"
        },

        "REC 30 USD/MWh": {
            "capex_grant": 0.00,
            "prod_credit_usd_per_kwh": 0.030,
            "description": "$30/MWh REC"
        },
    }

    # -------------------------------------------------------------------------
    # AD + RNG
    # -------------------------------------------------------------------------

    RNG_SCENARIOS = {

        "No subsidies": {
            "capex_grant": 0.00,
            "prod_credit_usd_per_m3": 0.00,
            "description": "No subsidies"
        },

        "ITC 30% grant": {
            "capex_grant": 0.30,
            "prod_credit_usd_per_m3": 0.00,
            "description": "30% ITC"
        },

        "RIN 3 USD/credit": {
            "capex_grant": 0.00,
            "prod_credit_usd_per_m3": 0.85,
            "description": "D3 RIN ($0.85/m3)"
        },

        "LCFS 90 USD/tCO2e": {
            "capex_grant": 0.00,
            "prod_credit_usd_per_m3": 0.35,
            "description": "LCFS ($0.35/m3)"
        },
    }


# =============================================================================
# PRODUCTION CALCULATION
# =============================================================================

def calc_production(
    vs_kg_per_day,
    vs_destruction=VS_DESTRUCTION,
    ch4_yield=CH4_YIELD,
    availability=AVAILABILITY
):

    vs_destroyed = (
        vs_kg_per_day
        * vs_destruction
    )

    ch4_per_year = (
        vs_destroyed
        * ch4_yield
        * 365
        * availability
    )

    energy_kwh_per_year = (
        ch4_per_year
        * CH4_LHV
    )

    return {

        'ch4_m3_per_year':
            ch4_per_year,

        'energy_kwh_per_year':
            energy_kwh_per_year,

        'vs_destroyed_kg_per_day':
            vs_destroyed
    }


# =============================================================================
# CAPITAL RECOVERY FACTOR
# =============================================================================

def get_crf(
    discount_rate=None,
    project_life=None
):

    if discount_rate is None:
        discount_rate = LiteratureData.DISCOUNT_RATE

    if project_life is None:
        project_life = LiteratureData.PROJECT_LIFE

    r = discount_rate
    n = project_life

    return (
        r * (1 + r) ** n
        / ((1 + r) ** n - 1)
    )


# =============================================================================
# CHP LCOE
# =============================================================================

def calc_lcoe_chp(
    vs_kg_per_day,
    subsidy_scenario,
    vs_destruction=VS_DESTRUCTION,
    ch4_yield=CH4_YIELD,
    availability=AVAILABILITY,
    chp_efficiency=CH4_ELEC_EFF,
    scaling_exponent=SCALING_EXPONENT,
    discount_rate=None,
    project_life=None
):

    prod = calc_production(
        vs_kg_per_day,
        vs_destruction,
        ch4_yield,
        availability
    )

    electricity_kwh = (
        prod['energy_kwh_per_year']
        * chp_efficiency
    )

    scale_factor = (
        vs_kg_per_day
        / LiteratureData.VS_kg_per_day
    ) ** scaling_exponent

    # -------------------------------------------------------------------------
    # CAPEX
    # -------------------------------------------------------------------------

    capex_ad = (
        LiteratureData.CAPEX_AD
        * scale_factor
    )

    capex_chp = (
        LiteratureData.CAPEX_CHP
        * scale_factor
    )

    capex_total = (
        capex_ad
        + capex_chp
    )

    capex_grant = subsidy_scenario.get(
        'capex_grant',
        0
    )

    capex_after_grant = (
        capex_total
        * (1 - capex_grant)
    )

    # -------------------------------------------------------------------------
    # OPEX
    # -------------------------------------------------------------------------

    opex_ad = (
        LiteratureData.OPEX_AD
        * scale_factor
    )

    opex_chp = (
        LiteratureData.OPEX_CHP
        * scale_factor
    )

    env_cost = (
        LiteratureData.ENV_CREDIT_CHP
    )

    opex_total = (
        opex_ad
        + opex_chp
        + env_cost
    )

    # -------------------------------------------------------------------------
    # Production credit
    # -------------------------------------------------------------------------

    prod_credit = subsidy_scenario.get(
        'prod_credit_usd_per_kwh',
        0
    )

    subsidy_revenue = (
        electricity_kwh
        * prod_credit
    )

    # -------------------------------------------------------------------------
    # Annualized cost
    # -------------------------------------------------------------------------

    annualized_capex = (
        capex_after_grant
        * get_crf(
            discount_rate,
            project_life
        )
    )

    annual_cost = (
        annualized_capex
        + opex_total
        - subsidy_revenue
    )

    lcoe = (
        annual_cost
        / electricity_kwh
        if electricity_kwh > 0
        else np.nan
    )

    return {

        'lcoe_usd_per_kwh':
            lcoe,

        'lcoe_cent_per_kwh':
            lcoe * 100,

        'electricity_mwh_per_year':
            electricity_kwh / 1000,

        'capex_total_usd':
            capex_total,

        'capex_total_after_grant_usd':
            capex_after_grant,

        'opex_total_usd':
            opex_total,

        'subsidy_revenue_usd_per_year':
            subsidy_revenue
    }


# =============================================================================
# RNG LEVELIZED COST
# =============================================================================

def calc_lcoe_rng(
    vs_kg_per_day,
    subsidy_scenario,
    vs_destruction=VS_DESTRUCTION,
    ch4_yield=CH4_YIELD,
    availability=AVAILABILITY,
    rng_recovery=RNG_RECOVERY,
    scaling_exponent=SCALING_EXPONENT,
    discount_rate=None,
    project_life=None
):

    prod = calc_production(
        vs_kg_per_day,
        vs_destruction,
        ch4_yield,
        availability
    )

    rng_m3_per_year = (
        prod['ch4_m3_per_year']
        * rng_recovery
    )

    scale_factor = (
        vs_kg_per_day
        / LiteratureData.VS_kg_per_day
    ) ** scaling_exponent

    # -------------------------------------------------------------------------
    # CAPEX
    # -------------------------------------------------------------------------

    capex_ad = (
        LiteratureData.CAPEX_AD
        * scale_factor
    )

    capex_rng = (
        LiteratureData.CAPEX_RNG
        * scale_factor
    )

    capex_total = (
        capex_ad
        + capex_rng
    )

    capex_grant = subsidy_scenario.get(
        'capex_grant',
        0
    )

    capex_after_grant = (
        capex_total
        * (1 - capex_grant)
    )

    # -------------------------------------------------------------------------
    # OPEX
    # -------------------------------------------------------------------------

    opex_ad = (
        LiteratureData.OPEX_AD
        * scale_factor
    )

    opex_rng = (
        LiteratureData.OPEX_RNG
        * scale_factor
    )

    env_cost = (
        LiteratureData.ENV_CREDIT_RNG
    )

    opex_total = (
        opex_ad
        + opex_rng
        + env_cost
    )

    # -------------------------------------------------------------------------
    # Production credit
    # -------------------------------------------------------------------------

    prod_credit = subsidy_scenario.get(
        'prod_credit_usd_per_m3',
        0
    )

    subsidy_revenue = (
        rng_m3_per_year
        * prod_credit
    )

    # -------------------------------------------------------------------------
    # Annualized cost
    # -------------------------------------------------------------------------

    annualized_capex = (
        capex_after_grant
        * get_crf(
            discount_rate,
            project_life
        )
    )

    annual_cost = (
        annualized_capex
        + opex_total
        - subsidy_revenue
    )

    levelized_cost = (
        annual_cost
        / rng_m3_per_year
        if rng_m3_per_year > 0
        else np.nan
    )

    return {

        'lcoe_usd_per_m3':
            levelized_cost,

        'rng_mm_m3_per_year':
            rng_m3_per_year / 1_000_000,

        'capex_total_usd':
            capex_total,

        'capex_total_after_grant_usd':
            capex_after_grant,

        'opex_total_usd':
            opex_total,

        'subsidy_revenue_usd_per_year':
            subsidy_revenue
    }


# =============================================================================
# MAIN POLICY / FACILITY-SCALE ANALYSIS
# =============================================================================

flow_scales_mgd = np.array([
    2,
    5,
    10,
    20,
    30,
    50,
    100,
    150,
    200
])

vs_scales = np.array([
    mgd_to_vs(mgd)
    for mgd in flow_scales_mgd
])


all_results = []


for vs, mgd in zip(
    vs_scales,
    flow_scales_mgd
):

    # -------------------------------------------------------------------------
    # CHP
    # -------------------------------------------------------------------------

    for (
        chp_name,
        chp_scenario
    ) in SubsidyScenarios.CHP_SCENARIOS.items():

        chp = calc_lcoe_chp(
            vs,
            chp_scenario
        )

        all_results.append({

            'Path':
                'CHP',

            'Scenario':
                chp_name,

            'Flow_MGD':
                mgd,

            'VS_ton_per_day':
                vs / 1000,

            'LCOE_cent_per_kWh':
                chp['lcoe_cent_per_kwh'],

            'Electricity_MWh_per_year':
                chp['electricity_mwh_per_year'],

            'CAPEX_MUSD':
                chp['capex_total_after_grant_usd']
                / 1_000_000,

            'OPEX_MUSD_per_year':
                chp['opex_total_usd']
                / 1_000_000,

            'Subsidy_Revenue_MUSD_per_year':
                chp['subsidy_revenue_usd_per_year']
                / 1_000_000,

            'RNG_LCOE_USD_per_m3':
                np.nan
        })


    # -------------------------------------------------------------------------
    # RNG
    # -------------------------------------------------------------------------

    for (
        rng_name,
        rng_scenario
    ) in SubsidyScenarios.RNG_SCENARIOS.items():

        rng = calc_lcoe_rng(
            vs,
            rng_scenario
        )

        all_results.append({

            'Path':
                'RNG',

            'Scenario':
                rng_name,

            'Flow_MGD':
                mgd,

            'VS_ton_per_day':
                vs / 1000,

            'LCOE_cent_per_kWh':
                np.nan,

            'Electricity_MWh_per_year':
                np.nan,

            'CAPEX_MUSD':
                np.nan,

            'OPEX_MUSD_per_year':
                np.nan,

            'Subsidy_Revenue_MUSD_per_year':
                np.nan,

            'RNG_LCOE_USD_per_m3':
                rng['lcoe_usd_per_m3'],

            'RNG_Output_MM_m3_per_year':
                rng['rng_mm_m3_per_year'],

            'RNG_CAPEX_MUSD':
                rng['capex_total_after_grant_usd']
                / 1_000_000,

            'RNG_OPEX_MUSD_per_year':
                rng['opex_total_usd']
                / 1_000_000,

            'RNG_Subsidy_Revenue_MUSD_per_year':
                rng['subsidy_revenue_usd_per_year']
                / 1_000_000
        })


df_results = pd.DataFrame(
    all_results
)

df_results.to_csv(
    'lcoe_results.csv',
    index=False
)


# =============================================================================
# SENSITIVITY ANALYSIS
# =============================================================================
#
# One-at-a-time (OAT) sensitivity analysis.
#
# Literature-derived CAPEX/OPEX reference values are held constant.
#
# Policy credits are excluded:
# sensitivity analysis is performed under the "No subsidies" scenario.
#
# Three representative facility scales:
# 10, 50, and 200 MGD.
# =============================================================================


# =============================================================================
# Sensitivity parameter ranges
# =============================================================================

SENSITIVITY_PARAMETERS = {

    'VS destruction': {
        'baseline': 0.55,
        'low': 0.44,
        'high': 0.66
    },

    'CH4 yield': {
        'baseline': 0.51,
        'low': 0.41,
        'high': 0.61
    },

    'Availability': {
        'baseline': 0.92,
        'low': 0.85,
        'high': 0.98
    },

    'CHP electrical efficiency': {
        'baseline': 0.38,
        'low': 0.30,
        'high': 0.45
    },

    'RNG methane recovery': {
        'baseline': 0.96,
        'low': 0.90,
        'high': 0.99
    },

    'Scaling exponent': {
        'baseline': 0.80,
        'low': 0.70,
        'high': 0.90
    },

    'Discount rate': {
        'baseline': 0.07,
        'low': 0.04,
        'high': 0.10
    },

    'Project life': {
        'baseline': 20,
        'low': 15,
        'high': 30
    },

    # Combined wastewater-strength / solids-loading parameter.
    #
    # Instead of varying VS/capita and flow/capita independently,
    # vary the VS loading associated with a given MGD by +/-20%.
    'VS loading per wastewater flow': {
        'baseline': 1.00,
        'low': 0.80,
        'high': 1.20
    }
}


# =============================================================================
# CHP sensitivity function
# =============================================================================

def run_chp_sensitivity(mgd):

    no_subsidy = (
        SubsidyScenarios
        .CHP_SCENARIOS['No subsidies']
    )

    baseline_vs = mgd_to_vs(mgd)

    baseline_result = calc_lcoe_chp(
        baseline_vs,
        no_subsidy
    )

    baseline_lcoe = (
        baseline_result[
            'lcoe_usd_per_kwh'
        ]
    )

    rows = []


    # -------------------------------------------------------------------------
    # VS destruction
    # -------------------------------------------------------------------------

    low = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        vs_destruction=
            SENSITIVITY_PARAMETERS[
                'VS destruction'
            ]['low']
    )['lcoe_usd_per_kwh']

    high = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        vs_destruction=
            SENSITIVITY_PARAMETERS[
                'VS destruction'
            ]['high']
    )['lcoe_usd_per_kwh']

    rows.append(
        ['VS destruction', low, high]
    )


    # -------------------------------------------------------------------------
    # CH4 yield
    # -------------------------------------------------------------------------

    low = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        ch4_yield=
            SENSITIVITY_PARAMETERS[
                'CH4 yield'
            ]['low']
    )['lcoe_usd_per_kwh']

    high = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        ch4_yield=
            SENSITIVITY_PARAMETERS[
                'CH4 yield'
            ]['high']
    )['lcoe_usd_per_kwh']

    rows.append(
        ['CH₄ yield', low, high]
    )


    # -------------------------------------------------------------------------
    # Availability
    # -------------------------------------------------------------------------

    low = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        availability=
            SENSITIVITY_PARAMETERS[
                'Availability'
            ]['low']
    )['lcoe_usd_per_kwh']

    high = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        availability=
            SENSITIVITY_PARAMETERS[
                'Availability'
            ]['high']
    )['lcoe_usd_per_kwh']

    rows.append(
        ['Availability', low, high]
    )


    # -------------------------------------------------------------------------
    # CHP electrical efficiency
    # -------------------------------------------------------------------------

    low = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        chp_efficiency=
            SENSITIVITY_PARAMETERS[
                'CHP electrical efficiency'
            ]['low']
    )['lcoe_usd_per_kwh']

    high = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        chp_efficiency=
            SENSITIVITY_PARAMETERS[
                'CHP electrical efficiency'
            ]['high']
    )['lcoe_usd_per_kwh']

    rows.append(
        ['CHP electrical efficiency',
         low,
         high]
    )


    # -------------------------------------------------------------------------
    # Scaling exponent
    # -------------------------------------------------------------------------

    low = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        scaling_exponent=
            SENSITIVITY_PARAMETERS[
                'Scaling exponent'
            ]['low']
    )['lcoe_usd_per_kwh']

    high = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        scaling_exponent=
            SENSITIVITY_PARAMETERS[
                'Scaling exponent'
            ]['high']
    )['lcoe_usd_per_kwh']

    rows.append(
        ['Scaling exponent', low, high]
    )


    # -------------------------------------------------------------------------
    # Discount rate
    # -------------------------------------------------------------------------

    low = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        discount_rate=
            SENSITIVITY_PARAMETERS[
                'Discount rate'
            ]['low']
    )['lcoe_usd_per_kwh']

    high = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        discount_rate=
            SENSITIVITY_PARAMETERS[
                'Discount rate'
            ]['high']
    )['lcoe_usd_per_kwh']

    rows.append(
        ['Discount rate', low, high]
    )


    # -------------------------------------------------------------------------
    # Project life
    # -------------------------------------------------------------------------

    low = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        project_life=
            SENSITIVITY_PARAMETERS[
                'Project life'
            ]['low']
    )['lcoe_usd_per_kwh']

    high = calc_lcoe_chp(
        baseline_vs,
        no_subsidy,
        project_life=
            SENSITIVITY_PARAMETERS[
                'Project life'
            ]['high']
    )['lcoe_usd_per_kwh']

    rows.append(
        ['Project life', low, high]
    )


    # -------------------------------------------------------------------------
    # VS loading per wastewater flow
    # -------------------------------------------------------------------------

    low_vs = (
        baseline_vs
        * SENSITIVITY_PARAMETERS[
            'VS loading per wastewater flow'
        ]['low']
    )

    high_vs = (
        baseline_vs
        * SENSITIVITY_PARAMETERS[
            'VS loading per wastewater flow'
        ]['high']
    )

    low = calc_lcoe_chp(
        low_vs,
        no_subsidy
    )['lcoe_usd_per_kwh']

    high = calc_lcoe_chp(
        high_vs,
        no_subsidy
    )['lcoe_usd_per_kwh']

    rows.append(
        ['VS loading per wastewater flow',
         low,
         high]
    )


    # -------------------------------------------------------------------------
    # Create dataframe
    # -------------------------------------------------------------------------

    sensitivity_df = pd.DataFrame(
        rows,
        columns=[
            'Parameter',
            'Low_LCOE',
            'High_LCOE'
        ]
    )

    sensitivity_df[
        'Baseline_LCOE'
    ] = baseline_lcoe

    sensitivity_df[
        'Low_change_pct'
    ] = (
        (
            sensitivity_df['Low_LCOE']
            - baseline_lcoe
        )
        / baseline_lcoe
        * 100
    )

    sensitivity_df[
        'High_change_pct'
    ] = (
        (
            sensitivity_df['High_LCOE']
            - baseline_lcoe
        )
        / baseline_lcoe
        * 100
    )

    sensitivity_df[
        'Max_abs_change'
    ] = sensitivity_df[
        [
            'Low_change_pct',
            'High_change_pct'
        ]
    ].abs().max(axis=1)

    sensitivity_df = (
        sensitivity_df
        .sort_values(
            'Max_abs_change',
            ascending=True
        )
        .reset_index(drop=True)
    )

    return (
        sensitivity_df,
        baseline_lcoe
    )


# =============================================================================
# RNG sensitivity function
# =============================================================================

def run_rng_sensitivity(mgd):

    no_subsidy = (
        SubsidyScenarios
        .RNG_SCENARIOS['No subsidies']
    )

    baseline_vs = mgd_to_vs(mgd)

    baseline_result = calc_lcoe_rng(
        baseline_vs,
        no_subsidy
    )

    baseline_lcoe = (
        baseline_result[
            'lcoe_usd_per_m3'
        ]
    )

    rows = []


    # -------------------------------------------------------------------------
    # VS destruction
    # -------------------------------------------------------------------------

    low = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        vs_destruction=
            SENSITIVITY_PARAMETERS[
                'VS destruction'
            ]['low']
    )['lcoe_usd_per_m3']

    high = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        vs_destruction=
            SENSITIVITY_PARAMETERS[
                'VS destruction'
            ]['high']
    )['lcoe_usd_per_m3']

    rows.append(
        ['VS destruction', low, high]
    )


    # -------------------------------------------------------------------------
    # CH4 yield
    # -------------------------------------------------------------------------

    low = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        ch4_yield=
            SENSITIVITY_PARAMETERS[
                'CH4 yield'
            ]['low']
    )['lcoe_usd_per_m3']

    high = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        ch4_yield=
            SENSITIVITY_PARAMETERS[
                'CH4 yield'
            ]['high']
    )['lcoe_usd_per_m3']

    rows.append(
        ['CH₄ yield', low, high]
    )


    # -------------------------------------------------------------------------
    # Availability
    # -------------------------------------------------------------------------

    low = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        availability=
            SENSITIVITY_PARAMETERS[
                'Availability'
            ]['low']
    )['lcoe_usd_per_m3']

    high = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        availability=
            SENSITIVITY_PARAMETERS[
                'Availability'
            ]['high']
    )['lcoe_usd_per_m3']

    rows.append(
        ['Availability', low, high]
    )


    # -------------------------------------------------------------------------
    # RNG methane recovery
    # -------------------------------------------------------------------------

    low = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        rng_recovery=
            SENSITIVITY_PARAMETERS[
                'RNG methane recovery'
            ]['low']
    )['lcoe_usd_per_m3']

    high = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        rng_recovery=
            SENSITIVITY_PARAMETERS[
                'RNG methane recovery'
            ]['high']
    )['lcoe_usd_per_m3']

    rows.append(
        ['RNG methane recovery',
         low,
         high]
    )


    # -------------------------------------------------------------------------
    # Scaling exponent
    # -------------------------------------------------------------------------

    low = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        scaling_exponent=
            SENSITIVITY_PARAMETERS[
                'Scaling exponent'
            ]['low']
    )['lcoe_usd_per_m3']

    high = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        scaling_exponent=
            SENSITIVITY_PARAMETERS[
                'Scaling exponent'
            ]['high']
    )['lcoe_usd_per_m3']

    rows.append(
        ['Scaling exponent', low, high]
    )


    # -------------------------------------------------------------------------
    # Discount rate
    # -------------------------------------------------------------------------

    low = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        discount_rate=
            SENSITIVITY_PARAMETERS[
                'Discount rate'
            ]['low']
    )['lcoe_usd_per_m3']

    high = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        discount_rate=
            SENSITIVITY_PARAMETERS[
                'Discount rate'
            ]['high']
    )['lcoe_usd_per_m3']

    rows.append(
        ['Discount rate', low, high]
    )


    # -------------------------------------------------------------------------
    # Project life
    # -------------------------------------------------------------------------

    low = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        project_life=
            SENSITIVITY_PARAMETERS[
                'Project life'
            ]['low']
    )['lcoe_usd_per_m3']

    high = calc_lcoe_rng(
        baseline_vs,
        no_subsidy,
        project_life=
            SENSITIVITY_PARAMETERS[
                'Project life'
            ]['high']
    )['lcoe_usd_per_m3']

    rows.append(
        ['Project life', low, high]
    )


    # -------------------------------------------------------------------------
    # VS loading per wastewater flow
    # -------------------------------------------------------------------------

    low_vs = (
        baseline_vs
        * SENSITIVITY_PARAMETERS[
            'VS loading per wastewater flow'
        ]['low']
    )

    high_vs = (
        baseline_vs
        * SENSITIVITY_PARAMETERS[
            'VS loading per wastewater flow'
        ]['high']
    )

    low = calc_lcoe_rng(
        low_vs,
        no_subsidy
    )['lcoe_usd_per_m3']

    high = calc_lcoe_rng(
        high_vs,
        no_subsidy
    )['lcoe_usd_per_m3']

    rows.append(
        ['VS loading per wastewater flow',
         low,
         high]
    )


    # -------------------------------------------------------------------------
    # Create dataframe
    # -------------------------------------------------------------------------

    sensitivity_df = pd.DataFrame(
        rows,
        columns=[
            'Parameter',
            'Low_LCOE',
            'High_LCOE'
        ]
    )

    sensitivity_df[
        'Baseline_LCOE'
    ] = baseline_lcoe

    sensitivity_df[
        'Low_change_pct'
    ] = (
        (
            sensitivity_df['Low_LCOE']
            - baseline_lcoe
        )
        / baseline_lcoe
        * 100
    )

    sensitivity_df[
        'High_change_pct'
    ] = (
        (
            sensitivity_df['High_LCOE']
            - baseline_lcoe
        )
        / baseline_lcoe
        * 100
    )

    sensitivity_df[
        'Max_abs_change'
    ] = sensitivity_df[
        [
            'Low_change_pct',
            'High_change_pct'
        ]
    ].abs().max(axis=1)

    sensitivity_df = (
        sensitivity_df
        .sort_values(
            'Max_abs_change',
            ascending=True
        )
        .reset_index(drop=True)
    )

    return (
        sensitivity_df,
        baseline_lcoe
    )


# =============================================================================
# Run sensitivity analysis
# =============================================================================

sensitivity_scales = [
    10,
    50,
    200
]

all_chp_sensitivity = []
all_rng_sensitivity = []


for mgd in sensitivity_scales:

    # CHP
    chp_sens, chp_baseline = (
        run_chp_sensitivity(mgd)
    )

    chp_sens[
        'Flow_MGD'
    ] = mgd

    chp_sens[
        'Path'
    ] = 'CHP'

    all_chp_sensitivity.append(
        chp_sens
    )


    # RNG
    rng_sens, rng_baseline = (
        run_rng_sensitivity(mgd)
    )

    rng_sens[
        'Flow_MGD'
    ] = mgd

    rng_sens[
        'Path'
    ] = 'RNG'

    all_rng_sensitivity.append(
        rng_sens
    )


# Combine results
chp_sensitivity_results = pd.concat(
    all_chp_sensitivity,
    ignore_index=True
)

rng_sensitivity_results = pd.concat(
    all_rng_sensitivity,
    ignore_index=True
)


# Save sensitivity results
chp_sensitivity_results.to_csv(
    'chp_sensitivity_results.csv',
    index=False
)

rng_sensitivity_results.to_csv(
    'rng_sensitivity_results.csv',
    index=False
)


# =============================================================================
# Print sensitivity results
# =============================================================================

print(
    "\n"
    + "=" * 90
)

print(
    "CHP SENSITIVITY ANALYSIS"
)

print(
    "=" * 90
)


for mgd in sensitivity_scales:

    temp = (
        chp_sensitivity_results[
            chp_sensitivity_results[
                'Flow_MGD'
            ] == mgd
        ]
        .sort_values(
            'Max_abs_change',
            ascending=False
        )
    )

    print(
        f"\nFacility size = {mgd} MGD"
    )

    print(
        temp[
            [
                'Parameter',
                'Low_change_pct',
                'High_change_pct'
            ]
        ].to_string(
            index=False
        )
    )


print(
    "\n"
    + "=" * 90
)

print(
    "RNG SENSITIVITY ANALYSIS"
)

print(
    "=" * 90
)


for mgd in sensitivity_scales:

    temp = (
        rng_sensitivity_results[
            rng_sensitivity_results[
                'Flow_MGD'
            ] == mgd
        ]
        .sort_values(
            'Max_abs_change',
            ascending=False
        )
    )

    print(
        f"\nFacility size = {mgd} MGD"
    )

    print(
        temp[
            [
                'Parameter',
                'Low_change_pct',
                'High_change_pct'
            ]
        ].to_string(
            index=False
        )
    )


# =============================================================================
# TORNADO PLOT FUNCTION
# =============================================================================

def plot_tornado(
    sensitivity_df,
    pathway,
    mgd
):

    data = sensitivity_df[
        sensitivity_df[
            'Flow_MGD'
        ] == mgd
    ].copy()

    data = data.sort_values(
        'Max_abs_change',
        ascending=True
    )

    y = np.arange(
        len(data)
    )

    low_values = (
        data[
            'Low_change_pct'
        ].values
    )

    high_values = (
        data[
            'High_change_pct'
        ].values
    )


    fig, ax = plt.subplots(
        figsize=(11, 7.5)
    )


    # Low parameter value
    ax.barh(
        y,
        low_values,
        height=0.65,
        alpha=0.75,
        label='Low parameter value'
    )


    # High parameter value
    ax.barh(
        y,
        high_values,
        height=0.65,
        alpha=0.75,
        label='High parameter value'
    )


    # Baseline
    ax.axvline(
        0,
        color='black',
        linewidth=1.8
    )


    ax.set_yticks(
        y
    )

    ax.set_yticklabels(
        data['Parameter'],
        fontsize=15
    )


    ax.set_xlabel(
        'Change in levelized cost relative to baseline (%)',
        fontsize=18
    )


    if pathway == 'CHP':

        ax.set_title(
            f'AD+CHP sensitivity analysis ({mgd} MGD)',
            fontsize=20
        )

    else:

        ax.set_title(
            f'AD+RNG sensitivity analysis ({mgd} MGD)',
            fontsize=20
        )


    ax.tick_params(
        axis='x',
        labelsize=15
    )

    ax.grid(
        axis='x',
        alpha=0.25
    )

    ax.legend(
        fontsize=14,
        frameon=False
    )


    plt.tight_layout()

    plt.show()


# =============================================================================
# Generate tornado plots
# =============================================================================

for mgd in sensitivity_scales:

    plot_tornado(
        chp_sensitivity_results,
        'CHP',
        mgd
    )


for mgd in sensitivity_scales:

    plot_tornado(
        rng_sensitivity_results,
        'RNG',
        mgd
    )


# =============================================================================
# MAIN-PAPER TORNADO PLOTS: 50 MGD
# =============================================================================

# CHP
plot_tornado(
    chp_sensitivity_results,
    'CHP',
    50
)

# RNG
plot_tornado(
    rng_sensitivity_results,
    'RNG',
    50
)