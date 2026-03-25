-- ============================================================
-- FunnelIQ — 02_funnel_dropoff.sql
-- Stage-by-stage funnel drop-off analysis
-- Core finding: where exactly are users leaving?
-- ============================================================

-- ── 1. Overall funnel waterfall ───────────────────────────────
SELECT '── FUNNEL WATERFALL ──' AS section;

SELECT
    'Session start'         AS stage,
    total_sessions          AS users,
    100.0                   AS pct_of_total,
    0.0                     AS drop_off_pct
FROM funnel_summary

UNION ALL

SELECT
    'Viewed product',
    sessions_viewed,
    ROUND(sessions_viewed * 100.0 / total_sessions, 2),
    ROUND((total_sessions - sessions_viewed) * 100.0 / total_sessions, 2)
FROM funnel_summary

UNION ALL

SELECT
    'Added to cart',
    sessions_carted,
    ROUND(sessions_carted * 100.0 / total_sessions, 2),
    ROUND((sessions_viewed - sessions_carted) * 100.0 / total_sessions, 2)
FROM funnel_summary

UNION ALL

SELECT
    'Completed purchase',
    sessions_purchased,
    ROUND(sessions_purchased * 100.0 / total_sessions, 2),
    ROUND((sessions_carted - sessions_purchased) * 100.0 / total_sessions, 2)
FROM funnel_summary;


-- ── 2. Drop-off volume and revenue impact ────────────────────
SELECT '' AS spacer;
SELECT '── DROP-OFF VOLUME & REVENUE IMPACT ──' AS section;

SELECT
    funnel_stage,
    COUNT(*)                                            AS sessions,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2)  AS pct_of_total,
    ROUND(AVG(avg_price), 2)                            AS avg_session_price,
    ROUND(AVG(unique_products), 1)                      AS avg_products_browsed,
    ROUND(AVG(duration_minutes), 1)                     AS avg_session_minutes,
    -- Estimated lost revenue (abandoned_cart × avg cart value)
    CASE
        WHEN funnel_stage = 'abandoned_cart'
        THEN ROUND(COUNT(*) * AVG(avg_price), 0)
        ELSE NULL
    END                                                 AS est_lost_revenue_usd
FROM sessions
GROUP BY funnel_stage
ORDER BY sessions DESC;


-- ── 3. Cart abandonment deep-dive ────────────────────────────
SELECT '' AS spacer;
SELECT '── CART ABANDONMENT ANALYSIS ──' AS section;

SELECT
    'Total sessions that reached cart'  AS metric,
    COUNT(*)                            AS value
FROM sessions WHERE reached_cart = 1

UNION ALL

SELECT
    'Cart sessions that purchased',
    COUNT(*)
FROM sessions WHERE reached_cart = 1 AND reached_purchase = 1

UNION ALL

SELECT
    'Cart sessions that abandoned',
    COUNT(*)
FROM sessions WHERE reached_cart = 1 AND reached_purchase = 0

UNION ALL

SELECT
    'Cart-to-purchase rate (%)',
    ROUND(SUM(CASE WHEN reached_purchase = 1 THEN 1.0 ELSE 0 END)
          / COUNT(*) * 100, 2)
FROM sessions WHERE reached_cart = 1;


-- ── 4. Bounce analysis by session depth ──────────────────────
SELECT '' AS spacer;
SELECT '── BOUNCE RATE BY SESSION DEPTH ──' AS section;

SELECT
    CASE
        WHEN total_events = 1  THEN '1 event (instant bounce)'
        WHEN total_events <= 3 THEN '2-3 events'
        WHEN total_events <= 5 THEN '4-5 events'
        WHEN total_events <= 10 THEN '6-10 events'
        ELSE '10+ events'
    END                                                 AS session_depth,
    COUNT(*)                                            AS sessions,
    SUM(CASE WHEN funnel_stage = 'bounced' THEN 1 ELSE 0 END)
                                                        AS bounced,
    SUM(CASE WHEN funnel_stage = 'purchased' THEN 1 ELSE 0 END)
                                                        AS purchased,
    ROUND(SUM(CASE WHEN funnel_stage = 'purchased' THEN 1.0 ELSE 0 END)
          / COUNT(*) * 100, 2)                          AS conv_rate_pct
FROM sessions
GROUP BY session_depth
ORDER BY
    CASE session_depth
        WHEN '1 event (instant bounce)' THEN 1
        WHEN '2-3 events'  THEN 2
        WHEN '4-5 events'  THEN 3
        WHEN '6-10 events' THEN 4
        ELSE 5
    END;


-- ── 5. Price sensitivity at drop-off ─────────────────────────
SELECT '' AS spacer;
SELECT '── PRICE SENSITIVITY AT EACH FUNNEL STAGE ──' AS section;

SELECT
    funnel_stage,
    ROUND(AVG(avg_price), 2)        AS avg_price,
    ROUND(AVG(max_price), 2)        AS avg_max_price_seen,
    ROUND(MIN(avg_price), 2)        AS min_avg_price,
    ROUND(MAX(avg_price), 2)        AS max_avg_price,
    COUNT(*)                        AS sessions
FROM sessions
GROUP BY funnel_stage
ORDER BY avg_price DESC;
