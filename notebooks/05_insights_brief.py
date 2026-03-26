"""
FunnelIQ — Module 5: Executive Insights Brief (PDF)
=====================================================
Generates a 3-page professional PDF report with inline
charts summarizing all findings from the FunnelIQ project.

Page 1: Cover + executive summary + KPI scorecard
Page 2: Key findings with inline charts
Page 3: ML model results + recommendations + impact table

Run from project root:
    python notebooks/05_insights_brief.py

Requires: outputs/ folder with charts from modules 3 and 4
Output:   outputs/FunnelIQ_Insights_Brief.pdf
"""

import os
import io
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
warnings.filterwarnings('ignore')

from reportlab.lib.pagesizes    import letter
from reportlab.lib.units        import inch
from reportlab.lib              import colors
from reportlab.lib.styles       import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums        import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus         import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image, KeepTogether
)
from reportlab.platypus.flowables import Flowable

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
PDF_PATH   = os.path.join(OUTPUT_DIR, 'FunnelIQ_Insights_Brief.pdf')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Brand colors ───────────────────────────────────────────────────────────
NAVY      = colors.HexColor('#1B2A4A')
BLUE      = colors.HexColor('#2D6BE4')
TEAL      = colors.HexColor('#17A98E')
AMBER     = colors.HexColor('#F5A623')
RED       = colors.HexColor('#E8402A')
GREEN     = colors.HexColor('#2E9E57')
LIGHT_BG  = colors.HexColor('#F0F4F8')
MID_GRAY  = colors.HexColor('#6B7280')
DARK_GRAY = colors.HexColor('#374151')
WHITE     = colors.white

print("\n" + "="*60)
print("  FunnelIQ — Module 5: Insights Brief")
print("="*60)

# ── Real numbers from our analysis ────────────────────────────────────────
STATS = {
    'raw_events':       '42,380,089',
    'sessions':         '9,239,402',
    'users':            '3,021,435',
    'products':         '165,647',
    'overall_conv':     '6.81%',
    'view_to_cart':     '6.2%',
    'drop_off':         '93.8%',
    'abandoned_carts':  '281,185',
    'lost_revenue':     '$94,216,419',
    'best_hour':        '9am',
    'best_conv_hour':   '8.57%',
    'worst_category':   'apparel',
    'worst_cat_conv':   '2.40%',
    'best_category':    'electronics',
    'best_cat_conv':    '8.88%',
    'top_combo':        'electronics / saturn',
    'top_combo_conv':   '17.4%',
    'session_dur_low':  '1.1%',
    'session_dur_high': '13.7%',
    'lr_auc':           '1.0000',
    'xgb_auc':          '0.9997',
    'model_accuracy':   '99%',
    'sessions_flagged': '1,689,163',
    'recoverable':      '236,482',
    'revenue_recovery': '$72,600,225',
    'top_shap_1':       'Total events',
    'top_shap_2':       'View count',
    'top_shap_3':       'Events per product',
}

# ── Helper: matplotlib fig → ReportLab Image ──────────────────────────────
def fig_to_img(fig, w_in, h_in):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150,
                bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=w_in*inch, height=h_in*inch)

# ── Mini chart builders ────────────────────────────────────────────────────
def make_funnel_chart():
    stages = ['Session\nStart', 'Viewed\nProduct',
              'Added\nto Cart', 'Purchased']
    vals   = [9239402, 9237562, 573019, 629560]
    pcts   = [100, 99.98, 6.2, 6.81]
    clrs   = ['#1B2A4A', '#2D6BE4', '#F5A623', '#2E9E57']

    fig, ax = plt.subplots(figsize=(4.5, 2.8))
    bars = ax.bar(stages, vals, color=clrs, edgecolor='white',
                  linewidth=0.5, width=0.55)
    for bar, v, p in zip(bars, vals, pcts):
        ax.text(bar.get_x()+bar.get_width()/2,
                bar.get_height()+80000,
                f'{v/1e6:.1f}M\n({p:.1f}%)',
                ha='center', fontsize=7, fontweight='bold')
    ax.annotate('−93.8%', xy=(1.5, 3e6),
                fontsize=8.5, color='#E8402A', fontweight='bold',
                ha='center',
                bbox=dict(boxstyle='round,pad=0.2', fc='white',
                          ec='#E8402A', alpha=0.9))
    ax.set_ylabel('Sessions', fontsize=8)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x,_: f'{x/1e6:.1f}M'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    fig.tight_layout()
    return fig_to_img(fig, 3.4, 2.2)

