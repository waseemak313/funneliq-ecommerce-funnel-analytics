"""
FunnelIQ — Module 1: Data Preparation & Funnel Construction
============================================================
Loads the REES46 eCommerce behavior dataset (2019-Oct.csv),
cleans it, engineers session-level funnel features, and
loads everything into a SQLite database for SQL analysis.

Dataset: https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store
File:    data/2019-Oct.csv (~2.3M rows)

Columns in raw data:
  event_time      : UTC timestamp of the event
  event_type      : view / cart / purchase
  product_id      : unique product ID
  category_id     : category ID
  category_code   : human-readable category (e.g. electronics.smartphone)
  brand           : brand name
  price           : product price (USD)
  user_id         : unique user ID
  user_session    : session ID (resets after long pause)

Run from project root:
    python notebooks/01_data_prep.py

Output:
    funneliq.db   — SQLite database with 4 tables
"""

import pandas as pd
import numpy as np
import sqlite3
import os
import warnings
warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', '2019-Oct.csv')
DB_PATH   = os.path.join(BASE_DIR, 'funneliq.db')

print("\n" + "="*60)
print("  FunnelIQ — Module 1: Data Preparation")
print("="*60)

# ── Step 1: Load raw data ──────────────────────────────────────────────────
print("\n  Step 1: Loading raw data...")
df = pd.read_csv(DATA_PATH, parse_dates=['event_time'])
print(f"  ✓ Loaded {len(df):,} rows × {len(df.columns)} columns")
print(f"  ✓ Date range: {df['event_time'].min().date()} → {df['event_time'].max().date()}")
print(f"  ✓ Event types: {df['event_type'].value_counts().to_dict()}")

# ── Step 2: Clean ──────────────────────────────────────────────────────────
print("\n  Step 2: Cleaning...")

raw_len = len(df)

# Drop rows missing critical fields
df = df.dropna(subset=['user_id', 'user_session', 'event_type', 'price'])

# Remove negative or zero prices
df = df[df['price'] > 0]

# Standardize strings
df['brand']         = df['brand'].str.lower().str.strip().fillna('unknown')
df['category_code'] = df['category_code'].fillna('unknown')

# Extract top-level category (e.g. 'electronics.smartphone' → 'electronics')
df['category_top'] = df['category_code'].apply(
    lambda x: x.split('.')[0] if x != 'unknown' else 'unknown'
)

# Extract sub-category
df['category_sub'] = df['category_code'].apply(
    lambda x: x.split('.')[1] if (x != 'unknown' and len(x.split('.')) > 1) else 'other'
)

# Time features
df['hour']        = df['event_time'].dt.hour
df['day_of_week'] = df['event_time'].dt.day_name()
df['date']        = df['event_time'].dt.date.astype(str)
df['week']        = df['event_time'].dt.isocalendar().week.astype(int)

# Price tier buckets
df['price_tier'] = pd.cut(
    df['price'],
    bins=[0, 20, 50, 100, 250, 500, 99999],
    labels=['<$20', '$20-50', '$50-100', '$100-250', '$250-500', '$500+']
)

cleaned_len = len(df)
print(f"  ✓ Removed {raw_len - cleaned_len:,} invalid rows")
print(f"  ✓ Clean dataset: {cleaned_len:,} rows")
print(f"  ✓ Unique users:    {df['user_id'].nunique():,}")
print(f"  ✓ Unique sessions: {df['user_session'].nunique():,}")
print(f"  ✓ Unique products: {df['product_id'].nunique():,}")

# ── Step 3: Build session-level funnel ─────────────────────────────────────
print("\n  Step 3: Building session-level funnel...")

# For each session, track which stages they reached
session_events = df.groupby('user_session')['event_type'].apply(set).reset_index()
session_events.columns = ['user_session', 'event_set']

session_events['reached_view']     = session_events['event_set'].apply(lambda x: 'view'     in x)
session_events['reached_cart']     = session_events['event_set'].apply(lambda x: 'cart'     in x)
session_events['reached_purchase'] = session_events['event_set'].apply(lambda x: 'purchase' in x)

# Session-level aggregates
session_agg = df.groupby('user_session').agg(
    user_id          =('user_id',    'first'),
    session_start    =('event_time', 'min'),
    session_end      =('event_time', 'max'),
    total_events     =('event_type', 'count'),
    n_views          =('event_type', lambda x: (x == 'view').sum()),
    n_carts          =('event_type', lambda x: (x == 'cart').sum()),
    n_purchases      =('event_type', lambda x: (x == 'purchase').sum()),
    unique_products  =('product_id', 'nunique'),
    avg_price        =('price',      'mean'),
    max_price        =('price',      'max'),
    min_price        =('price',      'min'),
    top_category     =('category_top', lambda x: x.value_counts().idxmax()),
    top_brand        =('brand',      lambda x: x.value_counts().idxmax()),
    primary_hour     =('hour',       'first'),
    day_of_week      =('day_of_week','first'),
).reset_index()

