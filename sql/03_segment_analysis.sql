-- ============================================================
-- FunnelIQ — 03_segment_analysis.sql
-- Conversion breakdown by category, brand, and price tier
-- Identifies highest-value optimization targets
-- ============================================================

-- ── 1. Conversion rate by top-level category ─────────────────
SELECT '── CONVERSION RATE BY CATEGORY ──' AS section;

SELECT
    top_category,
    COUNT(*)                                            AS total_sessions,
    SUM(reached_cart)                                   AS cart_sessions,
    SUM(converted)                                      AS purchases,
    ROUND(SUM(reached_cart) * 100.0 / COUNT(*), 2)      AS view_to_cart_pct,
    ROUND(SUM(converted) * 100.0 / COUNT(*), 2)         AS overall_conv_pct,
    ROUND(AVG(avg_price), 2)                            AS avg_price,
    CASE
        WHEN ROUND(SUM(converted)*100.0/COUNT(*),2) < 3
        THEN '🔴 HIGH PRIORITY'
        WHEN ROUND(SUM(converted)*100.0/COUNT(*),2) < 6
        THEN '🟡 MONITOR'
        ELSE '🟢 HEALTHY'
    END                                                 AS priority_flag
FROM sessions
WHERE top_category != 'unknown'
GROUP BY top_category
HAVING total_sessions > 1000
ORDER BY overall_conv_pct ASC
LIMIT 15;


-- ── 2. Top 15 brands by abandonment rate ─────────────────────
SELECT '' AS spacer;
SELECT '── TOP 15 BRANDS BY CART ABANDONMENT ──' AS section;

SELECT
    top_brand,
    COUNT(*)                                            AS total_sessions,
    SUM(reached_cart)                                   AS cart_sessions,
    SUM(CASE WHEN reached_cart=1 AND converted=0 THEN 1 ELSE 0 END)
                                                        AS abandoned,
    SUM(converted)                                      AS purchases,
    ROUND(SUM(converted) * 100.0 / COUNT(*), 2)         AS conv_rate_pct,
    ROUND(SUM(CASE WHEN reached_cart=1 AND converted=0 THEN 1.0 ELSE 0 END)
          / NULLIF(SUM(reached_cart), 0) * 100, 2)      AS cart_abandon_pct,
    ROUND(AVG(avg_price), 2)                            AS avg_price
FROM sessions
WHERE top_brand != 'unknown'
GROUP BY top_brand
HAVING total_sessions > 500
ORDER BY cart_abandon_pct DESC
LIMIT 15;


-- ── 3. Conversion by price tier ──────────────────────────────
SELECT '' AS spacer;
SELECT '── CONVERSION RATE BY PRICE TIER ──' AS section;

SELECT
    e.price_tier,
    COUNT(DISTINCT e.user_session)                      AS sessions,
    SUM(CASE WHEN e.event_type = 'cart'     THEN 1 ELSE 0 END) AS cart_events,
    SUM(CASE WHEN e.event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases,
    ROUND(SUM(CASE WHEN e.event_type='purchase' THEN 1.0 ELSE 0 END)
          / COUNT(DISTINCT e.user_session) * 100, 2)    AS conv_rate_pct,
    ROUND(AVG(e.price), 2)                              AS avg_price
FROM events e
WHERE e.price_tier IS NOT NULL
GROUP BY e.price_tier
ORDER BY
    CASE e.price_tier
        WHEN '<$20'      THEN 1
        WHEN '$20-50'    THEN 2
        WHEN '$50-100'   THEN 3
        WHEN '$100-250'  THEN 4
        WHEN '$250-500'  THEN 5
        WHEN '$500+'     THEN 6
    END;


-- ── 4. Category × price tier conversion heatmap ──────────────
SELECT '' AS spacer;
SELECT '── TOP CATEGORY × PRICE TIER CONVERSION ──' AS section;

SELECT
    s.top_category,
    ROUND(AVG(CASE WHEN s.avg_price < 20   THEN s.converted END) * 100, 1) AS 'under_20',
    ROUND(AVG(CASE WHEN s.avg_price BETWEEN 20 AND 50
                   THEN s.converted END) * 100, 1)                          AS '20_to_50',
    ROUND(AVG(CASE WHEN s.avg_price BETWEEN 50 AND 100
                   THEN s.converted END) * 100, 1)                          AS '50_to_100',
    ROUND(AVG(CASE WHEN s.avg_price BETWEEN 100 AND 250
                   THEN s.converted END) * 100, 1)                          AS '100_to_250',
    ROUND(AVG(CASE WHEN s.avg_price > 250
                   THEN s.converted END) * 100, 1)                          AS 'over_250',
    COUNT(*)                                                                 AS total_sessions
FROM sessions s
WHERE s.top_category != 'unknown'
GROUP BY s.top_category
HAVING total_sessions > 5000
ORDER BY total_sessions DESC
LIMIT 10;


-- ── 5. Multi-product vs single-product sessions ──────────────
SELECT '' AS spacer;
SELECT '── SESSION DEPTH IMPACT ON CONVERSION ──' AS section;

SELECT
    CASE
        WHEN unique_products = 1  THEN '1 product viewed'
        WHEN unique_products <= 3 THEN '2-3 products'
        WHEN unique_products <= 5 THEN '4-5 products'
        WHEN unique_products <= 10 THEN '6-10 products'
        ELSE '10+ products'
    END                                                 AS browse_depth,
    COUNT(*)                                            AS sessions,
    ROUND(AVG(converted) * 100, 2)                      AS conv_rate_pct,
    ROUND(AVG(avg_price), 2)                            AS avg_price,
    ROUND(AVG(duration_minutes), 1)                     AS avg_duration_min
FROM sessions
GROUP BY browse_depth
ORDER BY
    CASE browse_depth
        WHEN '1 product viewed' THEN 1
        WHEN '2-3 products'     THEN 2
        WHEN '4-5 products'     THEN 3
        WHEN '6-10 products'    THEN 4
        ELSE 5
    END;


-- ── 6. Top converting category-brand combos ──────────────────
SELECT '' AS spacer;
SELECT '── TOP 10 CATEGORY-BRAND COMBOS BY CONVERSION ──' AS section;

SELECT
    top_category || ' / ' || top_brand                  AS segment,
    COUNT(*)                                            AS sessions,
    SUM(converted)                                      AS purchases,
    ROUND(AVG(converted) * 100, 2)                      AS conv_rate_pct,
    ROUND(AVG(avg_price), 2)                            AS avg_price
FROM sessions
WHERE top_category != 'unknown'
  AND top_brand     != 'unknown'
GROUP BY top_category, top_brand
HAVING sessions > 200
ORDER BY conv_rate_pct DESC
LIMIT 10;
