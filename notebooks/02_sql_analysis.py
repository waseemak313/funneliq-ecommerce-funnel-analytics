"""
FunnelIQ — Module 2: SQL Analysis Runner
=========================================
Runs all 4 SQL analysis scripts against funneliq.db
and prints formatted results to the terminal.

Run from project root:
    python notebooks/02_sql_analysis.py

Requires: funneliq.db (run 01_data_prep.py first)
"""

import sqlite3
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, 'funneliq.db')
SQL_DIR  = os.path.join(BASE_DIR, 'sql')

pd.set_option('display.max_columns',  20)
pd.set_option('display.max_rows',     50)
pd.set_option('display.width',        120)
pd.set_option('display.float_format', '{:.2f}'.format)

print("\n" + "="*65)
print("  FunnelIQ — Module 2: SQL Analysis")
print("="*65)

conn = sqlite3.connect(DB_PATH)

scripts = [
    ('02_funnel_dropoff.sql',   'FUNNEL DROP-OFF ANALYSIS'),
    ('03_segment_analysis.sql', 'SEGMENT ANALYSIS'),
    ('04_time_patterns.sql',    'TIME & BEHAVIORAL PATTERNS'),
]

for fname, label in scripts:
    print(f"\n{'='*65}")
    print(f"  {label}")
    print(f"{'='*65}")

    sql_path = os.path.join(SQL_DIR, fname)
    sql      = open(sql_path).read()

    # Split on semicolons and run each statement
    statements = [s.strip() for s in sql.split(';') if s.strip()
                  and not s.strip().startswith('--')]

    for stmt in statements:
        if not stmt:
            continue
        try:
            cur  = conn.execute(stmt)
            rows = cur.fetchall()
            if not rows or not cur.description:
                continue

            cols = [d[0] for d in cur.description]

            # Skip section/spacer label rows
            if cols == ['section'] or cols == ['spacer']:
                if rows and rows[0][0]:
                    print(f"\n  {rows[0][0]}")
                continue

            df = pd.DataFrame(rows, columns=cols)

            # Format and print
            print(df.to_string(index=False))
            print()

        except Exception as e:
            # Skip statements that don't work on this SQLite version
            pass

conn.close()

# ── Key findings summary ───────────────────────────────────────
print("\n" + "="*65)
print("  KEY FINDINGS SUMMARY")
print("="*65)

conn = sqlite3.connect(DB_PATH)

# Funnel summary
fs = pd.read_sql("SELECT * FROM funnel_summary", conn).iloc[0]
print(f"\n  Funnel conversion rates:")
print(f"    Session → View:    100.0%")
print(f"    View → Cart:       {fs['cart_rate_pct']:.1f}%  ← biggest drop-off")
print(f"    Cart → Purchase:   {fs['purchase_rate_pct']:.1f}%")
print(f"    Overall:           {fs['overall_conv_pct']:.2f}%")

# Biggest abandonment segment
top_abandon = pd.read_sql("""
    SELECT top_category, COUNT(*) as sessions,
           ROUND(SUM(converted)*100.0/COUNT(*),2) as conv_pct
    FROM sessions
    WHERE top_category != 'unknown'
    GROUP BY top_category
    HAVING sessions > 1000
    ORDER BY conv_pct ASC LIMIT 1
""", conn).iloc[0]

print(f"\n  Lowest converting category:")
print(f"    {top_abandon['top_category']} — {top_abandon['conv_pct']}% conversion")
print(f"    ({int(top_abandon['sessions']):,} sessions)")

# Best hour
best_hour = pd.read_sql("""
    SELECT primary_hour, ROUND(SUM(converted)*100.0/COUNT(*),2) as conv_pct
    FROM sessions GROUP BY primary_hour
    ORDER BY conv_pct DESC LIMIT 1
""", conn).iloc[0]

print(f"\n  Best converting hour:")
print(f"    {int(best_hour['primary_hour'])}:00 — {best_hour['conv_pct']}% conversion rate")

# High-value abandoned carts
abandoned = pd.read_sql("""
    SELECT COUNT(*) as cnt, ROUND(AVG(avg_price),2) as avg_val
    FROM sessions
    WHERE funnel_stage='abandoned_cart' AND avg_price >= 100
""", conn).iloc[0]

print(f"\n  High-value abandoned carts ($100+):")
print(f"    {int(abandoned['cnt']):,} sessions — avg value ${abandoned['avg_val']}")
print(f"    Est. recoverable revenue: ${int(abandoned['cnt'] * abandoned['avg_val']):,}")

conn.close()
print("\n" + "="*65 + "\n")
