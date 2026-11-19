-- ====================================================================
-- GARTNER GSSO ANALYTICS: PROGRAM EFFECTIVENESS & MEASUREMENT
-- File: 04_program_effectiveness_analysis.sql
-- Concepts: Quasi-Experimental Evaluation, Treatment vs Control, Lift %, ROI
-- ====================================================================

WITH ProgramPerformance AS (
    SELECT 
        p.cohort_type,
        p.is_treated,
        p.completed_program,
        COUNT(p.account_id) AS total_enrolled_accounts,
        SUM(p.intervention_cost) AS total_program_cost,
        SUM(s.prior_year_arr) AS total_baseline_arr,
        
        -- Renewal outcomes
        COUNT(CASE WHEN s.renewal_status IN ('Renewed', 'Expanded') THEN 1 END) AS renewed_accounts_count,
        COUNT(CASE WHEN s.renewal_status = 'Churned' THEN 1 END) AS churned_accounts_count,
        
        -- Retained & Churned Revenue
        SUM(CASE WHEN s.renewal_status IN ('Renewed', 'Expanded') THEN s.prior_year_arr ELSE 0 END) AS retained_arr,
        SUM(CASE WHEN s.renewal_status = 'Churned' THEN s.prior_year_arr ELSE 0 END) AS churned_arr
    FROM gsso_program_enrollment p
    JOIN subscriptions s ON p.account_id = s.account_id AND s.fiscal_year = 2025
    GROUP BY p.cohort_type, p.is_treated, p.completed_program
)

SELECT 
    cohort_type,
    CASE 
        WHEN is_treated = 1 AND completed_program = 1 THEN 'Treatment - Completed'
        WHEN is_treated = 1 AND completed_program = 0 THEN 'Treatment - Dropped/Incomplete'
        ELSE 'Control Group (No Intervention)'
    END AS group_segment,
    
    total_enrolled_accounts,
    ROUND(total_baseline_arr / 1000000.0, 2) AS baseline_arr_millions,
    
    -- Renewal Rate
    ROUND((renewed_accounts_count * 100.0) / total_enrolled_accounts, 2) AS renewal_rate_pct,
    
    -- Logo Churn Rate
    ROUND((churned_accounts_count * 100.0) / total_enrolled_accounts, 2) AS churn_rate_pct,
    
    ROUND(retained_arr / 1000000.0, 2) AS retained_arr_millions,
    ROUND(churned_arr / 1000000.0, 2) AS lost_arr_millions,
    
    total_program_cost
FROM ProgramPerformance
ORDER BY renewal_rate_pct DESC;