def make_category_chart():
    cats  = ['sport','apparel','furniture','country_yard',
             'kids','accessories','auto','computers',
             'appliances','electronics']
    convs = [2.91, 2.40, 3.15, 3.19, 4.02,
             4.03, 4.81, 5.39, 7.17, 8.88]
    clrs  = ['#E8402A' if v < 3 else
             '#F5A623' if v < 6 else '#2E9E57'
             for v in convs]

    fig, ax = plt.subplots(figsize=(4.5, 2.8))
    ax.barh(cats, convs, color=clrs, edgecolor='white',
            linewidth=0.5, height=0.65)
    ax.axvline(6.81, color='#1B2A4A', linestyle='--',
               linewidth=1.2)
    ax.text(7.0, -0.5, 'Avg\n6.81%', fontsize=6.5,
            color='#1B2A4A', va='bottom')
    for i, v in enumerate(convs):
        ax.text(v+0.1, i, f'{v:.1f}%',
                va='center', fontsize=7, fontweight='bold')
    ax.set_xlabel('Conversion Rate (%)', fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    fig.tight_layout()
    return fig_to_img(fig, 3.4, 2.2)

def make_duration_chart():
    labels = ['<1 min','1-3 min','3-5 min',
              '5-10 min','10-30 min','30+ min']
    vals   = [1.1, 11.2, 13.7, 13.3, 12.8, 10.7]
    clrs   = ['#E8402A','#F5A623','#2E9E57',
              '#2D6BE4','#1B2A4A','#7B5EA7']

    fig, ax = plt.subplots(figsize=(4.5, 2.8))
    bars = ax.bar(labels, vals, color=clrs,
                  edgecolor='white', linewidth=0.5, width=0.6)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2,
                v+0.2, f'{v}%',
                ha='center', fontsize=7.5, fontweight='bold')
    ax.set_ylabel('Conversion Rate (%)', fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.tick_params(axis='x', labelsize=7, rotation=15)
    fig.tight_layout()
    return fig_to_img(fig, 3.4, 2.2)

def make_shap_chart():
    features = ['Cart ratio','Is weekend','Long session',
                'Multi-product','High price','Hour bucket',
                'Price range','Unique products',
                'Events/product','Session duration',
                'View count','Total events']
    vals     = [0.12, 0.15, 0.18, 0.22, 0.28,
                0.35, 0.52, 0.70, 4.32, 1.40,
                5.44, 6.62]
    clrs     = ['#2D6BE4']*9 + ['#F5A623','#F5A623','#E8402A']

    fig, ax = plt.subplots(figsize=(4.5, 2.8))
    ax.barh(features, vals, color=clrs,
            edgecolor='white', linewidth=0.5, height=0.65)
    ax.set_xlabel('Mean |SHAP value|', fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')
    ax.tick_params(axis='y', labelsize=7)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    fig.tight_layout()
    return fig_to_img(fig, 3.4, 2.2)

print("  Rendering inline charts...")
chart_funnel   = make_funnel_chart()
chart_category = make_category_chart()
chart_duration = make_duration_chart()
chart_shap     = make_shap_chart()
print("  ✓ 4 inline charts ready")

# ── Styles ─────────────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

sty = {
    'h_name':   S('HN', fontSize=24, textColor=WHITE,
                  fontName='Helvetica-Bold', leading=28),
    'h_sub':    S('HS', fontSize=9, textColor=colors.HexColor('#B8D4E8'),
                  fontName='Helvetica', leading=13),
    'section':  S('SEC', fontSize=11, textColor=NAVY,
                  fontName='Helvetica-Bold', spaceBefore=8,
                  spaceAfter=4, leading=14),
    'body':     S('BD', fontSize=8.5, textColor=DARK_GRAY,
                  fontName='Helvetica', leading=13,
                  spaceAfter=4, alignment=TA_JUSTIFY),
    'bullet':   S('BUL', fontSize=8.5, textColor=DARK_GRAY,
                  fontName='Helvetica', leading=13,
                  leftIndent=10, spaceAfter=3),
    'caption':  S('CAP', fontSize=7.5, textColor=MID_GRAY,
                  fontName='Helvetica-Oblique',
                  alignment=TA_CENTER, spaceAfter=4),
    'kpi_num':  S('KN', fontSize=20, textColor=NAVY,
                  fontName='Helvetica-Bold', leading=22,
                  alignment=TA_CENTER),
    'kpi_lab':  S('KL', fontSize=7, textColor=MID_GRAY,
                  fontName='Helvetica', leading=10,
                  alignment=TA_CENTER),
    'footer':   S('FT', fontSize=7, textColor=MID_GRAY,
                  fontName='Helvetica', alignment=TA_CENTER),
    'find_hd':  S('FH', fontSize=9.5, textColor=NAVY,
                  fontName='Helvetica-Bold', leading=12,
                  spaceBefore=4, spaceAfter=2),
    'find_bd':  S('FB', fontSize=8.2, textColor=DARK_GRAY,
                  fontName='Helvetica', leading=12,
                  spaceAfter=3, alignment=TA_JUSTIFY),
    'rec_body': S('RB', fontSize=8.2, textColor=DARK_GRAY,
                  fontName='Helvetica', leading=12, spaceAfter=2),
    'impact':   S('IMP', fontSize=8, textColor=colors.HexColor('#065F46'),
                  fontName='Helvetica-Bold', leading=11),
    'p2_head':  S('P2H', fontSize=14, textColor=WHITE,
                  fontName='Helvetica-Bold', leading=17),
    'p2_sub':   S('P2S', fontSize=8, textColor=colors.HexColor('#B8D4E8'),
                  fontName='Helvetica', alignment=TA_RIGHT, leading=11),
}

# ── Document setup ─────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    PDF_PATH,
    pagesize=letter,
    leftMargin=0.6*inch, rightMargin=0.6*inch,
    topMargin=0.5*inch,  bottomMargin=0.5*inch,
    title='FunnelIQ — E-Commerce Conversion Funnel Analytics Brief',
    author='FunnelIQ Analytics',
)
W = letter[0] - 1.2*inch
story = []

# ══════════════════════════════════════════════════════════════════════════
# PAGE 1 — Cover + Executive Summary + KPI Scorecard
# ══════════════════════════════════════════════════════════════════════════

# Header banner
hdr = Table([[
    Paragraph('FunnelIQ', sty['h_name']),
    Paragraph(
        'Prepared by: Waseem Akram<br/>'
        'Dataset: REES46 eCommerce Behavior Data<br/>'
        'Period: October 2019  |  42M events  |  3M users',
        sty['h_sub']
    ),
]], colWidths=[W*0.45, W*0.55])
hdr.setStyle(TableStyle([
    ('BACKGROUND',   (0,0), (-1,-1), NAVY),
    ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING',  (0,0), (-1,-1), 14),
    ('RIGHTPADDING', (0,0), (-1,-1), 14),
    ('TOPPADDING',   (0,0), (-1,-1), 14),
    ('BOTTOMPADDING',(0,0), (-1,-1), 14),
    ('ROUNDEDCORNERS', [6]),
]))
story.append(hdr)
story.append(Spacer(1, 0.15*inch))

story.append(Paragraph(
    'E-Commerce Conversion Funnel Optimization — Analytics Brief',
    S('SUB', fontSize=10, textColor=BLUE, fontName='Helvetica-Bold',
      leading=13, spaceAfter=2)
))
story.append(HRFlowable(width=W, thickness=1.5, color=BLUE,
                         spaceAfter=8, spaceBefore=2))

# KPI tiles
def kpi(num, label, color=NAVY):
    return [
        Paragraph(num, S('kn2', fontSize=18, textColor=color,
                         fontName='Helvetica-Bold', leading=20,
                         alignment=TA_CENTER)),
        Paragraph(label, S('kl2', fontSize=6.5, textColor=MID_GRAY,
                           fontName='Helvetica', leading=9,
                           alignment=TA_CENTER)),
    ]

kpi_rows = [[
    kpi('42.4M',  'Raw events\nprocessed'),
    kpi('9.2M',   'Sessions\nanalyzed'),
    kpi('3.0M',   'Unique\nusers'),
    kpi('6.81%',  'Overall\nconversion', BLUE),
    kpi('93.8%',  'View→Cart\ndrop-off', RED),
    kpi('0.9997', 'XGBoost\nROC-AUC', GREEN),
]]
flat_kpi = [
    [kpi_rows[0][i][0] for i in range(6)],
    [kpi_rows[0][i][1] for i in range(6)],
]
kpi_tbl = Table(flat_kpi, colWidths=[W/6]*6)
kpi_tbl.setStyle(TableStyle([
    ('BACKGROUND',   (0,0), (-1,-1), LIGHT_BG),
    ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
    ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING',   (0,0), (-1,-1), 7),
    ('BOTTOMPADDING',(0,0), (-1,-1), 6),
    ('LINEAFTER',    (0,0), (4,1),   0.5, colors.HexColor('#D1D5DB')),
    ('ROUNDEDCORNERS', [4]),
]))
story.append(kpi_tbl)
story.append(Spacer(1, 0.12*inch))

# Executive summary
story.append(Paragraph('Executive Summary', sty['section']))
story.append(Paragraph(
    'This brief presents the findings of a comprehensive funnel analytics study '
    'on 42 million real clickstream events from a multi-category e-commerce store. '
    'The analysis spans the full analytical stack — data engineering, SQL funnel '
    'analysis, exploratory visualization, and a predictive machine learning model '
    'to identify high-risk abandonment sessions in real time. '
    'The core finding is that <b>93.8% of sessions that view a product never add '
    'to cart</b> — the single largest conversion leak — representing an estimated '
    '<b>$94M in annual lost revenue</b>. '
    'Three targeted UX interventions, supported by model evidence, are projected '
    'to recover <b>$72.6M</b> through a 14% conversion uplift on high-risk sessions.',
    sty['body']
))

# Methodology
story.append(Paragraph('Methodology', sty['section']))
for item in [
    '<b>Data:</b> REES46 real clickstream data — 42M events, 9.2M sessions, '
    '3M users, 165K products (October 2019). No synthetic data used.',
    '<b>SQL Analysis:</b> SQLite queries across 4 analytical scripts covering '
    'funnel drop-off, segment conversion, price tier analysis, and time patterns.',
    '<b>ML Model:</b> XGBoost classifier trained on 7.4M sessions with 17 '
    'behavioral features. SHAP values used for explainability. '
    'ROC-AUC of 0.9997 on 1.8M test sessions.',
    '<b>Tools:</b> Python (pandas, numpy, matplotlib, scikit-learn, XGBoost, '
    'SHAP) · SQL (SQLite) · reportlab (PDF generation)',
]:
    story.append(Paragraph(f'&#8226;  {item}', sty['bullet']))

story.append(Spacer(1, 0.06*inch))
story.append(HRFlowable(width=W, thickness=0.5,
                         color=colors.HexColor('#E5E7EB'), spaceAfter=0))
story.append(Spacer(1, 0.04*inch))

# Footer page 1
story.append(Paragraph(
    'FunnelIQ Analytics  |  '
    'github.com/waseemak313/funneliq-ecommerce-funnel-analytics  |  '
    'Data: REES46 via Kaggle  |  Page 1 of 3',
    sty['footer']
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# PAGE 2 — Key Findings with Charts
# ══════════════════════════════════════════════════════════════════════════

p2_hdr = Table([[
    Paragraph('Key Findings', sty['p2_head']),
    Paragraph('FunnelIQ Analytics  |  Oct 2019', sty['p2_sub']),
]], colWidths=[W*0.6, W*0.4])
p2_hdr.setStyle(TableStyle([
    ('BACKGROUND',   (0,0), (-1,-1), NAVY),
    ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING',  (0,0), (-1,-1), 14),
    ('RIGHTPADDING', (0,0), (-1,-1), 14),
    ('TOPPADDING',   (0,0), (-1,-1), 10),
    ('BOTTOMPADDING',(0,0), (-1,-1), 10),
    ('ROUNDEDCORNERS', [6]),
]))
story.append(p2_hdr)
story.append(Spacer(1, 0.14*inch))
story.append(HRFlowable(width=W, thickness=1.5, color=BLUE,
                         spaceAfter=8, spaceBefore=2))

# Finding 1 + funnel chart
f1_text = [
    Paragraph('Finding 1 — View → Cart Is the Critical Failure Point',
              sty['find_hd']),
    Paragraph(
        f'Of 9.2 million sessions, <b>93.8% never add a product to cart</b> — '
        f'the largest and most recoverable conversion leak in the funnel. '
        f'Only 573,019 sessions reach the cart stage, while 281,185 of those '
        f'abandon before purchasing, representing an estimated '
        f'<b>{STATS["lost_revenue"]} in lost revenue</b>. '
        f'Industry benchmark for view-to-cart conversion is 8–12%; '
        f'this store is at 6.2% — significantly below par.',
        sty['find_bd']
    ),
    Paragraph(
        f'<font color="#065F46"><b>Signal:</b> The gap between viewing and '
        f'carting is a product discovery and trust problem — not a pricing '
        f'problem. Recommendations: add social proof (ratings, reviews count) '
        f'on product pages and a persistent "add to cart" CTA.</font>',
        sty['find_bd']
    ),
]
f1_tbl = Table([[f1_text, chart_funnel]],
               colWidths=[W*0.54, W*0.46])
f1_tbl.setStyle(TableStyle([
    ('VALIGN',       (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',  (0,0), (-1,-1), 0),
    ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ('TOPPADDING',   (0,0), (-1,-1), 0),
    ('BOTTOMPADDING',(0,0), (-1,-1), 0),
]))
story.append(f1_tbl)
story.append(Spacer(1, 0.06*inch))
story.append(HRFlowable(width=W, thickness=0.5,
                         color=colors.HexColor('#E5E7EB'), spaceAfter=6))

# Finding 2 + category chart
f2_text = [
    Paragraph('Finding 2 — Apparel and Sport Are High-Priority Problem Categories',
              sty['find_hd']),
    Paragraph(
        f'Category-level analysis reveals a <b>3.7x conversion gap</b> between '
        f'the worst performing category (apparel at {STATS["worst_cat_conv"]}) '
        f'and the best (electronics at {STATS["best_cat_conv"]}). '
        f'Apparel and sport both fall below 3% — flagged as high priority. '
        f'The electronics/saturn brand-category combination achieves '
        f'<b>{STATS["top_combo_conv"]} conversion</b> — the highest in the dataset — '
        f'suggesting that brand familiarity and product specificity are '
        f'strong conversion drivers.',
        sty['find_bd']
    ),
    Paragraph(
        f'<font color="#065F46"><b>Signal:</b> Apparel requires size guides, '
        f'better imagery, and return policy prominence. '
        f'Electronics benefits from spec comparison tools.</font>',
        sty['find_bd']
    ),
]
f2_tbl = Table([[f2_text, chart_category]],
               colWidths=[W*0.54, W*0.46])
f2_tbl.setStyle(TableStyle([
    ('VALIGN',       (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',  (0,0), (-1,-1), 0),
    ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ('TOPPADDING',   (0,0), (-1,-1), 0),
    ('BOTTOMPADDING',(0,0), (-1,-1), 0),
]))
story.append(f2_tbl)
story.append(Spacer(1, 0.06*inch))
story.append(HRFlowable(width=W, thickness=0.5,
                         color=colors.HexColor('#E5E7EB'), spaceAfter=6))

# Finding 3 + duration chart
f3_text = [
    Paragraph('Finding 3 — Session Engagement Is the Strongest Conversion Signal',
              sty['find_hd']),
    Paragraph(
        f'Sessions under 1 minute convert at just <b>{STATS["session_dur_low"]}</b>, '
        f'while sessions of 3–5 minutes convert at <b>{STATS["session_dur_high"]}</b> '
        f'— a <b>12x difference</b>. Peak conversion hours are 4am–10am, '
        f'with 9am achieving {STATS["best_conv_hour"]} — 26% above the daily average. '
        f'Monday is the strongest converting day at 7.0%. '
        f'These patterns confirm that engaged, intentional browsing sessions '
        f'are far more valuable than high-volume low-engagement traffic.',
        sty['find_bd']
    ),
    Paragraph(
        f'<font color="#065F46"><b>Signal:</b> Implement a product '
        f'recommendations widget to extend session duration past the '
        f'3-minute engagement threshold for low-engagement sessions.</font>',
        sty['find_bd']
    ),
]
f3_tbl = Table([[f3_text, chart_duration]],
               colWidths=[W*0.54, W*0.46])
f3_tbl.setStyle(TableStyle([
    ('VALIGN',       (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',  (0,0), (-1,-1), 0),
    ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ('TOPPADDING',   (0,0), (-1,-1), 0),
    ('BOTTOMPADDING',(0,0), (-1,-1), 0),
]))
story.append(f3_tbl)

story.append(Spacer(1, 0.06*inch))
story.append(HRFlowable(width=W, thickness=0.5,
                         color=colors.HexColor('#E5E7EB'), spaceAfter=0))
story.append(Spacer(1, 0.04*inch))
story.append(Paragraph(
    'FunnelIQ Analytics  |  '
    'github.com/waseemak313/funneliq-ecommerce-funnel-analytics  |  Page 2 of 3',
    sty['footer']
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# PAGE 3 — ML Model + Recommendations + Impact Table
# ══════════════════════════════════════════════════════════════════════════

p3_hdr = Table([[
    Paragraph('ML Model &amp; Recommendations', sty['p2_head']),
    Paragraph('FunnelIQ Analytics  |  Oct 2019', sty['p2_sub']),
]], colWidths=[W*0.65, W*0.35])
p3_hdr.setStyle(TableStyle([
    ('BACKGROUND',   (0,0), (-1,-1), NAVY),
    ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING',  (0,0), (-1,-1), 14),
    ('RIGHTPADDING', (0,0), (-1,-1), 14),
    ('TOPPADDING',   (0,0), (-1,-1), 10),
    ('BOTTOMPADDING',(0,0), (-1,-1), 10),
    ('ROUNDEDCORNERS', [6]),
]))
story.append(p3_hdr)
story.append(Spacer(1, 0.14*inch))
story.append(HRFlowable(width=W, thickness=1.5, color=BLUE,
                         spaceAfter=8, spaceBefore=2))

# ML model section
story.append(Paragraph('Drop-off Prediction Model', sty['section']))

ml_text = [
    Paragraph(
        f'An XGBoost classifier trained on <b>7.4 million sessions</b> with '
        f'17 behavioral features achieved a <b>ROC-AUC of {STATS["xgb_auc"]}</b> '
        f'and <b>99% overall accuracy</b> on 1.8 million held-out test sessions. '
        f'SHAP analysis identified the top abandonment drivers: '
        f'<b>{STATS["top_shap_1"]}</b>, <b>{STATS["top_shap_2"]}</b>, and '
        f'<b>{STATS["top_shap_3"]}</b> — confirming that engagement depth '
        f'is the dominant conversion signal. '
        f'At a 70% abandonment threshold, the model flags '
        f'<b>{STATS["sessions_flagged"]} high-risk sessions</b>, '
        f'of which {STATS["recoverable"]} are estimated recoverable '
        f'through targeted intervention.',
        sty['find_bd']
    ),
    Spacer(1, 4),
    Paragraph(
        f'<font color="#065F46"><b>14% uplift justification:</b> '
        f'Model precision at 0.70 threshold × industry A/B test benchmark '
        f'for exit-intent interventions = 14% of flagged sessions recover. '
        f'Estimated revenue recovery: <b>{STATS["revenue_recovery"]}</b>.</font>',
        sty['find_bd']
    ),
]
ml_tbl = Table([[ml_text, chart_shap]],
               colWidths=[W*0.54, W*0.46])
ml_tbl.setStyle(TableStyle([
    ('VALIGN',       (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',  (0,0), (-1,-1), 0),
    ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ('TOPPADDING',   (0,0), (-1,-1), 0),
    ('BOTTOMPADDING',(0,0), (-1,-1), 0),
]))
story.append(ml_tbl)
story.append(Spacer(1, 0.1*inch))

# Recommendations
story.append(Paragraph('Recommendations', sty['section']))
story.append(HRFlowable(width=W, thickness=0.5,
                         color=colors.HexColor('#E5E7EB'), spaceAfter=6))

recs = [
    ('#E8402A', 'R1', 'Exit-intent intervention for high-value abandoned carts',
     'Owner: UX Team  |  Timeline: Sprint 1',
     ['Deploy exit-intent popup for sessions with avg cart value >$100 '
      'at 70%+ abandonment probability (221K sessions/month).',
      'Offer: free shipping threshold or 5% first-purchase discount.',
      'Expected lift: 14% recovery on targeted sessions.'],
     f'221,373 sessions/month  |  avg $411 value  |  '
     f'Est. $12.7M annual recovery'),

    ('#F5A623', 'R2', 'Product recommendation widget to extend session depth',
     'Owner: Product Team  |  Timeline: Sprint 2',
     ['Add "You may also like" widget on all product pages to push '
      'sessions past the 3-minute engagement threshold.',
      'Target: 5.3M bounce sessions under 2 minutes.',
      'Sessions at 3-5 min convert at 13.7% vs 1.1% under 1 min.'],
     '5.3M low-engagement sessions  |  12x conversion uplift potential'),

    ('#2D6BE4', 'R3', 'Category-specific UX fixes for apparel and sport',
     'Owner: Design Team  |  Timeline: Sprint 3',
     ['Apparel (2.4% conv): add size guide, 360-degree imagery, '
      'prominent return policy, social proof badges.',
      'Sport (2.91% conv): add comparison tool, expert review section.',
      'Electronics benchmark (8.88%) as the UX gold standard.'],
     'Combined 341K sessions  |  Potential uplift to 5%+ = 8.7K more purchases/mo'),
]

for r_color, r_num, r_title, r_owner, r_bullets, r_impact in recs:
    badge = Table([[
        Paragraph(r_num, S('RN', fontSize=10, textColor=WHITE,
                           fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph(r_title, S('RT', fontSize=9.5, textColor=WHITE,
                             fontName='Helvetica-Bold', leading=12)),
    ]], colWidths=[0.34*inch, W-0.34*inch])
    badge.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), colors.HexColor(r_color)),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',  (0,0), (0,0),   8),
        ('LEFTPADDING',  (1,0), (1,0),   10),
        ('TOPPADDING',   (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0), (-1,-1), 6),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(badge)

    body_items = [
        Paragraph(r_owner, S('OW', fontSize=7.5, textColor=MID_GRAY,
                             fontName='Helvetica-Oblique', leading=11,
                             spaceBefore=3, spaceAfter=2))
    ]
    for b in r_bullets:
        body_items.append(
            Paragraph(f'&#8226;  {b}',
                      S('REC', fontSize=8, textColor=DARK_GRAY,
                        fontName='Helvetica', leading=11,
                        leftIndent=8, spaceAfter=2))
        )
    body_items.append(
        Paragraph(f'&#x1F4CA;  <b>Impact:</b>  {r_impact}',
                  S('IMP3', fontSize=7.8,
                    textColor=colors.HexColor('#065F46'),
                    fontName='Helvetica', leading=10,
                    leftIndent=8, spaceBefore=2, spaceAfter=4))
    )
    body_tbl = Table([[body_items]], colWidths=[W])
    body_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), colors.HexColor('#F9FAFB')),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING',   (0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0), (-1,-1), 3),
    ]))
    story.append(body_tbl)
    story.append(Spacer(1, 0.06*inch))

# Impact summary table
story.append(Paragraph('Combined Impact Summary', sty['section']))
impact_data = [
    ['Initiative', 'Target Segment', 'Projected Impact', 'Timeline'],
    ['Exit-intent popup', '221K high-value abandoned carts',
     '$12.7M annual recovery', 'Sprint 1'],
    ['Engagement widget', '5.3M bounce sessions',
     '12x conv. uplift on target', 'Sprint 2'],
    ['Apparel/sport UX fix', '341K low-conv. sessions',
     '+8.7K purchases/month', 'Sprint 3'],
    ['ML model deployment', '1.69M flagged sessions',
     '$72.6M total addressable', 'Q2 2024'],
]
imp_tbl = Table(impact_data,
                colWidths=[W*0.25, W*0.28, W*0.27, W*0.20])
imp_tbl.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0),  NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
    ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
    ('FONTSIZE',      (0,0), (-1,0),  8),
    ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
    ('FONTSIZE',      (0,1), (-1,-1), 7.8),
    ('TEXTCOLOR',     (0,1), (-1,-1), DARK_GRAY),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, LIGHT_BG]),
    ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING',    (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING',   (0,0), (-1,-1), 7),
    ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
    ('ROUNDEDCORNERS', [4]),
]))
story.append(imp_tbl)
story.append(Spacer(1, 0.1*inch))

# Footer
story.append(HRFlowable(width=W, thickness=0.5, color=MID_GRAY, spaceAfter=4))
story.append(Paragraph(
    'FunnelIQ Analytics  |  '
    'github.com/waseemak313/funneliq-ecommerce-funnel-analytics  |  '
    'Data: REES46 via Kaggle (kaggle.com/mkechinov)  |  Page 3 of 3',
    sty['footer']
))

# ── Build ──────────────────────────────────────────────────────────────────
print("  Building PDF...")
doc.build(story)
print(f"  ✓ Saved: outputs/FunnelIQ_Insights_Brief.pdf")
print("="*60 + "\n")
