-- ====================================================================
-- GARTNER GSSO ANALYTICS: SALES REPRESENTATIVE PRODUCTIVITY ANALYSIS
-- File: 05_seller_productivity_analysis.sql
-- Concepts: Performance Tiering, Quota Attainment %, Productivity Drivers, Ramp-Up
-- ====================================================================

WITH SellerPerformanceCategorization AS (
    SELECT 
        seller_id,
        seller_name,
        region,
        tenure_months,
        annual_quota,
        actual_attainment_arr,
        quota_attainment_pct,
        avg_monthly_activities,
        lead_conversion_rate,
        
        -- Tenure Ramp-up Segment
        CASE 
            WHEN tenure_months < 12 THEN '1. Ramping (< 12 mos)'
            WHEN tenure_months BETWEEN 12 AND 24 THEN '2. Tenured Core (12-24 mos)'
            ELSE '3. Senior Performer (> 24 mos)'
        END AS tenure_tier,
        
        -- Performance Attainment Tier
        CASE 
            WHEN quota_attainment_pct >= 100 THEN 'Top Performer (100%+)'
            WHEN quota_attainment_pct >= 80 THEN 'Target Performer (80-99%)'
            ELSE 'Underperforming (< 80%)'
        END AS performance_bracket
    FROM sellers
)

-- Summary by Region and Tenure Tier
SELECT 
    region,
    tenure_tier,
    COUNT(seller_id) AS total_reps,
    ROUND(AVG(annual_quota) / 1000.0, 1) AS avg_quota_thousands,
    ROUND(AVG(actual_attainment_arr) / 1000.0, 1) AS avg_revenue_attained_thousands,
    ROUND(AVG(quota_attainment_pct), 1) AS avg_attainment_pct,
    ROUND(AVG(avg_monthly_activities), 1) AS avg_activities_per_rep,
    ROUND(AVG(lead_conversion_rate) * 100, 1) AS avg_conversion_rate_pct,
    
    -- % of Reps hitting target
    ROUND(
        (COUNT(CASE WHEN performance_bracket = 'Top Performer (100%+)' THEN 1 END) * 100.0) / COUNT(seller_id), 
        1
    ) AS pct_reps_hitting_quota
FROM SellerPerformanceCategorization
GROUP BY region, tenure_tier
ORDER BY region, tenure_tier;
