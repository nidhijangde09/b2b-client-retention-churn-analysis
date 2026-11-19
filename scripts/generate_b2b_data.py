import os
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. GENERATE SELLERS (SALES REPS)
# -------------------------------------------------------------
n_sellers = 80
regions = ["North America", "EMEA", "APAC", "LATAM"]
region_weights = [0.45, 0.30, 0.15, 0.10]

seller_ids = [f"REP-{1000 + i}" for i in range(n_sellers)]
seller_names = [f"Seller_{i+1}" for i in range(n_sellers)]
seller_regions = np.random.choice(regions, size=n_sellers, p=region_weights)
seller_tenure_months = np.random.randint(6, 60, size=n_sellers)
seller_annual_quotas = np.random.choice([1200000, 1500000, 1800000, 2200000], size=n_sellers, p=[0.25, 0.40, 0.25, 0.10])

# Quota attainment correlated with tenure and activity
activities_per_month = np.random.normal(loc=35 + seller_tenure_months * 0.4, scale=6, size=n_sellers).clip(15, 75).round(1)
conversion_rates = np.random.normal(loc=0.18 + (seller_tenure_months / 100) * 0.08, scale=0.03, size=n_sellers).clip(0.08, 0.35).round(3)
actual_attainment_arr = (seller_annual_quotas * np.random.normal(loc=0.88 + (conversion_rates - 0.18)*1.5, scale=0.12, size=n_sellers)).round(-3).clip(400000, 3200000)
attainment_pct = ((actual_attainment_arr / seller_annual_quotas) * 100).round(1)

df_sellers = pd.DataFrame({
    "seller_id": seller_ids,
    "seller_name": seller_names,
    "region": seller_regions,
    "tenure_months": seller_tenure_months,
    "annual_quota": seller_annual_quotas,
    "actual_attainment_arr": actual_attainment_arr,
    "quota_attainment_pct": attainment_pct,
    "avg_monthly_activities": activities_per_month,
    "lead_conversion_rate": conversion_rates
})

# -------------------------------------------------------------
# 2. GENERATE ACCOUNTS
# -------------------------------------------------------------
n_accounts = 1200
account_ids = [f"ACC-{2000 + i}" for i in range(n_accounts)]
account_names = [f"Enterprise_Client_{i+1}" for i in range(n_accounts)]
tiers = ["Enterprise", "Strategic", "Mid-Market"]
tier_weights = [0.40, 0.25, 0.35]
industries = ["Technology", "Financial Services", "Healthcare", "Manufacturing", "Retail & CPG", "Public Sector"]
ind_weights = [0.30, 0.25, 0.15, 0.12, 0.10, 0.08]

acc_tiers = np.random.choice(tiers, size=n_accounts, p=tier_weights)
acc_industries = np.random.choice(industries, size=n_accounts, p=ind_weights)
acc_regions = np.random.choice(regions, size=n_accounts, p=region_weights)
assigned_sellers = np.random.choice(seller_ids, size=n_accounts)

# Baseline ARR by tier
base_arr_map = {
    "Strategic": (150000, 350000),
    "Enterprise": (60000, 160000),
    "Mid-Market": (25000, 65000)
}
current_arrs = [np.random.randint(base_arr_map[t][0], base_arr_map[t][1]) for t in acc_tiers]

df_accounts = pd.DataFrame({
    "account_id": account_ids,
    "account_name": account_names,
    "tier": acc_tiers,
    "industry": acc_industries,
    "region": acc_regions,
    "assigned_seller_id": assigned_sellers,
    "baseline_arr": current_arrs
})

# -------------------------------------------------------------
# 3. GSSO PROGRAM ENROLLMENT (Strategic Intervention Program)
# -------------------------------------------------------------
# Eligible: Enterprise & Strategic accounts renewal in H2 2025 or H1 2026 (700 accounts)
eligible_mask = df_accounts["tier"].isin(["Enterprise", "Strategic"])
eligible_accounts = df_accounts[eligible_mask]["account_id"].tolist()
np.random.shuffle(eligible_accounts)

