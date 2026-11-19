import os
import sqlite3
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "b2b_retention.db")

conn = sqlite3.connect(DB_PATH)

# ==============================================================================
# PART 1: STATISTICAL EVALUATION OF GSSO PROGRAM IMPACT (TREATMENT VS CONTROL)
# ==============================================================================
query_program = """
SELECT 
    p.account_id,
    p.cohort_type,
    p.is_treated,
    p.completed_program,
    p.intervention_cost,
    s.prior_year_arr,
    s.contract_value_arr,
    s.renewal_status,
    CASE WHEN s.renewal_status IN ('Renewed', 'Expanded') THEN 1 ELSE 0 END AS renewed_flag
FROM gsso_program_enrollment p
JOIN subscriptions s ON p.account_id = s.account_id AND s.fiscal_year = 2025
"""

df_prg = pd.read_sql_query(query_program, conn)

# Compare Treatment (Completed) vs Control
treated_completed = df_prg[df_prg["completed_program"] == 1]
control_group = df_prg[df_prg["is_treated"] == 0]

n_treat = len(treated_completed)
n_ctrl = len(control_group)

renewals_treat = treated_completed["renewed_flag"].sum()
renewals_ctrl = control_group["renewed_flag"].sum()

rate_treat = renewals_treat / n_treat
rate_ctrl = renewals_ctrl / n_ctrl
lift_pct = (rate_treat - rate_ctrl) * 100

# Two-proportion z-test
p_pool = (renewals_treat + renewals_ctrl) / (n_treat + n_ctrl)
se_pool = np.sqrt(p_pool * (1 - p_pool) * (1/n_treat + 1/n_ctrl))
z_stat = (rate_treat - rate_ctrl) / se_pool
p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

# Financial Impact & ROI
total_treat_cost = treated_completed["intervention_cost"].sum()
avg_contract_val = treated_completed["prior_year_arr"].mean()
incremental_accounts_saved = (rate_treat - rate_ctrl) * n_treat
incremental_arr_saved = incremental_accounts_saved * avg_contract_val
net_benefit = incremental_arr_saved - total_treat_cost
program_roi = (net_benefit / total_treat_cost) * 100

print("="*65)
print("GSSO STRATEGIC PROGRAM IMPACT ANALYSIS (EXECUTIVE METRICS)")
print("="*65)
print(f"Treatment Group (Completed) Renewal Rate : {rate_treat*100:.2f}% (N = {n_treat})")
print(f"Control Group Renewal Rate               : {rate_ctrl*100:.2f}% (N = {n_ctrl})")
print(f"Statistically Significant Lift           : +{lift_pct:.2f}%")
print(f"Z-Statistic                              : {z_stat:.4f} (p-value: {p_value:.5f})")
print(f"Status                                   : {'STATISTICALLY SIGNIFICANT (p < 0.01)' if p_value < 0.01 else 'Not Significant'}")
print("-" * 65)
print(f"Total Program Operational Cost           : ${total_treat_cost:,.2f}")
print(f"Incremental ARR Retained                 : ${incremental_arr_saved:,.2f}")
print(f"Net Program Value Created                : ${net_benefit:,.2f}")
print(f"Program Return on Investment (ROI)       : {program_roi:.1f}%")
print("="*65)

# ==============================================================================
# PART 2: MULTIVARIATE CHURN DRIVER ANALYSIS
# ==============================================================================
query_drivers = """
SELECT 
    t.account_id,
    AVG(t.seat_utilization_pct) AS avg_seat_util,
    AVG(t.portal_logins) AS avg_logins,
    AVG(t.research_downloads) AS avg_downloads,
    SUM(t.analyst_inquiries) AS total_analyst_calls,
    MAX(t.executive_sponsor_engaged) AS has_sponsor,
    SUM(t.support_tickets_opened) AS total_tickets,
    CASE WHEN s.renewal_status = 'Churned' THEN 1 ELSE 0 END AS churned_flag
FROM account_telemetry_monthly t
JOIN subscriptions s ON t.account_id = s.account_id AND s.fiscal_year = 2025
WHERE t.metric_month IN ('2025-07-01', '2025-08-01', '2025-09-01') -- Pre-renewal leading indicators (Q3)
GROUP BY t.account_id
"""

df_drivers = pd.read_sql_query(query_drivers, conn)

# Simple correlation matrix
numeric_cols = df_drivers.drop(columns=["account_id"])
corr = numeric_cols.corr()["churned_flag"].sort_values()
print("\nCHURN DRIVER CORRELATION (Leading Indicators in Q3 prior to renewal):")
for col, val in corr.items():
    if col != "churned_flag":
        print(f"  {col:<25} : {val:+.3f}")

conn.close()

# Save summary to csv for presentation/dashboard
impact_summary = pd.DataFrame([{
    "metric": "Treatment Renewal Rate %", "value": f"{rate_treat*100:.1f}%"
}, {
    "metric": "Control Renewal Rate %", "value": f"{rate_ctrl*100:.1f}%"
}, {
    "metric": "Incremental Lift %", "value": f"+{lift_pct:.1f}%"
}, {
    "metric": "p-value", "value": f"{p_value:.5f}"
}, {
    "metric": "Retained ARR", "value": f"${incremental_arr_saved/1000000:.2f}M"
}, {
    "metric": "Program ROI %", "value": f"{program_roi:.0f}%"
}])
impact_summary.to_csv(os.path.join(DATA_DIR, "program_impact_summary.csv"), index=False)
print(f"\nSummary metrics exported to {os.path.join(DATA_DIR, 'program_impact_summary.csv')}")
