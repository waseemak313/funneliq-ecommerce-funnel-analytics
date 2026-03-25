-- ============================================================
-- FunnelIQ — 01_schema.sql
-- Table definitions for the FunnelIQ SQLite database
-- ============================================================

-- ── events (500K sampled from 42M raw) ───────────────────────
CREATE TABLE IF NOT EXISTS events (
    event_time      TEXT,
    event_type      TEXT,       -- view / cart / purchase
    product_id      INTEGER,
    category_id     INTEGER,
    category_code   TEXT,
    brand           TEXT,
    price           REAL,
    user_id         INTEGER,
    user_session    TEXT,
    hour            INTEGER,
    day_of_week     TEXT,
    date            TEXT,
    week            INTEGER,
    price_tier      TEXT,
    category_top    TEXT,
    category_sub    TEXT
);

-- ── sessions (9.2M — full dataset) ───────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    user_session        TEXT PRIMARY KEY,
    user_id             INTEGER,
    session_start       TEXT,
    session_end         TEXT,
    total_events        INTEGER,
    n_views             INTEGER,
    n_carts             INTEGER,
    n_purchases         INTEGER,
    unique_products     INTEGER,
    avg_price           REAL,
    max_price           REAL,
    min_price           REAL,
    top_category        TEXT,
    top_brand           TEXT,
    primary_hour        INTEGER,
    day_of_week         TEXT,
    duration_minutes    REAL,
    reached_view        INTEGER,    -- 0/1
    reached_cart        INTEGER,    -- 0/1
    reached_purchase    INTEGER,    -- 0/1
    funnel_stage        TEXT,       -- bounced / abandoned_cart / purchased
    converted           INTEGER,    -- 0/1
    cart_converted      INTEGER     -- 0/1
);

-- ── products (165K unique products) ──────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id              INTEGER PRIMARY KEY,
    category_code           TEXT,
    category_top            TEXT,
    category_sub            TEXT,
    brand                   TEXT,
    avg_price               REAL,
    n_views                 INTEGER,
    n_carts                 INTEGER,
    n_purchases             INTEGER,
    view_to_cart_rate       REAL,
    cart_to_purchase_rate   REAL
);

-- ── funnel_summary (pre-aggregated KPIs) ─────────────────────
CREATE TABLE IF NOT EXISTS funnel_summary (
    total_sessions      INTEGER,
    sessions_viewed     INTEGER,
    sessions_carted     INTEGER,
    sessions_purchased  INTEGER,
    view_rate_pct       REAL,
    cart_rate_pct       REAL,
    purchase_rate_pct   REAL,
    overall_conv_pct    REAL
);

-- ── Indexes ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_sessions_stage    ON sessions(funnel_stage);
CREATE INDEX IF NOT EXISTS idx_sessions_category ON sessions(top_category);
CREATE INDEX IF NOT EXISTS idx_sessions_brand    ON sessions(top_brand);
CREATE INDEX IF NOT EXISTS idx_sessions_hour     ON sessions(primary_hour);
CREATE INDEX IF NOT EXISTS idx_sessions_dow      ON sessions(day_of_week);
CREATE INDEX IF NOT EXISTS idx_events_type       ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_category   ON events(category_top);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_top);

SELECT 'Schema ready.' AS status;
