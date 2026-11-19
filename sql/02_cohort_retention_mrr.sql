-- ====================================================================
-- GARTNER GSSO ANALYTICS: RETENTION & REVENUE METRICS (GRR / NRR / CHURN)
-- File: 02_cohort_retention_mrr.sql
-- Concepts: CTEs, Window Functions (LAG, SUM OVER), CASE WHEN, Aggregations
-- ====================================================================

WITH PriorVsCurrentRevenue AS (
    SELECT 
        s.account_id,
        a.tier,
        a.region,
        a.industry,
        s.fiscal_year,
        s.prior_year_arr,
        s.contract_value_arr AS current_year_arr,
        s.renewal_status,
        s.expansion_arr,
        s.churn_arr
    FROM subscriptions s
    JOIN accounts a ON s.account_id = a.account_id
    WHERE s.fiscal_year = 2025
),

-- Aggregate base metrics by Tier and Region
TierRegionMetrics AS (
    SELECT 
        tier,
        region,
        COUNT(account_id) AS total_accounts_up_for_renewal,
        SUM(prior_year_arr) AS starting_arr_base,
        
        -- Retained revenue capped at prior ARR (for GRR)
        SUM(CASE 
            WHEN renewal_status IN ('Renewed', 'Expanded') THEN prior_year_arr
            WHEN renewal_status = 'Contracted' THEN current_year_arr
            ELSE 0 
        END) AS retained_arr_base,
        
        -- Net current revenue including expansions (for NRR)
        SUM(current_year_arr) AS ending_arr_total,
        
        -- Expansions & Churn breakdowns
        SUM(expansion_arr) AS total_expansion_arr,
        SUM(churn_arr) AS total_churn_arr,
        
        -- Logo counts
        COUNT(CASE WHEN renewal_status = 'Churned' THEN 1 END) AS churned_logos,
        COUNT(CASE WHEN renewal_status = 'Expanded' THEN 1 END) AS expanded_logos,
        COUNT(CASE WHEN renewal_status = 'Renewed' THEN 1 END) AS flat_renewed_logos
    FROM PriorVsCurrentRevenue
    GROUP BY tier, region
)

SELECT 
    tier,
    region,
    total_accounts_up_for_renewal,
    ROUND(starting_arr_base / 1000000.0, 2) AS starting_arr_millions,
    ROUND(ending_arr_total / 1000000.0, 2) AS ending_arr_millions,
    
    -- Logo Churn Rate %
    ROUND((churned_logos * 100.0) / total_accounts_up_for_renewal, 2) AS logo_churn_pct,
    
    -- Gross Revenue Retention (GRR): How well we retain existing base without expansions (Target: > 85%)
    ROUND((retained_arr_base * 100.0) / starting_arr_base, 2) AS grr_pct,
    
    -- Net Revenue Retention (NRR): Retention including expansion (Target: > 105%)
    ROUND((ending_arr_total * 100.0) / starting_arr_base, 2) AS nrr_pct,
    
    -- Total Dollar Churn at Risk
    ROUND(total_churn_arr / 1000000.0, 2) AS churned_arr_millions
FROM TierRegionMetrics
ORDER BY tier, grr_pct DESC;
