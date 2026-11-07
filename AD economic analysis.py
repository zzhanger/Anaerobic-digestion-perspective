# -*- coding: utf-8 -*-
"""
Created on Mon May 11 12:19:56 2026

@author: zz1405
"""

"""
AD+CHP vs AD+RNG LCOE 计算模型

"""

"""
AD+CHP vs AD+RNG LCOE Model
Based on literature data (1600 WCE facility)

CORRECTION: Environmental credits are COSTS (carbon compliance), not revenue
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================================
# Literature Data (1600 WCE = 10,858 kg VS/day)
# ============================================================================

class LiteratureData:
    # Scale
    WCE = 1600     # equivalent to 135600 PE or 11 MGD
    VS_kg_per_day = 10858    # 58 kg VS/m3 * 0.117 m3/WCE *1600
    
    # CAPEX (USD)
    CAPEX_AD = 1879000
    CAPEX_RNG = 3266745    # 1 mile pipeline distance
    CAPEX_CHP = 1880565
    
    # Annual OPEX (USD/year)
    OPEX_AD = 162766
    OPEX_RNG = 147086
    OPEX_CHP = 112500
    
    # Environmental credits (COSTS - carbon compliance)
    ENV_CREDIT_RNG = 47000  # USD/year (cost)
    ENV_CREDIT_CHP = 6000   # USD/year (cost)
    
    # Financial
    PROJECT_LIFE = 20  # years
    DISCOUNT_RATE = 0.07


# ============================================================================
# Technical Parameters (UPDATED based on real plant data)
# ============================================================================

VS_DESTRUCTION = 0.55          
CH4_YIELD = 0.51               # m³ CH4/kg VS destroyed
AVAILABILITY = 0.92            
CH4_LHV = 9.97                 # kWh/m³ CH₄
CH4_ELEC_EFF = 0.38            
RNG_RECOVERY = 0.96            # methane recovery for RNG
SCALING_EXPONENT = 0.80        # economy of scale


# ============================================================================
# Conversion Factors: VS to MGD (UPDATED)
# ============================================================================

# Municipal WWTP assumptions (updated based on real plant data)
VS_PER_CAPITA = 0.08           
FLOW_PER_CAPITA_GPD = 100      # gallons/person/day

def vs_to_mgd(vs_kg_per_day):
    """Convert VS loading to wastewater flow (MGD)"""
    population = vs_kg_per_day / VS_PER_CAPITA
    mgd = population * FLOW_PER_CAPITA_GPD / 1000000
    return mgd

def mgd_to_vs(mgd):
    """Convert wastewater flow (MGD) to VS loading (kg/day)"""
    population = mgd * 1000000 / FLOW_PER_CAPITA_GPD
    vs = population * VS_PER_CAPITA
    return vs


# ============================================================================
# Subsidy Scenarios (SIMPLIFIED - 4 scenarios each)
# ============================================================================

class SubsidyScenarios:
    """
    Simplified subsidy scenarios for WWTP AD+CHP and AD+RNG.
    """

    # -------------------------
    # AD + CHP subsidy scenarios (4 scenarios)
    # -------------------------
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

    # -------------------------
    # AD + RNG subsidy scenarios (4 scenarios)
    # -------------------------
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

        "D3 RIN (1.92 USD/RIN)": {
            "capex_grant": 0.00,
            "prod_credit_usd_per_m3": 0.85,
            "description": "D3 RIN ($1.92/RIN)"
        },

        "LCFS 90 USD/tCO2e": {
            "capex_grant": 0.00,
            "prod_credit_usd_per_m3": 0.35,
            "description": "LCFS ($0.35)"
        },
    }


# ============================================================================
# Production Calculations
# ============================================================================

def calc_production(vs_kg_per_day):
    """Calculate CH4 and energy production"""
    vs_destroyed = vs_kg_per_day * VS_DESTRUCTION
    ch4_per_year = vs_destroyed * CH4_YIELD * 365 * AVAILABILITY
    energy_kwh_per_year = ch4_per_year * CH4_LHV
    return {
        'ch4_m3_per_year': ch4_per_year,
        'energy_kwh_per_year': energy_kwh_per_year,
        'vs_destroyed_kg_per_day': vs_destroyed
    }


# ============================================================================
# LCOE Calculations with Subsidies
# ============================================================================

def get_crf():
    """Capital Recovery Factor"""
    r = LiteratureData.DISCOUNT_RATE
    n = LiteratureData.PROJECT_LIFE
    return (r * (1 + r)**n) / ((1 + r)**n - 1)


def calc_lcoe_chp(vs_kg_per_day, subsidy_scenario):
    """LCOE for AD+CHP with subsidies (USD/kWh) - includes production credits"""
    
    prod = calc_production(vs_kg_per_day)
    electricity_kwh = prod['energy_kwh_per_year'] * CH4_ELEC_EFF
    
    scale_factor = (vs_kg_per_day / LiteratureData.VS_kg_per_day) ** SCALING_EXPONENT
    
    capex_ad = LiteratureData.CAPEX_AD * scale_factor
    capex_chp = LiteratureData.CAPEX_CHP * scale_factor
    capex_total = capex_ad + capex_chp
    
    # Apply CAPEX grant (ITC)
    capex_grant = subsidy_scenario.get('capex_grant', 0)
    capex_total_after_grant = capex_total * (1 - capex_grant)
    
    opex_ad = LiteratureData.OPEX_AD * scale_factor
    opex_chp = LiteratureData.OPEX_CHP * scale_factor
    env_cost = LiteratureData.ENV_CREDIT_CHP
    opex_total = opex_ad + opex_chp + env_cost
    
    # Production subsidy (revenue) - REC + PTC
    prod_credit = subsidy_scenario.get('prod_credit_usd_per_kwh', 0)
    subsidy_revenue = electricity_kwh * prod_credit
    
    # Annualized cost - SUBTRACT production subsidies from cost
    annualized_capex = capex_total_after_grant * get_crf()
    annual_cost = annualized_capex + opex_total - subsidy_revenue  
    lcoe_usd = annual_cost / electricity_kwh if electricity_kwh > 0 else np.nan
    
    # Net profit (based on reduced LCOE)
    avg_elec_price = 0.105  # USD/kWh
    net_profit = electricity_kwh * (avg_elec_price - lcoe_usd)
    
    return {
        'lcoe_usd_per_kwh': lcoe_usd,
        'lcoe_cent_per_kwh': lcoe_usd * 100,
        'electricity_mwh_per_year': electricity_kwh / 1000,
        'capex_total_usd': capex_total,
        'capex_total_after_grant_usd': capex_total_after_grant,
        'opex_total_usd': opex_total,
        'subsidy_revenue_usd_per_year': subsidy_revenue,
        'net_profit_usd_per_year': net_profit,
        'capex_grant_pct': capex_grant * 100,
        'prod_credit_usd_per_kwh': prod_credit
    }


def calc_lcoe_rng(vs_kg_per_day, subsidy_scenario):
    """LCOE for AD+RNG with subsidies (USD/m³ RNG) - includes production credits"""
    
    prod = calc_production(vs_kg_per_day)
    rng_m3_per_year = prod['ch4_m3_per_year'] * RNG_RECOVERY
    
    scale_factor = (vs_kg_per_day / LiteratureData.VS_kg_per_day) ** SCALING_EXPONENT
    
    capex_ad = LiteratureData.CAPEX_AD * scale_factor
    capex_rng = LiteratureData.CAPEX_RNG * scale_factor
    capex_total = capex_ad + capex_rng
    
    # Apply CAPEX grant (ITC for RNG equipment)
    capex_grant = subsidy_scenario.get('capex_grant', 0)
    capex_total_after_grant = capex_total * (1 - capex_grant)
    
    opex_ad = LiteratureData.OPEX_AD * scale_factor
    opex_rng = LiteratureData.OPEX_RNG * scale_factor
    env_cost = LiteratureData.ENV_CREDIT_RNG
    opex_total = opex_ad + opex_rng + env_cost
    
    # Production subsidy (revenue) - RINs + LCFS
    prod_credit = subsidy_scenario.get('prod_credit_usd_per_m3', 0)
    subsidy_revenue = rng_m3_per_year * prod_credit
    
    # Annualized cost - SUBTRACT production subsidies from cost
    annualized_capex = capex_total_after_grant * get_crf()
    annual_cost = annualized_capex + opex_total - subsidy_revenue
    lcoe = annual_cost / rng_m3_per_year if rng_m3_per_year > 0 else np.nan
    
    # Net profit (based on reduced LCOE)
    avg_gas_price = 0.45  # USD/m³
    net_profit = rng_m3_per_year * (avg_gas_price - lcoe)
    
    return {
        'lcoe_usd_per_m3': lcoe,
        'rng_mm_m3_per_year': rng_m3_per_year / 1_000_000,
        'capex_total_usd': capex_total,
        'capex_total_after_grant_usd': capex_total_after_grant,
        'opex_total_usd': opex_total,
        'subsidy_revenue_usd_per_year': subsidy_revenue,
        'net_profit_usd_per_year': net_profit,
        'capex_grant_pct': capex_grant * 100,
        'prod_credit_usd_per_m3': prod_credit
    }


# ============================================================================
# Main Analysis
# ============================================================================

# Economic benchmarks
AVG_ELEC_PRICE = 0.105   # USD/kWh = 10.5 ¢/kWh
AVG_GAS_PRICE = 0.45     # USD/m³ (pipeline gas price for injection benchmark)

# Define facility scales in MGD
flow_scales_mgd = np.array([2, 5, 10, 20, 30, 50, 100, 150, 200])

# Convert to VS
vs_scales = np.array([mgd_to_vs(mgd) for mgd in flow_scales_mgd])

# Calculate literature facility MGD equivalent
lit_mgd = vs_to_mgd(LiteratureData.VS_kg_per_day)

print("=" * 90)
print("AD+CHP vs AD+RNG LCOE Model with Subsidy Scenarios")
print(f"Based on literature data: 1600 WCE = {LiteratureData.VS_kg_per_day:,} kg VS/day")
print(f"= {lit_mgd:.1f} MGD (at {VS_PER_CAPITA:.2f} kg VS/PE, {FLOW_PER_CAPITA_GPD} gpd/PE)")
print("=" * 90)

# Display subsidy scenarios
print("\n" + "=" * 90)
print("SUBSIDY SCENARIOS (UPDATED)")
print("=" * 90)

print("\nCHP Subsidy Scenarios:")
for name, scenario in SubsidyScenarios.CHP_SCENARIOS.items():
    print(f"  {name:12s}: {scenario['description']}")

print("\nRNG Subsidy Scenarios:")
for name, scenario in SubsidyScenarios.RNG_SCENARIOS.items():
    print(f"  {name:12s}: {scenario['description']}")

# Calculate for each scale and each scenario (INDEPENDENTLY)
all_results = []

for vs, mgd in zip(vs_scales, flow_scales_mgd):
    # CHP results - independent of RNG
    for chp_name, chp_scenario in SubsidyScenarios.CHP_SCENARIOS.items():
        chp = calc_lcoe_chp(vs, chp_scenario)
        
        all_results.append({
            'Path': 'CHP',
            'Scenario': chp_name,
            'Flow_MGD': mgd,
            'VS_ton_per_day': vs / 1000,
            # CHP results
            'LCOE_cent_per_kWh': chp['lcoe_cent_per_kwh'],
            'Electricity_MWh_per_year': chp['electricity_mwh_per_year'],
            'CAPEX_MUSD': chp['capex_total_after_grant_usd'] / 1_000_000,
            'OPEX_MUSD_per_year': chp['opex_total_usd'] / 1_000_000,
            'Subsidy_Revenue_MUSD_per_year': chp['subsidy_revenue_usd_per_year'] / 1_000_000,
            'Net_Profit_MUSD_per_year': chp['net_profit_usd_per_year'] / 1_000_000,
            # RNG fields (empty)
            'RNG_LCOE_USD_per_m3': np.nan,
            'RNG_Output_MM_m3_per_year': np.nan,
        })
    
    # RNG results - independent of CHP
    for rng_name, rng_scenario in SubsidyScenarios.RNG_SCENARIOS.items():
        rng = calc_lcoe_rng(vs, rng_scenario)
        
        all_results.append({
            'Path': 'RNG',
            'Scenario': rng_name,
            'Flow_MGD': mgd,
            'VS_ton_per_day': vs / 1000,
            # CHP fields (empty)
            'LCOE_cent_per_kWh': np.nan,
            'Electricity_MWh_per_year': np.nan,
            'CAPEX_MUSD': np.nan,
            'OPEX_MUSD_per_year': np.nan,
            'Subsidy_Revenue_MUSD_per_year': np.nan,
            'Net_Profit_MUSD_per_year': np.nan,
            # RNG results
            'RNG_LCOE_USD_per_m3': rng['lcoe_usd_per_m3'],
            'RNG_Output_MM_m3_per_year': rng['rng_mm_m3_per_year'],
            'RNG_CAPEX_MUSD': rng['capex_total_after_grant_usd'] / 1_000_000,
            'RNG_OPEX_MUSD_per_year': rng['opex_total_usd'] / 1_000_000,
            'RNG_Subsidy_Revenue_MUSD_per_year': rng['subsidy_revenue_usd_per_year'] / 1_000_000,
            'RNG_Net_Profit_MUSD_per_year': rng['net_profit_usd_per_year'] / 1_000_000,
        })

df = pd.DataFrame(all_results)

# Save to CSV
df.to_csv('lcoe_results.csv', index=False)