# Session duration in minutes
session_agg['duration_minutes'] = (
    (session_agg['session_end'] - session_agg['session_start'])
    .dt.total_seconds() / 60
).round(2)

# Merge funnel flags
sessions = session_agg.merge(session_events[['user_session','reached_view',
                                              'reached_cart','reached_purchase']],
                              on='user_session')

# Funnel stage label
def funnel_stage(row):
    if row['reached_purchase']: return 'purchased'
    if row['reached_cart']:     return 'abandoned_cart'
    return 'bounced'

sessions['funnel_stage'] = sessions.apply(funnel_stage, axis=1)

# Converted flag (for ML)
sessions['converted'] = (sessions['funnel_stage'] == 'purchased').astype(int)

# Cart-to-purchase flag (only for sessions that reached cart)
sessions['cart_converted'] = (
    (sessions['reached_cart']) & (sessions['reached_purchase'])
).astype(int)

print(f"  ✓ {len(sessions):,} sessions built")
print(f"  ✓ Funnel stages:")
stage_counts = sessions['funnel_stage'].value_counts()
for stage, count in stage_counts.items():
    pct = count / len(sessions) * 100
    print(f"      {stage:<20}: {count:>7,}  ({pct:.1f}%)")

# ── Step 4: Compute funnel metrics ─────────────────────────────────────────
print("\n  Step 4: Computing funnel metrics...")

total_sessions  = len(sessions)
viewed          = sessions['reached_view'].sum()
carted          = sessions['reached_cart'].sum()
purchased       = sessions['reached_purchase'].sum()

view_rate       = viewed    / total_sessions * 100
cart_rate       = carted    / viewed         * 100
purchase_rate   = purchased / carted         * 100
overall_conv    = purchased / total_sessions * 100

print(f"  ✓ Funnel conversion rates:")
print(f"      Session → View:     {view_rate:.1f}%")
print(f"      View   → Cart:      {cart_rate:.1f}%  ← biggest drop-off")
print(f"      Cart   → Purchase:  {purchase_rate:.1f}%")
print(f"      Overall conversion: {overall_conv:.1f}%")

# ── Step 5: Build product-level table ──────────────────────────────────────
print("\n  Step 5: Building product-level summary...")

products = df.groupby('product_id').agg(
    category_code  =('category_code',  'first'),
    category_top   =('category_top',   'first'),
    category_sub   =('category_sub',   'first'),
    brand          =('brand',          'first'),
    avg_price      =('price',          'mean'),
    n_views        =('event_type', lambda x: (x == 'view').sum()),
    n_carts        =('event_type', lambda x: (x == 'cart').sum()),
    n_purchases    =('event_type', lambda x: (x == 'purchase').sum()),
).reset_index()

products['view_to_cart_rate']    = (products['n_carts']    / products['n_views'].replace(0,np.nan) * 100).round(2)
products['cart_to_purchase_rate']= (products['n_purchases']/ products['n_carts'].replace(0,np.nan) * 100).round(2)
products['avg_price']            = products['avg_price'].round(2)

print(f"  ✓ {len(products):,} unique products profiled")

# ── Step 6: Load to SQLite ─────────────────────────────────────────────────
print("\n  Step 6: Loading to SQLite...")

conn = sqlite3.connect(DB_PATH)

# Raw events (sample 500K for performance — still statistically representative)
print("    Loading events table (sampling 500K rows)...")
df_sample = df.sample(n=min(500_000, len(df)), random_state=42)
df_sample.to_sql('events', conn, if_exists='replace', index=False,
                 chunksize=10_000)
print(f"    ✓ events: {len(df_sample):,} rows")

# Sessions
sessions.to_sql('sessions', conn, if_exists='replace', index=False)
print(f"    ✓ sessions: {len(sessions):,} rows")

# Products
products.to_sql('products', conn, if_exists='replace', index=False)
print(f"    ✓ products: {len(products):,} rows")

# Funnel summary (pre-aggregated for fast dashboard queries)
funnel_summary = pd.DataFrame([{
    'total_sessions':   int(total_sessions),
    'sessions_viewed':  int(viewed),
    'sessions_carted':  int(carted),
    'sessions_purchased': int(purchased),
    'view_rate_pct':    round(view_rate, 2),
    'cart_rate_pct':    round(cart_rate, 2),
    'purchase_rate_pct':round(purchase_rate, 2),
    'overall_conv_pct': round(overall_conv, 2),
}])
funnel_summary.to_sql('funnel_summary', conn, if_exists='replace', index=False)
print(f"    ✓ funnel_summary: 1 row")

conn.close()

# ── Summary ────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  DATASET SUMMARY")
print("="*60)
print(f"  Raw events loaded    : {cleaned_len:,}")
print(f"  Sessions built       : {total_sessions:,}")
print(f"  Unique users         : {df['user_id'].nunique():,}")
print(f"  Unique products      : {len(products):,}")
print(f"  Overall conversion   : {overall_conv:.2f}%")
print(f"  Biggest drop-off     : View → Cart ({100-cart_rate:.1f}% fall off)")
print(f"  Database saved to    : funneliq.db")
print("="*60 + "\n")