n_study = min(600, len(eligible_accounts))
study_accounts = eligible_accounts[:n_study]
# 50% treatment, 50% control
treatment_accounts = set(study_accounts[:n_study//2])
control_accounts = set(study_accounts[n_study//2:])

program_records = []
for acc_id in study_accounts:
    is_treated = 1 if acc_id in treatment_accounts else 0
    completed = 1 if (is_treated and np.random.rand() > 0.12) else 0 # 88% completion in treatment
    program_records.append({
        "account_id": acc_id,
        "program_id": "PRG-RET-2025",
        "program_name": "Executive Onboarding & Guided Seat Adoption",
        "cohort_type": "Treatment" if is_treated else "Control",
        "is_treated": is_treated,
        "completed_program": completed,
        "intervention_cost": 1450 if is_treated else 0
    })

df_programs = pd.DataFrame(program_records)

# -------------------------------------------------------------
# 4. SUBSCRIPTIONS & RENEWAL PERFORMANCE
# -------------------------------------------------------------
sub_records = []
treatment_map = dict(zip(df_programs["account_id"], df_programs["is_treated"]))
completed_map = dict(zip(df_programs["account_id"], df_programs["completed_program"]))

for idx, row in df_accounts.iterrows():
    acc_id = row["account_id"]
    tier = row["tier"]
    base_arr = row["baseline_arr"]
    is_treated = treatment_map.get(acc_id, 0)
    completed_prg = completed_map.get(acc_id, 0)
    
    # 2024 historical baseline contract
    sub_records.append({
        "subscription_id": f"SUB-2024-{idx+1:04d}",
        "account_id": acc_id,
        "fiscal_year": 2024,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "contract_value_arr": base_arr,
        "prior_year_arr": base_arr,
        "renewal_status": "Renewed",
        "expansion_arr": 0,
        "churn_arr": 0
    })
    
    # 2025/2026 renewal decision logic
    # Baseline renewal probability depends on tier and program intervention
    base_prob = 0.78 if tier == "Mid-Market" else (0.83 if tier == "Enterprise" else 0.88)
    
    if completed_prg == 1:
        base_prob += 0.09 # +9% statistically significant lift from GSSO program
    elif is_treated == 1 and completed_prg == 0:
        base_prob += 0.02
        
    rand_val = np.random.rand()
    if rand_val < (1 - base_prob):
        status = "Churned"
        contract_2025 = 0
        expansion = 0
        churn_amt = base_arr
    elif rand_val < (1 - base_prob + 0.25):
        status = "Expanded"
        expansion = round(base_arr * np.random.uniform(0.10, 0.35), -2)
        contract_2025 = base_arr + expansion
        churn_amt = 0
    else:
        status = "Renewed"
        contract_2025 = base_arr
        expansion = 0
        churn_amt = 0
        
    sub_records.append({
        "subscription_id": f"SUB-2025-{idx+1:04d}",
        "account_id": acc_id,
        "fiscal_year": 2025,
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "contract_value_arr": contract_2025,
        "prior_year_arr": base_arr,
        "renewal_status": status,
        "expansion_arr": expansion,
        "churn_arr": churn_amt
    })

df_subscriptions = pd.DataFrame(sub_records)

# -------------------------------------------------------------
# 5. ACCOUNT TELEMETRY & PRODUCT USAGE (Monthly snapshots)
# -------------------------------------------------------------
telemetry_records = []
# 12 months for 2025
months = [f"2025-{m:02d}-01" for m in range(1, 13)]

# Map 2025 status to simulate realistic leading indicators
sub_status_2025 = df_subscriptions[df_subscriptions["fiscal_year"] == 2025].set_index("account_id")["renewal_status"].to_dict()

for idx, row in df_accounts.iterrows():
    acc_id = row["account_id"]
    tier = row["tier"]
    status = sub_status_2025.get(acc_id, "Renewed")
    licensed_seats = 20 if tier == "Mid-Market" else (50 if tier == "Enterprise" else 120)
    
    # Healthy vs churn trajectory
    for m_idx, m_date in enumerate(months):
        if status == "Churned":
            # Declining engagement curve
            decay_factor = max(0.15, 1.0 - (m_idx / 11) * 0.70)
        elif status == "Expanded":
            # Expanding usage
            decay_factor = min(1.25, 0.85 + (m_idx / 11) * 0.35)
        else:
            # Stable renewal
            decay_factor = np.random.uniform(0.75, 1.05)
            
        active_users = int(np.clip(licensed_seats * decay_factor * np.random.uniform(0.7, 0.95), 1, licensed_seats))
        seat_util = round(active_users / licensed_seats, 3)
        portal_logins = int(active_users * np.random.uniform(3, 8))
        research_downloads = int(active_users * np.random.uniform(0.8, 2.5))
        analyst_inquiries = int(np.random.poisson(lam=1.8 if status != 'Churned' else 0.4))
        sponsor_engaged = 1 if (status != "Churned" and np.random.rand() > 0.25) else (1 if np.random.rand() > 0.7 else 0)
        tickets_opened = np.random.randint(0, 4)
        avg_res_days = round(np.random.uniform(1.2, 5.5), 1)
        
        telemetry_records.append({
            "account_id": acc_id,
            "metric_month": m_date,
            "licensed_seats": licensed_seats,
            "active_users": active_users,
            "seat_utilization_pct": seat_util,
            "portal_logins": portal_logins,
            "research_downloads": research_downloads,
            "analyst_inquiries": analyst_inquiries,
            "executive_sponsor_engaged": sponsor_engaged,
            "support_tickets_opened": tickets_opened,
            "avg_resolution_days": avg_res_days
        })

df_telemetry = pd.DataFrame(telemetry_records)

# -------------------------------------------------------------
# 6. EXPORT TO CSV AND SQLITE DB
# -------------------------------------------------------------
df_sellers.to_csv(os.path.join(DATA_DIR, "sellers.csv"), index=False)
df_accounts.to_csv(os.path.join(DATA_DIR, "accounts.csv"), index=False)
df_programs.to_csv(os.path.join(DATA_DIR, "gsso_program_enrollment.csv"), index=False)
df_subscriptions.to_csv(os.path.join(DATA_DIR, "subscriptions.csv"), index=False)
df_telemetry.to_csv(os.path.join(DATA_DIR, "account_telemetry_monthly.csv"), index=False)

db_path = os.path.join(DATA_DIR, "b2b_retention.db")
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
df_sellers.to_sql("sellers", conn, index=False)
df_accounts.to_sql("accounts", conn, index=False)
df_programs.to_sql("gsso_program_enrollment", conn, index=False)
df_subscriptions.to_sql("subscriptions", conn, index=False)
df_telemetry.to_sql("account_telemetry_monthly", conn, index=False)
conn.close()

print(f"Data generation complete! Files written to {DATA_DIR}")
print(f"Accounts: {len(df_accounts)}, Subscriptions: {len(df_subscriptions)}, Monthly Telemetry: {len(df_telemetry)}, Sellers: {len(df_sellers)}")
