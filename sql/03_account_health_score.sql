-- ====================================================================
-- GARTNER GSSO ANALYTICS: 90-DAY ACCOUNT HEALTH SCORING & CHURN PREDICTION
-- File: 03_account_health_score.sql
-- Concepts: Rolling Averages, Windowing, Composite Scoring, Revenue at Risk
-- ====================================================================

WITH RecentTelemetry AS (
    -- Take last 3 months of telemetry (Months 10, 11, 12 of 2025)
    SELECT 
        account_id,
        AVG(seat_utilization_pct) AS avg_seat_utilization,
        AVG(portal_logins) AS avg_monthly_logins,
        AVG(research_downloads) AS avg_monthly_downloads,
        SUM(analyst_inquiries) AS total_analyst_inquiries_90d,
        MAX(executive_sponsor_engaged) AS has_active_sponsor,
        SUM(support_tickets_opened) AS total_tickets_opened,
        AVG(avg_resolution_days) AS avg_ticket_resolution_time
    FROM account_telemetry_monthly
    WHERE metric_month IN ('2025-10-01', '2025-11-01', '2025-12-01')
    GROUP BY account_id
),

ScoredAccounts AS (
    SELECT 
        a.account_id,
        a.account_name,
        a.tier,
        a.region,
        a.industry,
        a.baseline_arr,
        t.avg_seat_utilization,
        t.total_analyst_inquiries_90d,
        t.has_active_sponsor,
        t.total_tickets_opened,
        
        -- Multi-Factor Health Score calculation (0 to 100)
        ROUND(
            (CASE 
                WHEN t.avg_seat_utilization >= 0.75 THEN 35
                WHEN t.avg_seat_utilization >= 0.50 THEN 22
                WHEN t.avg_seat_utilization >= 0.30 THEN 10
                ELSE 0 
            END) +
            (CASE 
                WHEN t.total_analyst_inquiries_90d >= 4 THEN 25
                WHEN t.total_analyst_inquiries_90d >= 2 THEN 18
                WHEN t.total_analyst_inquiries_90d >= 1 THEN 10
                ELSE 0 
            END) +
            (CASE 
                WHEN t.has_active_sponsor = 1 THEN 25
                ELSE 0 
            END) +
            (CASE 
                WHEN t.total_tickets_opened <= 1 THEN 15
                WHEN t.total_tickets_opened <= 3 THEN 8
                ELSE 0 
            END),
            1
        ) AS account_health_score
    FROM accounts a
    JOIN RecentTelemetry t ON a.account_id = t.account_id
)

SELECT 
    account_id,
    account_name,
    tier,
    region,
    industry,
    baseline_arr,
    ROUND(avg_seat_utilization * 100, 1) AS seat_utilization_pct,
    total_analyst_inquiries_90d,
    has_active_sponsor,
    account_health_score,
    
    -- Risk Classification & Recommended GSSO Playbook Action
    CASE 
        WHEN account_health_score >= 70 THEN 'Green (Low Risk)'
        WHEN account_health_score >= 45 THEN 'Amber (Moderate Risk)'
        ELSE 'Red (Critical Risk)'
    END AS risk_tier,
    
    CASE 
        WHEN account_health_score < 45 AND has_active_sponsor = 0 
            THEN 'Urgent: Executive Re-alignment & Sponsor Briefing'
        WHEN account_health_score < 45 AND avg_seat_utilization < 0.30 
            THEN 'Service Action: Seat Adoption & Training Workshop'
        WHEN account_health_score BETWEEN 45 AND 69 
            THEN 'Proactive: Schedule Analyst Inquiry Session'
        ELSE 'Growth: Position Contract Expansion / Upsell'
    END AS recommended_action
FROM ScoredAccounts
ORDER BY account_health_score ASC, baseline_arr DESC;
