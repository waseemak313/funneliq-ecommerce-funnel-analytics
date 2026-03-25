-- ============================================================
-- FunnelIQ — 04_time_patterns.sql
-- Hourly, daily, and weekly conversion patterns
-- Identifies optimal timing for UX interventions
-- ============================================================

-- ── 1. Conversion rate by hour of day ────────────────────────
SELECT '── CONVERSION RATE BY HOUR OF DAY ──' AS section;

SELECT
    primary_hour                                        AS hour,
    COUNT(*)                                            AS sessions,
    SUM(converted)                                      AS purchases,
    ROUND(SUM(converted) * 100.0 / COUNT(*), 2)         AS conv_rate_pct,
    ROUND(AVG(avg_price), 2)                            AS avg_order_value,
    CASE
        WHEN ROUND(SUM(converted)*100.0/COUNT(*),2) >=
             (SELECT AVG(conv) FROM (
                SELECT ROUND(SUM(converted)*100.0/COUNT(*),2) AS conv
                FROM sessions GROUP BY primary_hour
             )) * 1.2
        THEN 'PEAK'
        WHEN ROUND(SUM(converted)*100.0/COUNT(*),2) <=
             (SELECT AVG(conv) FROM (
                SELECT ROUND(SUM(converted)*100.0/COUNT(*),2) AS conv
                FROM sessions GROUP BY primary_hour
             )) * 0.8
        THEN 'LOW'
        ELSE 'AVERAGE'
    END                                                 AS performance
FROM sessions
GROUP BY primary_hour
ORDER BY primary_hour;


-- ── 2. Conversion by day of week ─────────────────────────────
SELECT '' AS spacer;
SELECT '── CONVERSION RATE BY DAY OF WEEK ──' AS section;

SELECT
    day_of_week,
    COUNT(*)                                            AS sessions,
    SUM(converted)                                      AS purchases,
    ROUND(SUM(converted) * 100.0 / COUNT(*), 2)         AS conv_rate_pct,
    ROUND(AVG(avg_price), 2)                            AS avg_order_value,
    SUM(reached_cart)                                   AS cart_sessions,
    ROUND(SUM(reached_cart) * 100.0 / COUNT(*), 2)      AS cart_rate_pct
FROM sessions
GROUP BY day_of_week
ORDER BY
    CASE day_of_week
        WHEN 'Monday'    THEN 1 WHEN 'Tuesday'   THEN 2
        WHEN 'Wednesday' THEN 3 WHEN 'Thursday'  THEN 4
        WHEN 'Friday'    THEN 5 WHEN 'Saturday'  THEN 6
        WHEN 'Sunday'    THEN 7
    END;


-- ── 3. Peak hour × category conversion ───────────────────────
SELECT '' AS spacer;
SELECT '── PEAK HOURS BY CATEGORY ──' AS section;

SELECT
    top_category,
    COUNT(*)                                            AS total_sessions,
    -- Best converting hour
    (SELECT primary_hour FROM sessions s2
     WHERE s2.top_category = s.top_category
     GROUP BY primary_hour
     ORDER BY SUM(converted)*1.0/COUNT(*) DESC
     LIMIT 1)                                           AS best_hour,
    ROUND(MAX(SUM(converted)*1.0/COUNT(*)) OVER
          (PARTITION BY top_category) * 100, 2)         AS best_hour_conv_pct,
    ROUND(AVG(converted) * 100, 2)                      AS overall_conv_pct
FROM sessions s
WHERE top_category != 'unknown'
GROUP BY top_category
HAVING total_sessions > 5000
ORDER BY overall_conv_pct DESC
LIMIT 10;


-- ── 4. Session duration vs conversion ────────────────────────
SELECT '' AS spacer;
SELECT '── SESSION DURATION IMPACT ON CONVERSION ──' AS section;

SELECT
    CASE
        WHEN duration_minutes < 1   THEN 'Under 1 min'
        WHEN duration_minutes < 3   THEN '1-3 mins'
        WHEN duration_minutes < 5   THEN '3-5 mins'
        WHEN duration_minutes < 10  THEN '5-10 mins'
        WHEN duration_minutes < 30  THEN '10-30 mins'
        ELSE 'Over 30 mins'
    END                                                 AS session_duration,
    COUNT(*)                                            AS sessions,
    SUM(converted)                                      AS purchases,
    ROUND(SUM(converted) * 100.0 / COUNT(*), 2)         AS conv_rate_pct,
    ROUND(AVG(avg_price), 2)                            AS avg_price,
    ROUND(AVG(unique_products), 1)                      AS avg_products_viewed
FROM sessions
GROUP BY session_duration
ORDER BY
    CASE session_duration
        WHEN 'Under 1 min'  THEN 1
        WHEN '1-3 mins'     THEN 2
        WHEN '3-5 mins'     THEN 3
        WHEN '5-10 mins'    THEN 4
        WHEN '10-30 mins'   THEN 5
        ELSE 6
    END;


-- ── 5. Weekly trend ──────────────────────────────────────────
SELECT '' AS spacer;
SELECT '── WEEKLY CONVERSION TREND ──' AS section;

SELECT
    SUBSTR(session_start, 1, 10)                        AS week_start_date,
    COUNT(*)                                            AS sessions,
    SUM(converted)                                      AS purchases,
    ROUND(SUM(converted) * 100.0 / COUNT(*), 2)         AS conv_rate_pct,
    ROUND(AVG(avg_price), 2)                            AS avg_order_value,
    SUM(reached_cart)                                   AS cart_sessions
FROM sessions
GROUP BY SUBSTR(session_start, 1, 7),
         CAST(STRFTIME('%W', session_start) AS INTEGER)
ORDER BY week_start_date
LIMIT 5;


-- ── 6. UX intervention targeting summary ─────────────────────
SELECT '' AS spacer;
SELECT '── UX INTERVENTION PRIORITY TARGETS ──' AS section;

SELECT
    'High-price abandoned carts ($100+)'    AS segment,
    COUNT(*)                                AS sessions,
    ROUND(AVG(avg_price), 2)                AS avg_value,
    'Exit-intent discount popup'            AS recommended_intervention
FROM sessions
WHERE funnel_stage = 'abandoned_cart' AND avg_price >= 100

UNION ALL

SELECT
    'Short sessions < 2min that bounced',
    COUNT(*),
    ROUND(AVG(avg_price), 2),
    'Personalized recommendations widget'
FROM sessions
WHERE funnel_stage = 'bounced' AND duration_minutes < 2

UNION ALL

SELECT
    'Multi-product browsers who did not cart',
    COUNT(*),
    ROUND(AVG(avg_price), 2),
    'Wishlist / save-for-later prompt'
FROM sessions
WHERE funnel_stage = 'bounced' AND unique_products >= 5

UNION ALL

SELECT
    'Late-night sessions (11pm-2am)',
    COUNT(*),
    ROUND(AVG(avg_price), 2),
    'Urgency messaging + free shipping threshold'
FROM sessions
WHERE primary_hour >= 23 OR primary_hour <= 2;
