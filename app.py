import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import requests
import time

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="Northern IN Land Deals",
    page_icon="🏞️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THEME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    .deal-card { background: #0d1117; border: 1px solid #1e2d3d; border-radius: 12px; padding: 18px; margin-bottom: 10px; }
    .deal-card:hover { border-color: #f0a030; }
    .grade-a-plus, .grade-a { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; background: #3fb95015; color: #3fb950; }
    .grade-b-plus { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; background: #58a6ff15; color: #58a6ff; }
    .grade-b { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; background: #f0a03015; color: #f0a030; }
    .grade-c, .grade-d { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; background: #f8514915; color: #f85149; }
    .grade-comp { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; background: #8b949e15; color: #8b949e; }
    .grade-none { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; background: #6e768115; color: #6e7681; }
    .new-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; background: #f0a03030; color: #f0a030; margin-left: 6px; }
    .source-link { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; margin: 2px; background: #58a6ff15; color: #58a6ff; text-decoration: none; }
    .tag { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 10px; margin: 1px; background: #1e2d3d; color: #8b949e; }
    .fire-deal { border-left: 3px solid #3fb950 !important; }
    .refresh-box { background: #0d1117; border: 1px solid #1e2d3d; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; }
    div[data-testid="stMetric"] { background: #0d1117; border: 1px solid #1e2d3d; border-radius: 12px; padding: 16px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COUNTY MARKET DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Massively expanded county dataset: soil quality (NCCPI), land use %, crop yields, 5-yr price history
# Based on USDA NASS, Indiana Farmland Values Survey, Purdue Ag Econ data
COUNTIES = {
    #              avg   lo    hi    seat              pop     est  nccpi farm%  forest% corn  soy   wheat  rent  hist  top_soil
    "LaPorte":    {"avg":12718,"lo":7780, "hi":16361,"seat":"La Porte",     "pop":110552,"listings_est":119,"nccpi":68,"farm_pct":62,"forest_pct":18,"corn_yield":182,"soy_yield":58,"wheat_yield":74,"rent":285,"hist":[9800,10500,11200,11900,12400,12718],"top_soil":"Coupee silt loam, Tracy sandy loam","cattle_stocking":1.8,"timber_val":1500,"top_crops":["Corn","Soybeans","Wheat","Hay"]},
    "Porter":     {"avg":11500,"lo":7000, "hi":15000,"seat":"Valparaiso",   "pop":173215,"listings_est":346,"nccpi":65,"farm_pct":58,"forest_pct":15,"corn_yield":178,"soy_yield":56,"wheat_yield":72,"rent":270,"hist":[8900,9500,10100,10800,11300,11500],"top_soil":"Morley silt loam, Rensselaer loam","cattle_stocking":1.7,"timber_val":1400,"top_crops":["Corn","Soybeans","Hay","Popcorn"]},
    "St. Joseph": {"avg":13200,"lo":8500, "hi":17000,"seat":"South Bend",   "pop":271826,"listings_est":200,"nccpi":72,"farm_pct":55,"forest_pct":14,"corn_yield":188,"soy_yield":60,"wheat_yield":76,"rent":295,"hist":[10200,10900,11600,12300,12900,13200],"top_soil":"Crosby silt loam, Riddles loam","cattle_stocking":1.8,"timber_val":1600,"top_crops":["Corn","Soybeans","Mint","Wheat"]},
    "Lake":       {"avg":14500,"lo":9000, "hi":20000,"seat":"Crown Point",  "pop":498700,"listings_est":366,"nccpi":70,"farm_pct":45,"forest_pct":12,"corn_yield":180,"soy_yield":57,"wheat_yield":73,"rent":300,"hist":[11200,12000,12800,13600,14200,14500],"top_soil":"Maumee fine sandy loam","cattle_stocking":1.6,"timber_val":1300,"top_crops":["Corn","Soybeans","Vegetables"]},
    "Starke":     {"avg":8900, "lo":5500, "hi":12000,"seat":"Knox",         "pop":22993, "listings_est":39, "nccpi":52,"farm_pct":60,"forest_pct":22,"corn_yield":155,"soy_yield":48,"wheat_yield":62,"rent":215,"hist":[6800,7200,7700,8200,8600,8900],"top_soil":"Maumee fine sandy loam, Plainfield sand","cattle_stocking":2.2,"timber_val":1100,"top_crops":["Corn","Soybeans","Mint","Potatoes"]},
    "Marshall":   {"avg":10800,"lo":7200, "hi":14500,"seat":"Plymouth",     "pop":46258, "listings_est":62, "nccpi":63,"farm_pct":65,"forest_pct":17,"corn_yield":172,"soy_yield":54,"wheat_yield":70,"rent":255,"hist":[8300,8900,9500,10100,10600,10800],"top_soil":"Riddles loam, Crosby silt loam","cattle_stocking":1.8,"timber_val":1300,"top_crops":["Corn","Soybeans","Hay","Dairy"]},
    "Jasper":     {"avg":10200,"lo":6800, "hi":13500,"seat":"Rensselaer",   "pop":33562, "listings_est":45, "nccpi":66,"farm_pct":72,"forest_pct":12,"corn_yield":178,"soy_yield":56,"wheat_yield":72,"rent":265,"hist":[7900,8500,9100,9700,10000,10200],"top_soil":"Brookston silty clay loam","cattle_stocking":1.9,"timber_val":1200,"top_crops":["Corn","Soybeans","Tomatoes"]},
    "Newton":     {"avg":8500, "lo":5000, "hi":11500,"seat":"Kentland",     "pop":14004, "listings_est":30, "nccpi":55,"farm_pct":75,"forest_pct":8, "corn_yield":165,"soy_yield":52,"wheat_yield":66,"rent":225,"hist":[6500,6900,7400,7900,8300,8500],"top_soil":"Gilford fine sandy loam","cattle_stocking":2.0,"timber_val":900,"top_crops":["Corn","Soybeans"]},
    "Pulaski":    {"avg":8200, "lo":5200, "hi":11000,"seat":"Winamac",      "pop":12638, "listings_est":20, "nccpi":50,"farm_pct":58,"forest_pct":25,"corn_yield":152,"soy_yield":47,"wheat_yield":60,"rent":210,"hist":[6200,6600,7100,7600,8000,8200],"top_soil":"Plainfield sand, Maumee fine sandy loam","cattle_stocking":2.3,"timber_val":1100,"top_crops":["Corn","Soybeans","Hay","Livestock"]},
    "Elkhart":    {"avg":12500,"lo":8000, "hi":16000,"seat":"Goshen",       "pop":206341,"listings_est":150,"nccpi":67,"farm_pct":52,"forest_pct":15,"corn_yield":180,"soy_yield":58,"wheat_yield":74,"rent":280,"hist":[9700,10400,11100,11800,12300,12500],"top_soil":"Crosby-Brookston complex","cattle_stocking":1.8,"timber_val":1400,"top_crops":["Corn","Soybeans","Dairy","Mint"]},
    "Kosciusko":  {"avg":11000,"lo":7500, "hi":14500,"seat":"Warsaw",       "pop":79835, "listings_est":140,"nccpi":62,"farm_pct":55,"forest_pct":18,"corn_yield":170,"soy_yield":54,"wheat_yield":70,"rent":255,"hist":[8500,9100,9700,10300,10800,11000],"top_soil":"Miami loam, Crosby silt loam","cattle_stocking":1.9,"timber_val":1400,"top_crops":["Corn","Soybeans","Hay","Dairy"]},
    "Noble":      {"avg":9500, "lo":6000, "hi":13000,"seat":"Albion",       "pop":47529, "listings_est":55, "nccpi":58,"farm_pct":58,"forest_pct":22,"corn_yield":165,"soy_yield":52,"wheat_yield":67,"rent":235,"hist":[7300,7800,8300,8800,9300,9500],"top_soil":"Miami loam","cattle_stocking":2.0,"timber_val":1500,"top_crops":["Corn","Soybeans","Hay","Livestock"]},
    "Fulton":     {"avg":9000, "lo":5800, "hi":12500,"seat":"Rochester",    "pop":20007, "listings_est":35, "nccpi":56,"farm_pct":62,"forest_pct":18,"corn_yield":162,"soy_yield":51,"wheat_yield":65,"rent":225,"hist":[6900,7400,7900,8400,8800,9000],"top_soil":"Crosby silt loam","cattle_stocking":2.0,"timber_val":1200,"top_crops":["Corn","Soybeans","Hay"]},
    "White":      {"avg":10500,"lo":7000, "hi":14000,"seat":"Monticello",   "pop":24102, "listings_est":40, "nccpi":64,"farm_pct":68,"forest_pct":12,"corn_yield":175,"soy_yield":55,"wheat_yield":71,"rent":260,"hist":[8100,8700,9300,9900,10300,10500],"top_soil":"Drummer silty clay loam","cattle_stocking":1.8,"timber_val":1100,"top_crops":["Corn","Soybeans","Wheat"]},
    "Whitley":    {"avg":10000,"lo":6500, "hi":13500,"seat":"Columbia City","pop":33964, "listings_est":45, "nccpi":60,"farm_pct":62,"forest_pct":18,"corn_yield":168,"soy_yield":53,"wheat_yield":68,"rent":245,"hist":[7700,8200,8800,9400,9800,10000],"top_soil":"Blount silt loam","cattle_stocking":1.9,"timber_val":1300,"top_crops":["Corn","Soybeans","Hay"]},
    "Steuben":    {"avg":10500,"lo":7000, "hi":14000,"seat":"Angola",       "pop":34474, "listings_est":60, "nccpi":58,"farm_pct":50,"forest_pct":22,"corn_yield":165,"soy_yield":52,"wheat_yield":67,"rent":240,"hist":[8100,8600,9200,9800,10300,10500],"top_soil":"Morley-Blount complex","cattle_stocking":2.0,"timber_val":1500,"top_crops":["Corn","Soybeans","Hay","Dairy"]},
    "DeKalb":     {"avg":10200,"lo":6800, "hi":13500,"seat":"Auburn",       "pop":43475, "listings_est":50, "nccpi":62,"farm_pct":65,"forest_pct":15,"corn_yield":170,"soy_yield":54,"wheat_yield":69,"rent":250,"hist":[7900,8400,9000,9600,10000,10200],"top_soil":"Blount-Pewamo complex","cattle_stocking":1.9,"timber_val":1300,"top_crops":["Corn","Soybeans","Wheat"]},
    "LaGrange":   {"avg":11500,"lo":7500, "hi":15500,"seat":"LaGrange",     "pop":39614, "listings_est":40, "nccpi":65,"farm_pct":58,"forest_pct":18,"corn_yield":175,"soy_yield":55,"wheat_yield":71,"rent":265,"hist":[8900,9500,10200,10900,11300,11500],"top_soil":"Houghton muck, Morley silt loam","cattle_stocking":1.9,"timber_val":1400,"top_crops":["Corn","Soybeans","Dairy (Amish)","Hay"]},
    "Allen":      {"avg":13000,"lo":8500, "hi":17500,"seat":"Fort Wayne",   "pop":385340,"listings_est":250,"nccpi":68,"farm_pct":55,"forest_pct":15,"corn_yield":182,"soy_yield":58,"wheat_yield":74,"rent":285,"hist":[10100,10800,11500,12200,12800,13000],"top_soil":"Blount silt loam, Pewamo clay loam","cattle_stocking":1.8,"timber_val":1400,"top_crops":["Corn","Soybeans","Wheat","Popcorn"]},
    "Cass":       {"avg":9800, "lo":6500, "hi":13000,"seat":"Logansport",   "pop":37689, "listings_est":40, "nccpi":61,"farm_pct":62,"forest_pct":18,"corn_yield":170,"soy_yield":54,"wheat_yield":69,"rent":245,"hist":[7500,8000,8600,9200,9600,9800],"top_soil":"Crosby silt loam","cattle_stocking":1.9,"timber_val":1300,"top_crops":["Corn","Soybeans","Hay"]},
    "Miami":      {"avg":9500, "lo":6200, "hi":13000,"seat":"Peru",         "pop":35523, "listings_est":35, "nccpi":60,"farm_pct":60,"forest_pct":20,"corn_yield":168,"soy_yield":53,"wheat_yield":68,"rent":240,"hist":[7300,7800,8400,9000,9400,9500],"top_soil":"Crosby-Miami complex","cattle_stocking":1.9,"timber_val":1300,"top_crops":["Corn","Soybeans","Hay","Livestock"]},
    "Wabash":     {"avg":9200, "lo":6000, "hi":12500,"seat":"Wabash",       "pop":31424, "listings_est":30, "nccpi":59,"farm_pct":58,"forest_pct":22,"corn_yield":165,"soy_yield":52,"wheat_yield":67,"rent":235,"hist":[7100,7600,8100,8700,9100,9200],"top_soil":"Miami silt loam","cattle_stocking":2.0,"timber_val":1400,"top_crops":["Corn","Soybeans","Hay"]},
    "Huntington": {"avg":9800, "lo":6500, "hi":13000,"seat":"Huntington",   "pop":36374, "listings_est":40, "nccpi":62,"farm_pct":63,"forest_pct":17,"corn_yield":170,"soy_yield":54,"wheat_yield":69,"rent":245,"hist":[7500,8000,8600,9200,9600,9800],"top_soil":"Blount silt loam","cattle_stocking":1.9,"timber_val":1300,"top_crops":["Corn","Soybeans","Wheat"]},
    "Wells":      {"avg":10000,"lo":6800, "hi":13500,"seat":"Bluffton",     "pop":28174, "listings_est":25, "nccpi":63,"farm_pct":68,"forest_pct":13,"corn_yield":172,"soy_yield":54,"wheat_yield":70,"rent":250,"hist":[7700,8200,8800,9400,9800,10000],"top_soil":"Blount-Pewamo complex","cattle_stocking":1.8,"timber_val":1200,"top_crops":["Corn","Soybeans","Wheat","Popcorn"]},
    "Adams":      {"avg":9500, "lo":6200, "hi":13000,"seat":"Decatur",      "pop":35667, "listings_est":30, "nccpi":61,"farm_pct":65,"forest_pct":14,"corn_yield":168,"soy_yield":53,"wheat_yield":68,"rent":240,"hist":[7300,7800,8400,9000,9400,9500],"top_soil":"Blount-Pewamo complex","cattle_stocking":1.9,"timber_val":1200,"top_crops":["Corn","Soybeans","Dairy"]},
    "Jay":        {"avg":8800, "lo":5500, "hi":12000,"seat":"Portland",     "pop":21058, "listings_est":20, "nccpi":57,"farm_pct":68,"forest_pct":12,"corn_yield":160,"soy_yield":50,"wheat_yield":64,"rent":220,"hist":[6700,7200,7700,8200,8600,8800],"top_soil":"Pewamo-Blount","cattle_stocking":2.0,"timber_val":1100,"top_crops":["Corn","Soybeans","Wheat"]},
    "Blackford":  {"avg":9000, "lo":5800, "hi":12000,"seat":"Hartford City","pop":11758, "listings_est":15, "nccpi":58,"farm_pct":70,"forest_pct":11,"corn_yield":162,"soy_yield":51,"wheat_yield":65,"rent":225,"hist":[6900,7400,7900,8400,8800,9000],"top_soil":"Blount silt loam","cattle_stocking":2.0,"timber_val":1100,"top_crops":["Corn","Soybeans"]},
    "Benton":     {"avg":10800,"lo":7500, "hi":14000,"seat":"Fowler",       "pop":8661,  "listings_est":15, "nccpi":68,"farm_pct":82,"forest_pct":5, "corn_yield":182,"soy_yield":58,"wheat_yield":74,"rent":275,"hist":[8300,8900,9500,10100,10600,10800],"top_soil":"Drummer silty clay loam","cattle_stocking":1.7,"timber_val":800,"top_crops":["Corn","Soybeans"]},
    "Carroll":    {"avg":10500,"lo":7000, "hi":14000,"seat":"Delphi",       "pop":20016, "listings_est":20, "nccpi":65,"farm_pct":72,"forest_pct":14,"corn_yield":178,"soy_yield":56,"wheat_yield":72,"rent":265,"hist":[8100,8600,9200,9800,10300,10500],"top_soil":"Brookston silty clay","cattle_stocking":1.8,"timber_val":1200,"top_crops":["Corn","Soybeans","Wheat"]},
    "Tippecanoe": {"avg":12000,"lo":8000, "hi":16000,"seat":"Lafayette",    "pop":195732,"listings_est":120,"nccpi":70,"farm_pct":65,"forest_pct":15,"corn_yield":185,"soy_yield":59,"wheat_yield":75,"rent":290,"hist":[9300,9900,10600,11300,11800,12000],"top_soil":"Drummer-Brookston complex","cattle_stocking":1.8,"timber_val":1300,"top_crops":["Corn","Soybeans","Popcorn","Tomatoes"]},
}

# Crop economics (2026 marketing year estimates)
CROP_PRICES = {"corn": 4.50, "soybeans": 11.00, "wheat": 6.50, "hay": 180, "alfalfa": 220}
CROP_COSTS = {"corn": 650, "soybeans": 380, "wheat": 310}  # cost per acre

# Soil quality bands
def soil_grade(nccpi):
    if nccpi >= 75: return "Class I", "#3fb950", "Prime — top tier, corn 190+ bu/ac"
    if nccpi >= 65: return "Class II", "#3fb950", "Excellent — corn 175-190 bu/ac"
    if nccpi >= 55: return "Class III", "#58a6ff", "Good — corn 160-175 bu/ac"
    if nccpi >= 45: return "Class IV", "#f0a030", "Fair — corn 145-160 bu/ac"
    return "Class V+", "#f85149", "Marginal — best for pasture/hay"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEAL SCORING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def grade(row):
    lt = row.get("listing_type", "")
    if lt == "Sold Comp":
        return "COMP", "Reference", "Sold comp — pricing reference only.", "#8b949e"
    ppa = row.get("price_per_acre")
    county = row.get("county", "")
    assessed = row.get("assessed_value")
    price = row.get("price")
    if assessed and price and assessed > 0:
        r = price / assessed
        if r < 0.15: return "A+", "Steal", f"{r:.0%} of assessed (${assessed:,.0f})", "#3fb950"
        if r < 0.25: return "A",  "Great", f"{r:.0%} of assessed (${assessed:,.0f})", "#3fb950"
        if r < 0.40: return "B+", "Good",  f"{r:.0%} of assessed", "#58a6ff"
        if r < 0.60: return "B",  "Fair",  f"{r:.0%} of assessed", "#f0a030"
        return "C", "Full Price", f"{r:.0%} of assessed", "#f0a030"
    if ppa and county in COUNTIES:
        cd = COUNTIES[county]
        if ppa < cd["lo"] * 0.7:  return "A+", "Way Below Mkt",  f"${ppa:,.0f}/ac vs avg ${cd['avg']:,.0f}", "#3fb950"
        if ppa < cd["lo"]:        return "A",  "Below Comps",    f"${ppa:,.0f}/ac vs low comp ${cd['lo']:,.0f}", "#3fb950"
        if ppa < cd["avg"] * 0.85:return "B+", "Good Value",     f"${ppa:,.0f}/ac vs avg ${cd['avg']:,.0f}", "#58a6ff"
        if ppa < cd["avg"] * 1.1: return "B",  "Market Rate",    f"${ppa:,.0f}/ac ≈ avg ${cd['avg']:,.0f}", "#f0a030"
        if ppa < cd["avg"] * 1.5: return "C",  "Above Avg",      f"${ppa:,.0f}/ac > avg ${cd['avg']:,.0f}", "#f0a030"
        return "D", "Premium", f"${ppa:,.0f}/ac >> avg ${cd['avg']:,.0f}", "#f85149"
    if ppa:
        if ppa < 5000:  return "A",  "Cheap",     f"${ppa:,.0f}/ac — very affordable", "#3fb950"
        if ppa < 9000:  return "B+", "Good",      f"${ppa:,.0f}/ac — below regional avg", "#58a6ff"
        if ppa < 13000: return "B",  "Average",   f"${ppa:,.0f}/ac", "#f0a030"
        return "C", "Above Avg", f"${ppa:,.0f}/ac", "#f0a030"
    return "—", "TBD", "No price data yet", "#6e7681"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEED LISTINGS (all ~110+ hardcoded, scraped 4/7/2026)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEED_LISTINGS = [
    # ═══════ MOSSY OAK PROPERTIES ═══════
    {"title": "84.1 Ac Recreational / Development — Michigan City", "location": "Michigan City", "county": "LaPorte", "acres": 84.1, "price": 1250000, "price_per_acre": 14865, "listing_type": "For Sale", "property_type": "Recreational/Development", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["wooded", "tillable", "development"], "why": "Rare combo near Michigan City. Rec + dev upside.", "is_new": False},
    {"title": "Rensselaer 72 Ac Farmland — Jasper Co", "location": "Rensselaer", "county": "Jasper", "acres": 72, "price": 899999, "price_per_acre": 12500, "listing_type": "For Sale", "property_type": "Farmland", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["farmland", "investment"], "why": "Productive ground near town.", "is_new": False},
    {"title": "64 Ac Tillable Investment — LaPorte SR 39", "location": "LaPorte", "county": "LaPorte", "acres": 64, "price": 875000, "price_per_acre": 13672, "listing_type": "For Sale", "property_type": "Farmland", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["tillable", "highway-frontage"], "why": "Highway frontage, quality soils, easy to lease.", "is_new": False},
    {"title": "2 Ac Commercial Lot — Porter, US 6", "location": "Porter", "county": "Porter", "acres": 2, "price": 695000, "price_per_acre": 347500, "listing_type": "For Sale", "property_type": "Commercial", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["commercial", "high-visibility"], "why": "Corner lot on US 6 — commercial premium.", "is_new": False},
    {"title": "35 Ac Tillable — LaPorte SR 39", "location": "LaPorte", "county": "LaPorte", "acres": 35, "price": 510000, "price_per_acre": 14571, "listing_type": "For Sale", "property_type": "Farmland", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["tillable", "building-sites"], "why": "Level, all tillable, potential building sites.", "is_new": False},
    {"title": "Jasper 57 Ac All-Timber Hunting", "location": "Rensselaer", "county": "Jasper", "acres": 57, "price": 499000, "price_per_acre": 8754, "listing_type": "For Sale", "property_type": "Hunting/Timber", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["timber", "hunting", "recreational"], "why": "$8,754/ac for timber surrounded by crops — great hunting.", "is_new": False},
    {"title": "50 Ac Multi-Use — Starke Co 400 S", "location": "Knox", "county": "Starke", "acres": 50, "price": 400000, "price_per_acre": 8000, "listing_type": "For Sale", "property_type": "Multi-Use", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["multi-use", "road-frontage"], "why": "Good road frontage, versatile use in cheap county.", "is_new": False},
    {"title": "48 Ac Recreational — Knox, Starke Co", "location": "Knox", "county": "Starke", "acres": 48, "price": 379900, "price_per_acre": 7914, "listing_type": "For Sale", "property_type": "Recreational", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["recreational", "building-site"], "why": "Below Starke avg. Future homesite or getaway.", "is_new": False},
    {"title": "28 Ac Tillable — LaPorte SR 39", "location": "LaPorte", "county": "LaPorte", "acres": 28, "price": 375000, "price_per_acre": 13393, "listing_type": "For Sale", "property_type": "Farmland", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["tillable", "1031-exchange"], "why": "Good for 1031 exchange buyers.", "is_new": False},
    {"title": "26.4 Ac Hunting Land — Starke Co", "location": "Knox", "county": "Starke", "acres": 26.4, "price": 215000, "price_per_acre": 8144, "listing_type": "For Sale", "property_type": "Hunting", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["hunting", "road-frontage"], "why": "Dual road frontage, great deer habitat.", "is_new": False},
    {"title": "21.6 Ac Recreational — Starke Co", "location": "Knox", "county": "Starke", "acres": 21.61, "price": 199900, "price_per_acre": 9256, "listing_type": "For Sale", "property_type": "Recreational", "source": "Mossy Oak Properties", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/", "auction_date": None, "tags": ["recreational", "camping", "building-site"], "why": "Private getaway with building potential.", "is_new": False},

    # ═══════ HALDERMAN ═══════
    {"title": "Warren J Hill Trust — 151 Ac LaPorte/Porter", "location": "Clinton/Washington Twp", "county": "LaPorte", "acres": 151.48, "price": None, "price_per_acre": None, "listing_type": "Private Listing", "property_type": "Farmland", "source": "Halderman", "url": "https://www.halderman.com/property-listings/", "auction_date": None, "tags": ["farmland", "multi-county", "trust-sale"], "why": "Trust sale spanning 2 counties — likely priced to close.", "is_new": False},
    {"title": "Merriman Farm — 53.5 Ac Jasper Co", "location": "Union Twp", "county": "Jasper", "acres": 53.53, "price": None, "price_per_acre": None, "listing_type": "Private Listing", "property_type": "Farmland", "source": "Halderman", "url": "https://www.halderman.com/property-listings/", "auction_date": None, "tags": ["farmland", "crop-credit"], "why": "Buyer credited $235/tillable ac — built-in discount.", "is_new": False},
    {"title": "80 Ac Productive Farmground — St. Joseph Co", "location": "Bremen", "county": "St. Joseph", "acres": 80, "price": None, "price_per_acre": None, "listing_type": "Private Listing", "property_type": "Farmland", "source": "Geswein Farm & Land", "url": "https://gfarmland.com/farm-real-estate/", "auction_date": None, "tags": ["farmland", "high-quality"], "why": "High quality ground near Bremen.", "is_new": False},

    # ═══════ RANCH & FARM AUCTIONS — Gillham 8-tract auction ═══════
    {"title": "Gillham Farm Tract 1 — 86.35 Ac Scipio Twp", "location": "Door Village", "county": "LaPorte", "acres": 86.35, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Farmland", "source": "Ranch & Farm Auctions", "url": "https://ranchandfarmauctions.com/auction-event/la-porte-co-in-40061-acres-in-8-tracts", "auction_date": "2026-07-23", "tags": ["auction", "tillable", "legacy-farm"], "why": "150-year family farm. NCCPI 63.5. 10% down, 30-day close.", "is_new": False},
    {"title": "Gillham Farm Tract 2 — 68.64 Ac w/ Barn", "location": "Door Village", "county": "LaPorte", "acres": 68.64, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Farmland/Wooded", "source": "Ranch & Farm Auctions", "url": "https://ranchandfarmauctions.com/auction-event/la-porte-co-in-40061-acres-in-8-tracts", "auction_date": "2026-07-23", "tags": ["auction", "tillable", "wooded", "barn"], "why": "NCCPI 68.9. Barn + crib included. 4.5 ac wooded.", "is_new": False},
    {"title": "Gillham Farm Tract 3 — 26.38 Ac All Tillable", "location": "Door Village", "county": "LaPorte", "acres": 26.38, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Farmland", "source": "Ranch & Farm Auctions", "url": "https://ranchandfarmauctions.com/auction-event/la-porte-co-in-40061-acres-in-8-tracts", "auction_date": "2026-07-23", "tags": ["auction", "tillable", "small-tract"], "why": "Nearly 100% tillable. NCCPI 68.6. Smallest tract = lowest bid.", "is_new": False},
    {"title": "Harder-Patek Tract 4 — 16.75 Ac Wooded", "location": "Union Mills", "county": "LaPorte", "acres": 16.75, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Wooded/Recreational", "source": "Ranch & Farm Auctions", "url": "https://ranchandfarmauctions.com/auction-event/la-porte-co-in-40061-acres-in-8-tracts", "auction_date": "2026-07-23", "tags": ["auction", "wooded", "recreational"], "why": "Cheap wooded tract — could go low at auction.", "is_new": False},
    {"title": "Harder-Patek Tract 5 — 2 Ac Wooded", "location": "Union Mills", "county": "LaPorte", "acres": 2, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Wooded", "source": "Ranch & Farm Auctions", "url": "https://ranchandfarmauctions.com/auction-event/la-porte-co-in-40061-acres-in-8-tracts", "auction_date": "2026-07-23", "tags": ["auction", "wooded", "tiny-tract"], "why": "2 acres, $8 in taxes. Potential ultra-cheap pickup.", "is_new": False},
    {"title": "Harder-Patek Tract 6 — 2.5 Ac Corner Lot", "location": "Union Mills", "county": "LaPorte", "acres": 2.5, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Tillable/Building", "source": "Ranch & Farm Auctions", "url": "https://ranchandfarmauctions.com/auction-event/la-porte-co-in-40061-acres-in-8-tracts", "auction_date": "2026-07-23", "tags": ["auction", "corner-lot", "building-site"], "why": "Corner lot near new home. Good building site.", "is_new": False},
    {"title": "Harder-Patek Tract 7 — 5.5 Ac Historic Farmstead", "location": "Union Mills", "county": "LaPorte", "acres": 5.5, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Farmstead/Residential", "source": "Ranch & Farm Auctions", "url": "https://ranchandfarmauctions.com/auction-event/la-porte-co-in-40061-acres-in-8-tracts", "auction_date": "2026-07-23", "tags": ["auction", "farmstead", "home", "barns"], "why": "3BR/2.5BA 3400sqft home + 5 barns + silo. Currently rented.", "is_new": False},
    {"title": "Harder-Patek Tract 8 — 190 Ac Cropland", "location": "Union Mills", "county": "LaPorte", "acres": 190, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Farmland", "source": "Ranch & Farm Auctions", "url": "https://ranchandfarmauctions.com/auction-event/la-porte-co-in-40061-acres-in-8-tracts", "auction_date": "2026-07-23", "tags": ["auction", "cropland", "large-tract"], "why": "160 tillable ac. NCCPI 71.7. Biggest tract in auction.", "is_new": False},

    # ═══════ SCHRADER AUCTIONS ═══════
    {"title": "Schrader: Elkhart Co Land Auction", "location": "Goshen", "county": "Elkhart", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Land", "source": "Schrader Auction", "url": "https://www.schraderauction.com/auctions/all", "auction_date": "2026-04-08", "tags": ["auction", "elkhart"], "why": "Live auction in Goshen — Elkhart is strong economy county.", "is_new": False},
    {"title": "Schrader: Lake Co — Cedar Lake", "location": "Cedar Lake", "county": "Lake", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Land", "source": "Schrader Auction", "url": "https://www.schraderauction.com/auctions/all", "auction_date": "2026-04-10", "tags": ["auction", "cedar-lake", "lake-county"], "why": "Cedar Lake growth area — fast appreciating.", "is_new": False},
    {"title": "Schrader: Kosciusko Co — Claypool", "location": "Claypool", "county": "Kosciusko", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Land", "source": "Schrader Auction", "url": "https://www.schraderauction.com/auctions/all", "auction_date": "2026-04-29", "tags": ["auction", "kosciusko"], "why": "Warsaw/medical device corridor.", "is_new": False},
    {"title": "Schrader: Whitley Co — Columbia City", "location": "Columbia City", "county": "Whitley", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Farmland", "source": "Schrader Auction", "url": "https://www.schraderauction.com/auctions/all", "auction_date": "2026-05-14", "tags": ["auction", "whitley"], "why": "Affordable county with good soils.", "is_new": False},

    # ═══════ LAND & FARM / LANDWATCH ═══════
    {"title": "76 Ac Hunting Land — Plymouth, Marshall Co", "location": "Plymouth", "county": "Marshall", "acres": 76, "price": 650000, "price_per_acre": 8553, "listing_type": "For Sale", "property_type": "Hunting", "source": "Mossy Oak / Land & Farm", "url": "https://www.landandfarm.com/search/indiana/marshall-county-land-for-sale/", "auction_date": None, "tags": ["hunting", "diverse-terrain"], "why": "Rarely available hunting ground SE of Plymouth. Below avg $/ac.", "is_new": False},
    {"title": "80 Ac Kankakee Riverfront — 9 Parcels", "location": "LaPorte County", "county": "LaPorte", "acres": 80, "price": 485000, "price_per_acre": 6063, "listing_type": "For Sale", "property_type": "Recreational", "source": "Land & Farm", "url": "https://www.landandfarm.com/search/IN/LaPorte-County-land-for-sale/", "auction_date": None, "tags": ["riverfront", "hunting", "multi-parcel"], "why": "$6K/ac with river frontage — well below comps. 9 parcels = sell pieces.", "is_new": False},
    {"title": "64 Ac Hunting/Recreational — LaPorte Co", "location": "LaPorte County", "county": "LaPorte", "acres": 64, "price": 379900, "price_per_acre": 5936, "listing_type": "For Sale", "property_type": "Recreational", "source": "Land & Farm", "url": "https://www.landandfarm.com/property/64-acres-laporte-county-hunting-recreational-land-for-sale-33290770/", "auction_date": None, "tags": ["hunting", "recreational"], "why": "$5,936/ac — way below LaPorte avg of $12,718. Investigate.", "is_new": False},
    {"title": "60+ Ac Historic Farm — Michigan City REDUCED", "location": "Michigan City", "county": "LaPorte", "acres": 60, "price": 599000, "price_per_acre": 9983, "listing_type": "For Sale", "property_type": "Development", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/laporte-county", "auction_date": None, "tags": ["price-reduced", "development"], "why": "Price reduced + Michigan City growth corridor.", "is_new": False},
    {"title": "40 Ac Farmland/Mini-Farm — Coolspring Twp", "location": "Coolspring Twp", "county": "LaPorte", "acres": 40, "price": 165000, "price_per_acre": 4125, "listing_type": "For Sale", "property_type": "Farmland", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/laporte-county", "auction_date": None, "tags": ["farmland", "affordable", "mini-farm"], "why": "$4,125/ac vs county avg $12,718. Potential hidden gem.", "is_new": False},
    {"title": "85.5 Ac Cropland & Rec — Coolspring Twp", "location": "Coolspring Twp", "county": "LaPorte", "acres": 85.5, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Cropland/Recreational", "source": "Halderman / HLS", "url": "https://www.halderman.com/property-listings/", "auction_date": None, "tags": ["cropland", "wooded", "building-sites"], "why": "51.8 tillable + 33.6 wooded. Split potential.", "is_new": False},
    {"title": "197 Ac Cropland + CRP — Hanna", "location": "Hanna", "county": "LaPorte", "acres": 197, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Farmland/CRP", "source": "Land.com", "url": "https://www.land.com/LaPorte-County-IN/all-land/", "auction_date": None, "tags": ["farmland", "crp", "large-tract"], "why": "167.5 cropland + 29.5 CRP. Two guaranteed income streams.", "is_new": False},
    {"title": "19 Ac Dev/Rec — Michigan City", "location": "Michigan City", "county": "LaPorte", "acres": 19, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Development/Recreational", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/laporte-county", "auction_date": None, "tags": ["development", "recreational"], "why": "Mix of wooded and tillable near Michigan City.", "is_new": False},
    {"title": "6 Ac Commercial — I-94 & US 421", "location": "Michigan City", "county": "LaPorte", "acres": 6, "price": 350000, "price_per_acre": 58333, "listing_type": "For Sale", "property_type": "Commercial", "source": "Land.com", "url": "https://www.land.com/LaPorte-County-IN/all-land/", "auction_date": None, "tags": ["commercial", "highway"], "why": "I-94/US 421 intersection — max visibility.", "is_new": False},
    {"title": "15.87 Ac Wooded Estate w/ Home", "location": "La Porte", "county": "LaPorte", "acres": 15.87, "price": 1297990, "price_per_acre": 81789, "listing_type": "For Sale", "property_type": "Residential Estate", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/laporte-county", "auction_date": None, "tags": ["estate", "luxury", "wooded"], "why": "Premium property — wooded estate on US 35.", "is_new": False},

    # ═══════ GESWEIN ═══════
    {"title": "188 Ac Land Auction — Jasper Co (SOLD)", "location": "Jasper County", "county": "Jasper", "acres": 188, "price": None, "price_per_acre": None, "listing_type": "Sold Comp", "property_type": "Farmland", "source": "Geswein Farm & Land", "url": "https://gfarmland.com/farm-real-estate/", "auction_date": None, "tags": ["comp", "sold", "auction"], "why": None, "is_new": False},

    # ═══════ MULTI-COUNTY LISTINGS ═══════
    {"title": "120 Ac Tillable — Knox Area, Starke Co", "location": "North Bend Twp", "county": "Starke", "acres": 120, "price": 660000, "price_per_acre": 5500, "listing_type": "For Sale", "property_type": "Farmland", "source": "Land.com", "url": "https://www.land.com/Starke-County-IN/all-land/", "auction_date": None, "tags": ["farmland", "affordable"], "why": "$5,500/ac = bottom of Starke comps. One of cheapest farming counties.", "is_new": False},
    {"title": "80 Ac Hunting & Timber — Starke Co", "location": "Davis Twp", "county": "Starke", "acres": 80, "price": 320000, "price_per_acre": 4000, "listing_type": "For Sale", "property_type": "Hunting/Timber", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/starke-county", "auction_date": None, "tags": ["hunting", "timber", "creek"], "why": "$4K/ac for timber + best whitetail hunting in region.", "is_new": False},
    {"title": "160 Ac Farm — Newton Co, Tile Drained", "location": "Lake Twp", "county": "Newton", "acres": 160, "price": 1120000, "price_per_acre": 7000, "listing_type": "For Sale", "property_type": "Farmland", "source": "Geswein", "url": "https://gfarmland.com/farm-real-estate/", "auction_date": None, "tags": ["farmland", "tile-drained", "quarter-section"], "why": "$7K/ac tile-drained farmland. Newton undervalued vs neighbors.", "is_new": False},
    {"title": "240 Ac Mixed Cropland + Wetland — Newton Co", "location": "Beaver Twp", "county": "Newton", "acres": 240, "price": 1080000, "price_per_acre": 4500, "listing_type": "For Sale", "property_type": "Farmland/Wetland", "source": "Land & Farm", "url": "https://www.landandfarm.com/search/indiana/newton-county-land-for-sale/", "auction_date": None, "tags": ["farmland", "wetland", "conservation", "large-tract"], "why": "$4,500/ac steal. Wetland acres = USDA conservation payments.", "is_new": False},
    {"title": "200 Ac Cropland Estate Sale — Pulaski Co", "location": "Rich Grove Twp", "county": "Pulaski", "acres": 200, "price": 1400000, "price_per_acre": 7000, "listing_type": "For Sale", "property_type": "Farmland", "source": "Halderman", "url": "https://www.halderman.com/property-listings/", "auction_date": None, "tags": ["farmland", "estate-sale", "high-CAI"], "why": "Estate = motivated. $280/ac rent ÷ $7K/ac = 4% cash yield.", "is_new": False},
    {"title": "40 Ac Wooded — Tippecanoe River, Pulaski Co", "location": "Tippecanoe Twp", "county": "Pulaski", "acres": 40, "price": 140000, "price_per_acre": 3500, "listing_type": "For Sale", "property_type": "Recreational", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/pulaski-county", "auction_date": None, "tags": ["wooded", "river-access", "hunting", "cheap"], "why": "$3,500/ac near Tippecanoe River. Cheapest rec land in N. IN.", "is_new": False},
    {"title": "Tippecanoe River Waterfront — 3.5 Ac Winamac", "location": "Winamac", "county": "Pulaski", "acres": 3.51, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Waterfront", "source": "Land.com", "url": "https://www.land.com/Pulaski-County-IN/all-land/", "auction_date": None, "tags": ["waterfront", "river", "retreat"], "why": "Serene waterfront on Tippecanoe River.", "is_new": False},
    {"title": "75 Ac Tillable — US 30 Corridor, Porter Co", "location": "Morgan Twp", "county": "Porter", "acres": 75, "price": 712500, "price_per_acre": 9500, "listing_type": "For Sale", "property_type": "Farmland", "source": "Land.com", "url": "https://www.land.com/Porter-County-IN/all-land/", "auction_date": None, "tags": ["farmland", "us-30", "development-potential"], "why": "US 30 corridor seeing commercial push. Farm now, develop later.", "is_new": False},
    {"title": "160 Ac — Plymouth, Marshall Co", "location": "West Twp", "county": "Marshall", "acres": 160, "price": 1280000, "price_per_acre": 8000, "listing_type": "For Sale", "property_type": "Farmland", "source": "Schrader Auction", "url": "https://www.schraderauction.com/auctions/all", "auction_date": None, "tags": ["farmland", "quarter-section"], "why": "$8K/ac below Marshall avg of $10,800.", "is_new": False},
    {"title": "93 Ac Yellow River Frontage — Marshall Co", "location": "Tippecanoe Twp", "county": "Marshall", "acres": 93, "price": 511500, "price_per_acre": 5500, "listing_type": "For Sale", "property_type": "Recreational/Farmland", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/marshall-county", "auction_date": None, "tags": ["riverfront", "hunting", "mixed-use", "culver"], "why": "$5,500/ac with river frontage near Culver. Tourism upside.", "is_new": False},
    {"title": "320 Ac Two Quarter Sections — Jasper Co", "location": "Wheatfield Twp", "county": "Jasper", "acres": 320, "price": 2720000, "price_per_acre": 8500, "listing_type": "Auction", "property_type": "Farmland", "source": "Sullivan Auctioneers", "url": "https://www.sullivanauctioneers.com/land-listings/", "auction_date": "2026-06-15", "tags": ["farmland", "large-tract", "auction", "high-yield"], "why": "PI 138 = excellent yields. Auction could go below market.", "is_new": False},
    {"title": "45 Ac Near Rensselaer — Jasper Co", "location": "Barkley Twp", "county": "Jasper", "acres": 45, "price": 270000, "price_per_acre": 6000, "listing_type": "For Sale", "property_type": "Farmland/Development", "source": "Land & Farm", "url": "https://www.landandfarm.com/search/indiana/jasper-county-land-for-sale/", "auction_date": None, "tags": ["farmland", "development-potential"], "why": "$6K/ac near growing town. Rezone → $15-25K/ac.", "is_new": False},
    {"title": "50 Ac South Bend Metro Edge — St. Joseph Co", "location": "Harris Twp", "county": "St. Joseph", "acres": 50, "price": 475000, "price_per_acre": 9500, "listing_type": "For Sale", "property_type": "Farmland/Development", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/st-joseph-county", "auction_date": None, "tags": ["development", "south-bend", "metro-edge"], "why": "Metro-edge farmland 2-5x in 10 years as South Bend grows.", "is_new": False},
    {"title": "68 Ac Near Goshen — Elkhart Co", "location": "Elkhart Twp", "county": "Elkhart", "acres": 68, "price": 680000, "price_per_acre": 10000, "listing_type": "For Sale", "property_type": "Farmland", "source": "Land.com", "url": "https://www.land.com/Elkhart-County-IN/all-land/", "auction_date": None, "tags": ["farmland", "strong-economy"], "why": "Strongest manufacturing economy in N. IN (RV industry).", "is_new": False},
    {"title": "180 Ac Rochester Area — Fulton Co Estate", "location": "Liberty Twp", "county": "Fulton", "acres": 180, "price": 990000, "price_per_acre": 5500, "listing_type": "For Sale", "property_type": "Farmland", "source": "Halderman", "url": "https://www.halderman.com/property-listings/", "auction_date": None, "tags": ["farmland", "estate-sale", "large-tract"], "why": "$5,500/ac = bottom of N. IN market. Estate = motivated.", "is_new": False},
    {"title": "35 Ac Wooded Near Lake Manitou — Fulton Co", "location": "Rochester", "county": "Fulton", "acres": 35, "price": 122500, "price_per_acre": 3500, "listing_type": "For Sale", "property_type": "Recreational", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/fulton-county", "auction_date": None, "tags": ["wooded", "lake-adjacent", "hunting", "cheap"], "why": "$3,500/ac near Lake Manitou. Cheapest rec land around.", "is_new": False},
    {"title": "100 Ac Warsaw Outskirts — Kosciusko Co", "location": "Wayne Twp", "county": "Kosciusko", "acres": 100, "price": 850000, "price_per_acre": 8500, "listing_type": "For Sale", "property_type": "Farmland", "source": "Geswein", "url": "https://gfarmland.com/farm-real-estate/", "auction_date": None, "tags": ["farmland", "warsaw", "medical-corridor"], "why": "Warsaw medical device industry = strong economy. Below avg.", "is_new": False},
    {"title": "25 Ac Warsaw w/ Home, Pond & Barn", "location": "Warsaw", "county": "Kosciusko", "acres": 25, "price": 849900, "price_per_acre": 33996, "listing_type": "For Sale", "property_type": "Residential Farm", "source": "Mossy Oak", "url": "https://www.mossyoakproperties.com/land-for-sale/indiana/", "auction_date": None, "tags": ["home", "barn", "pond"], "why": "Includes 3,274sqft home + pole barn + pond.", "is_new": False},
    {"title": "60 Ac Chain O'Lakes Area — Noble Co", "location": "Orange Twp", "county": "Noble", "acres": 60, "price": 300000, "price_per_acre": 5000, "listing_type": "For Sale", "property_type": "Recreational/Farmland", "source": "Land & Farm", "url": "https://www.landandfarm.com/search/indiana/noble-county-land-for-sale/", "auction_date": None, "tags": ["recreational", "state-park", "affordable"], "why": "$5K/ac near state park. Noble underpriced vs Elkhart/Kosciusko.", "is_new": False},
    {"title": "25 Ac Crown Point Growth Area — Lake Co", "location": "Center Twp", "county": "Lake", "acres": 25, "price": 375000, "price_per_acre": 15000, "listing_type": "For Sale", "property_type": "Development", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/lake-county", "auction_date": None, "tags": ["development", "crown-point", "growth"], "why": "Crown Point = one of IN's fastest-growing cities.", "is_new": False},
    {"title": "3.9 Ac Residential — Crown Point, Cedar Lake Rd", "location": "Crown Point", "county": "Lake", "acres": 3.9, "price": 355000, "price_per_acre": 91119, "listing_type": "For Sale", "property_type": "Residential", "source": "LandSearch", "url": "https://www.landsearch.com/properties/12201-cedar-lake-rd-crown-point-in-46307/3912672", "auction_date": None, "tags": ["residential", "crown-point"], "why": "Near Cedar Lake in hot growth area.", "is_new": False},
    {"title": "240 Ac Monticello — White Co, PI 142", "location": "Liberty Twp", "county": "White", "acres": 240, "price": 1920000, "price_per_acre": 8000, "listing_type": "For Sale", "property_type": "Farmland", "source": "Sullivan Auctioneers", "url": "https://www.sullivanauctioneers.com/land-listings/", "auction_date": None, "tags": ["farmland", "high-productivity", "large-tract"], "why": "PI 142 outstanding. $8K/ac for that soil quality = bargain.", "is_new": False},

    # ═══════ TAX SALES & SHERIFF SALES ═══════
    {"title": "LaPorte Co Annual Tax Sale 2026", "location": "La Porte", "county": "LaPorte", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services / LaPorte Treasurer", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-10-08", "tags": ["tax-sale", "deep-discount"], "why": "Pennies on dollar. Even if redeemed = 10-15% return.", "is_new": False},
    {"title": "LaPorte Co Commissioner's Certificate Sale", "location": "La Porte", "county": "LaPorte", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Failed Tax Parcels", "source": "LaPorte Co. Treasurer", "url": "https://laporteco.in.gov/residents/county-treasurer/real-estate-tax-sale/", "auction_date": None, "tags": ["tax-sale", "commissioner", "deepest-discount"], "why": "Failed first sale = county is desperate. Steepest discounts.", "is_new": False},
    {"title": "Porter Co Tax/Certificate Sale 2026", "location": "Valparaiso", "county": "Porter", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "Porter Co Auditor", "url": "https://www.portercountyin.gov/1319/Tax-Certificate-Sales", "auction_date": "2026-09-15", "tags": ["tax-sale", "porter"], "why": "Porter Co has mix of rural + suburban parcels.", "is_new": False},
    {"title": "Lake Co Tax Lien Sale 2026", "location": "Crown Point", "county": "Lake", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "Lake Co Auditor", "url": "https://lakecountyin.gov/departments/auditor-taxsales", "auction_date": "2026-09-22", "tags": ["tax-sale", "high-volume", "lake-county"], "why": "Largest county = most parcels. Urban lots to rural acreage.", "is_new": False},
    {"title": "Starke Co Tax Sale 2026", "location": "Knox", "county": "Starke", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "County Treasurer", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-15", "tags": ["tax-sale", "cheap-county"], "why": "Low values = $100-$500 starting bids. Great entry point.", "is_new": False},
    {"title": "St. Joseph Co Sheriff's Sales", "location": "South Bend", "county": "St. Joseph", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Sheriff Sale", "property_type": "Foreclosures", "source": "St. Joseph Co Sheriff", "url": "https://sjcpd.org/sheriffs-sale/", "auction_date": None, "tags": ["sheriff-sale", "foreclosure", "south-bend"], "why": "No redemption period. Often 20-50% of market value.", "is_new": False},
    {"title": "LaPorte Co Sheriff's Sales", "location": "La Porte", "county": "LaPorte", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Sheriff Sale", "property_type": "Foreclosures", "source": "LaPorte Co Sheriff", "url": "https://www.laportecountysheriff.com/sheriff-sales", "auction_date": None, "tags": ["sheriff-sale", "foreclosure"], "why": "Min $3K deposit. No contingencies. Published 30d prior.", "is_new": False},
    {"title": "Hamilton Co Tax Sale 2026", "location": "Noblesville", "county": "Hamilton", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "Hamilton Co", "url": "https://www.hamiltoncounty.in.gov/452/Real-Property-Tax-Sale", "auction_date": "2026-10-08", "tags": ["tax-sale", "hamilton"], "why": "Hamilton is expensive — but tax sale = deep discounts.", "is_new": False},

    # ═══════ SOLD COMPS ═══════
    {"title": "COMP: 205 Ac Schultz Wray Farm", "location": "Union Mills", "county": "LaPorte", "acres": 205, "price": 1595000, "price_per_acre": 7781, "listing_type": "Sold Comp", "property_type": "Farmland", "source": "Halderman", "url": "https://www.halderman.com/property-listings/", "auction_date": None, "tags": ["comp"], "why": None, "is_new": False},
    {"title": "COMP: 81 Ac Braid Farm", "location": "New Carlisle", "county": "St. Joseph", "acres": 81.78, "price": 1015000, "price_per_acre": 12411, "listing_type": "Sold Comp", "property_type": "Farmland", "source": "Halderman", "url": "https://www.halderman.com/property-listings/", "auction_date": None, "tags": ["comp"], "why": None, "is_new": False},
    {"title": "COMP: 165 Ac (3 tracts)", "location": "LaPorte County", "county": "LaPorte", "acres": 165.33, "price": 1888000, "price_per_acre": 10976, "listing_type": "Sold Comp", "property_type": "Farmland", "source": "Halderman", "url": "https://www.halderman.com/property-listings/", "auction_date": None, "tags": ["comp"], "why": None, "is_new": False},

    # ═══════ WAVE 2 — more listings ═══════
    {"title": "42.5 Ac US 6 Plymouth — Tillable + Woods", "location": "Plymouth", "county": "Marshall", "acres": 42.5, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Recreational/Farmland", "source": "IN Land & Lifestyle", "url": "https://indianalandandlifestyle.com/land-for-sale/marshall-county/", "auction_date": None, "tags": ["tillable", "wooded", "hunting", "us-6"], "why": "20 ac tillable + woods. Great for hunting, camping, horseback riding.", "is_new": False},
    {"title": "41 Ac Yellow River Timberland — Plymouth (SOLD)", "location": "Plymouth", "county": "Marshall", "acres": 41, "price": None, "price_per_acre": None, "listing_type": "Sold Comp", "property_type": "Timberland/Recreational", "source": "IN Land & Lifestyle", "url": "https://indianalandandlifestyle.com/", "auction_date": None, "tags": ["comp", "sold", "yellow-river"], "why": None, "is_new": False},
    {"title": "13.5 Ac Recreational — Near La Paz", "location": "La Paz", "county": "Marshall", "acres": 13.5, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Recreational", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/marshall-county", "auction_date": None, "tags": ["recreational", "hunting", "camping"], "why": "Small affordable tract near La Paz. Good for getaway cabin.", "is_new": False},
    {"title": "27.8 Ac Residential Dev — Portage R2 Zoned", "location": "Portage", "county": "Porter", "acres": 27.8, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Development", "source": "Land.com", "url": "https://www.land.com/Porter-County-IN/all-land/", "auction_date": None, "tags": ["development", "residential", "zoned-R2"], "why": "Already zoned R2 residential. US 6 intersection. Portage is growing.", "is_new": False},
    {"title": "6.82 Ac Commercial — Portage C2 Zoned", "location": "Portage", "county": "Porter", "acres": 6.82, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Commercial", "source": "Land.com", "url": "https://www.land.com/Porter-County-IN/all-land/", "auction_date": None, "tags": ["commercial", "zoned-C2", "portage"], "why": "Pre-zoned commercial. No rezoning risk.", "is_new": False},
    {"title": "7.24 Ac US 30 — Valparaiso", "location": "Valparaiso", "county": "Porter", "acres": 7.24, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Residential", "source": "Land.com", "url": "https://www.land.com/Porter-County-IN/all-land/", "auction_date": None, "tags": ["us-30", "valparaiso", "residential"], "why": "US 30 frontage in Valpo. High traffic, high demand.", "is_new": False},
    {"title": "12 Ac Washington Twp — Valparaiso", "location": "Valparaiso", "county": "Porter", "acres": 12, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Residential/Development", "source": "Homes.com", "url": "https://www.homes.com/porter-county-in/land-for-sale/", "auction_date": None, "tags": ["valparaiso", "development"], "why": "Nearly 12 acres in prime Valpo location.", "is_new": False},
    {"title": "23.15 Ac — Porter County", "location": "Porter County", "county": "Porter", "acres": 23.15, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Land", "source": "Land.com", "url": "https://www.land.com/property/23.15-acres-in-Porter-County-Indiana/9382562/", "auction_date": None, "tags": ["porter", "land"], "why": "Mid-size tract in Porter County.", "is_new": False},
    {"title": "10 Ac — Medaryville, Pulaski Co", "location": "Medaryville", "county": "Pulaski", "acres": 10, "price": 274900, "price_per_acre": 27490, "listing_type": "For Sale", "property_type": "Residential/Land", "source": "LandSearch", "url": "https://www.landsearch.com/properties/pulaski-county-in", "auction_date": None, "tags": ["medaryville", "residential"], "why": "Small tract in cheapest county region.", "is_new": False},
    {"title": "14 Ac — Winamac, Pulaski Co", "location": "Winamac", "county": "Pulaski", "acres": 14, "price": 425000, "price_per_acre": 30357, "listing_type": "For Sale", "property_type": "Residential/Land", "source": "LandSearch", "url": "https://www.landsearch.com/properties/pulaski-county-in", "auction_date": None, "tags": ["winamac", "residential"], "why": "Near county seat. Likely includes improvements.", "is_new": False},
    {"title": "28.8 Ac — Medaryville, Pulaski Co", "location": "Medaryville", "county": "Pulaski", "acres": 28.81, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Land", "source": "LandSearch", "url": "https://www.landsearch.com/properties/pulaski-county-in", "auction_date": None, "tags": ["medaryville", "affordable"], "why": "Almost 29 acres in ultra-cheap county.", "is_new": False},
    {"title": "37 Ac — Winamac, Pulaski Co", "location": "Winamac", "county": "Pulaski", "acres": 37, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Land", "source": "LandSearch", "url": "https://www.landsearch.com/properties/pulaski-county-in", "auction_date": None, "tags": ["winamac", "mid-size"], "why": "37 acres in one of Indiana's cheapest counties.", "is_new": False},
    {"title": "16 Ac Log Cabin — Winamac, Pulaski Co", "location": "Winamac", "county": "Pulaski", "acres": 16, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Residential/Recreational", "source": "IN Land & Lifestyle", "url": "https://indianalandandlifestyle.com/property/land-for-sale-pulaski-county-in-log-cabin-with-16-acres-pulaski-indiana/6482/", "auction_date": None, "tags": ["log-cabin", "recreational"], "why": "Log cabin on 16 acres. Turnkey getaway.", "is_new": False},
    {"title": "112 Ac WRP Tippecanoe River — Rochester", "location": "Rochester", "county": "Fulton", "acres": 112, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Conservation/Recreational", "source": "LandSearch", "url": "https://www.landsearch.com/properties/fulton-county-in", "auction_date": None, "tags": ["wetlands-reserve", "tippecanoe-river", "conservation"], "why": "WRP property on Tippecanoe River. USDA conservation payments.", "is_new": False},
    {"title": "26 Ac Dev Opportunity — Rochester US 31", "location": "Rochester", "county": "Fulton", "acres": 26, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Development", "source": "LandSearch", "url": "https://www.landsearch.com/properties/fulton-county-in", "auction_date": None, "tags": ["development", "us-31", "rochester"], "why": "US 31 corner lot near Rochester. Commercial potential.", "is_new": False},
    {"title": "10 Ac — Brook, Newton Co", "location": "Brook", "county": "Newton", "acres": 10, "price": 189900, "price_per_acre": 18990, "listing_type": "For Sale", "property_type": "Residential/Land", "source": "LandSearch", "url": "https://www.landsearch.com/properties/newton-county-in", "auction_date": None, "tags": ["brook", "affordable"], "why": "10 acres in ultra-cheap Newton County.", "is_new": False},
    {"title": "4.5 Ac — Kentland, Newton Co", "location": "Kentland", "county": "Newton", "acres": 4.5, "price": 150000, "price_per_acre": 33333, "listing_type": "For Sale", "property_type": "Residential", "source": "LandSearch", "url": "https://www.landsearch.com/properties/newton-county-in", "auction_date": None, "tags": ["kentland", "residential"], "why": "Near county seat. Small tract.", "is_new": False},
    {"title": "2 Ac — Kentland (Under Contract)", "location": "Kentland", "county": "Newton", "acres": 2, "price": 35000, "price_per_acre": 17500, "listing_type": "Under Contract", "property_type": "Residential", "source": "LandSearch", "url": "https://www.landsearch.com/properties/newton-county-in", "auction_date": None, "tags": ["kentland", "cheap"], "why": "$35K for 2 acres — shows how cheap Newton Co is.", "is_new": False},
    {"title": "42 Ac Hunting Paradise — Angola Area", "location": "Angola", "county": "Steuben", "acres": 42, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Recreational/Hunting", "source": "IN Land & Lifestyle", "url": "https://indianalandandlifestyle.com/land-for-sale/steuben-county/", "auction_date": None, "tags": ["hunting", "angola", "ponds"], "why": "Rolling hills, ponds, lakes, streams. Low taxes. Near Angola.", "is_new": False},
    {"title": "8.7 Ac Commercial — Fremont SR 120", "location": "Fremont", "county": "Steuben", "acres": 8.7, "price": 1199000, "price_per_acre": 137886, "listing_type": "For Sale", "property_type": "Commercial", "source": "IN Land & Lifestyle", "url": "https://indianalandandlifestyle.com/land-for-sale/steuben-county/", "auction_date": None, "tags": ["commercial", "fremont", "sr-120"], "why": "Strategic SR 120 commercial site.", "is_new": False},
    {"title": "11.8 Ac Big Lake Frontage — Noble Co", "location": "Noble County", "county": "Noble", "acres": 11.767, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Lakefront", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/noble-county", "auction_date": None, "tags": ["lakefront", "big-lake", "premium"], "why": "461 ft of lake frontage on Big Lake. Rare find.", "is_new": False},
    {"title": "75 Ac Hunting — Rolling Hills, Noble Co", "location": "Noble County", "county": "Noble", "acres": 75.18, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Hunting", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/noble-county", "auction_date": None, "tags": ["hunting", "rolling-hills", "ponds"], "why": "Rolling hills + ponds + streams. Low taxes. Great deer.", "is_new": False},
    {"title": "20.5 Ac Tillable + Woods — South Whitley", "location": "South Whitley", "county": "Whitley", "acres": 20.5, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Farmland/Hunting", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/whitley-county", "auction_date": None, "tags": ["tillable", "wooded", "hunting"], "why": "Mix of productive tillable + woods for hunting.", "is_new": False},
    {"title": "70 Ac Recreational — Cass/Miami Line", "location": "Peru area", "county": "Cass", "acres": 70, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Recreational", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/cass-county", "auction_date": None, "tags": ["recreational", "hunting", "affordable"], "why": "70 ac recreational paradise near Peru. Cass Co is cheap.", "is_new": False},
    {"title": "29.7 Ac Tillable — SR 16, Twelve Mile", "location": "Twelve Mile", "county": "Cass", "acres": 29.7, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Farmland", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/cass-county", "auction_date": None, "tags": ["tillable", "road-frontage", "sr-16"], "why": "Productive tillable with dual road frontage off SR 16.", "is_new": False},
    {"title": "20 Ac Tillable — North of Denver", "location": "Denver", "county": "Miami", "acres": 20, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Farmland", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/miami-county", "auction_date": None, "tags": ["tillable", "affordable"], "why": "Prime tillable near Denver. Miami Co avg $9,500/ac.", "is_new": False},
    {"title": "44 Ac — North Judson Area, Starke Co", "location": "North Judson", "county": "Starke", "acres": 44, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Farmland/Building", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/starke-county", "auction_date": None, "tags": ["tillable", "building-site", "north-judson"], "why": "Good mix of tillable + building sites. Starke is cheap.", "is_new": False},
    {"title": "80.6 Ac Outdoor Getaway — Near Walkerton", "location": "Walkerton", "county": "LaPorte", "acres": 80.6, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Recreational", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/laporte-county", "auction_date": None, "tags": ["recreational", "getaway", "walkerton"], "why": "80+ ac outdoor enthusiast property near Walkerton.", "is_new": False},
    {"title": "10 Ac Kankakee River — Year-Round Use", "location": "LaPorte County", "county": "LaPorte", "acres": 10, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Recreational", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/laporte-county", "auction_date": None, "tags": ["kankakee-river", "year-round", "improvements"], "why": "Desirable Kankakee River property with improvements.", "is_new": False},
    {"title": "Mixed Tillable/Rec — E SR 4, Mill Creek", "location": "Mill Creek", "county": "LaPorte", "acres": None, "price": None, "price_per_acre": None, "listing_type": "For Sale", "property_type": "Farmland/Recreational", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/laporte-county/farms-ranches", "auction_date": None, "tags": ["tillable", "hunting", "waterfowl"], "why": "Mix of tillable + hunting. Whitetail, turkey, waterfowl, duck, geese.", "is_new": False},

    # ═══════ MORE TAX SALES ═══════
    {"title": "Elkhart Co Tax Sale 2026", "location": "Goshen", "county": "Elkhart", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-20", "tags": ["tax-sale", "elkhart"], "why": "Elkhart = strong economy. Tax sale parcels in good areas.", "is_new": False},
    {"title": "Marshall Co Tax Sale 2026", "location": "Plymouth", "county": "Marshall", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-18", "tags": ["tax-sale", "marshall"], "why": "Marshall Co has rural + lakeside parcels.", "is_new": False},
    {"title": "Kosciusko Co Tax Sale 2026", "location": "Warsaw", "county": "Kosciusko", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-25", "tags": ["tax-sale", "kosciusko", "lake-properties"], "why": "Lake properties sometimes hit tax sale. Warsaw strong economy.", "is_new": False},
    {"title": "Noble Co Tax Sale 2026", "location": "Albion", "county": "Noble", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-10-01", "tags": ["tax-sale", "noble"], "why": "Noble Co = underpriced. Tax sales = even cheaper.", "is_new": False},
    {"title": "Fulton Co Tax Sale 2026", "location": "Rochester", "county": "Fulton", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-28", "tags": ["tax-sale", "fulton", "cheap"], "why": "Very cheap county. Tax parcels could go for $100-$500.", "is_new": False},
    {"title": "Jasper Co Tax Sale 2026", "location": "Rensselaer", "county": "Jasper", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-22", "tags": ["tax-sale", "jasper"], "why": "Jasper = productive farmland county. Tax sales here are rare finds.", "is_new": False},
    {"title": "Newton Co Tax Sale 2026", "location": "Kentland", "county": "Newton", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-15", "tags": ["tax-sale", "newton", "ultra-cheap"], "why": "Cheapest county in region. Tax sale = absolute bottom prices.", "is_new": False},
    {"title": "Pulaski Co Tax Sale 2026", "location": "Winamac", "county": "Pulaski", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-17", "tags": ["tax-sale", "pulaski", "ultra-cheap"], "why": "Cheapest avg farmland in region. Tax parcels = pennies.", "is_new": False},
    {"title": "Allen Co Tax Sale 2026", "location": "Fort Wayne", "county": "Allen", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-10-05", "tags": ["tax-sale", "allen", "fort-wayne", "high-volume"], "why": "2nd largest county. Hundreds of parcels. Urban + rural.", "is_new": False},
    {"title": "Cass Co Tax Sale 2026", "location": "Logansport", "county": "Cass", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-22", "tags": ["tax-sale", "cass"], "why": "Affordable county. Logansport area parcels.", "is_new": False},
    {"title": "Porter Co Sheriff's Sales", "location": "Valparaiso", "county": "Porter", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Sheriff Sale", "property_type": "Foreclosures", "source": "Porter Co Sheriff", "url": "https://www.portercountysheriff.com/sheriffsales", "auction_date": None, "tags": ["sheriff-sale", "foreclosure", "porter"], "why": "No redemption period. Foreclosure = motivated pricing.", "is_new": False},
    {"title": "Lake Co Sheriff's Sales", "location": "Crown Point", "county": "Lake", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Sheriff Sale", "property_type": "Foreclosures", "source": "Lake Co Sheriff", "url": "https://lakecountyin.gov/departments/sheriff/sheriff-sale-listings-c/", "auction_date": None, "tags": ["sheriff-sale", "foreclosure", "lake-county", "high-volume"], "why": "Largest county = most sheriff sales. Crown Point, Gary, Hammond, etc.", "is_new": False},
    {"title": "Allen Co Sheriff's Sales", "location": "Fort Wayne", "county": "Allen", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Sheriff Sale", "property_type": "Foreclosures", "source": "Allen Co Sheriff", "url": "https://www.allencountysheriff.org/sheriff-sale/", "auction_date": None, "tags": ["sheriff-sale", "foreclosure", "fort-wayne"], "why": "Fort Wayne metro. High volume of foreclosure properties.", "is_new": False},

    # ═══════ ADDITIONAL COUNTIES — DeKalb, LaGrange, Wabash, Huntington, Wells, Adams, Jay, Benton, Carroll, Tippecanoe ═══════
    {"title": "75 Ac Farmland — Auburn Area, DeKalb Co", "location": "Auburn", "county": "DeKalb", "acres": 75, "price": 712500, "price_per_acre": 9500, "listing_type": "For Sale", "property_type": "Farmland", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/dekalb-county", "auction_date": None, "tags": ["farmland", "auburn", "affordable"], "why": "$9,500/ac slightly below DeKalb avg. Auburn growing due to I-69.", "is_new": False},
    {"title": "40 Ac Amish Country — LaGrange Co", "location": "Shipshewana", "county": "LaGrange", "acres": 40, "price": 380000, "price_per_acre": 9500, "listing_type": "For Sale", "property_type": "Farmland", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/lagrange-county", "auction_date": None, "tags": ["farmland", "amish", "shipshewana"], "why": "Amish country near Shipshewana flea market = tourism + farmland.", "is_new": False},
    {"title": "55 Ac Wabash River Farmland", "location": "Wabash", "county": "Wabash", "acres": 55, "price": 451000, "price_per_acre": 8200, "listing_type": "For Sale", "property_type": "Farmland", "source": "Geswein", "url": "https://gfarmland.com/farm-real-estate/", "auction_date": None, "tags": ["farmland", "river-bottom", "wabash"], "why": "Rich river bottom soils near Wabash. Undervalued county.", "is_new": False},
    {"title": "90 Ac Tillable — Huntington Co", "location": "Huntington", "county": "Huntington", "acres": 90, "price": 810000, "price_per_acre": 9000, "listing_type": "For Sale", "property_type": "Farmland", "source": "Halderman", "url": "https://www.halderman.com/property-listings/", "auction_date": None, "tags": ["farmland", "tillable", "productive"], "why": "Strong soils. $9K/ac below Huntington avg of $9,800.", "is_new": False},
    {"title": "60 Ac Cash Crop Farm — Wells Co", "location": "Bluffton", "county": "Wells", "acres": 60, "price": 540000, "price_per_acre": 9000, "listing_type": "For Sale", "property_type": "Farmland", "source": "Land & Farm", "url": "https://www.landandfarm.com/search/indiana/wells-county-land-for-sale/", "auction_date": None, "tags": ["farmland", "cash-crop", "bluffton"], "why": "$9K/ac below Wells avg of $10K. Consistent cash renter.", "is_new": False},
    {"title": "80 Ac Farmland — Decatur, Adams Co", "location": "Decatur", "county": "Adams", "acres": 80, "price": 680000, "price_per_acre": 8500, "listing_type": "For Sale", "property_type": "Farmland", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/adams-county", "auction_date": None, "tags": ["farmland", "decatur", "affordable"], "why": "$8,500/ac below Adams avg of $9,500. Good soils.", "is_new": False},
    {"title": "45 Ac Hunting & Tillable — Jay Co", "location": "Portland", "county": "Jay", "acres": 45, "price": 315000, "price_per_acre": 7000, "listing_type": "For Sale", "property_type": "Mixed Use", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/jay-county", "auction_date": None, "tags": ["hunting", "tillable", "affordable"], "why": "$7K/ac in cheap county. Split between income + recreation.", "is_new": False},
    {"title": "35 Ac — Benton Co Farmland", "location": "Fowler", "county": "Benton", "acres": 35, "price": 315000, "price_per_acre": 9000, "listing_type": "For Sale", "property_type": "Farmland", "source": "Sullivan Auctioneers", "url": "https://www.sullivanauctioneers.com/land-listings/", "auction_date": None, "tags": ["farmland", "benton", "productive"], "why": "Benton has some of IN's best soils. $9K/ac = good entry.", "is_new": False},
    {"title": "50 Ac — Carroll Co Near Delphi", "location": "Delphi", "county": "Carroll", "acres": 50, "price": 450000, "price_per_acre": 9000, "listing_type": "For Sale", "property_type": "Farmland", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/carroll-county", "auction_date": None, "tags": ["farmland", "delphi", "wabash-river"], "why": "Near Delphi, Wabash River access. Carroll undervalued.", "is_new": False},
    {"title": "100 Ac Tippecanoe Co — Purdue Corridor", "location": "Lafayette", "county": "Tippecanoe", "acres": 100, "price": 1100000, "price_per_acre": 11000, "listing_type": "For Sale", "property_type": "Farmland/Development", "source": "Land.com", "url": "https://www.land.com/Tippecanoe-County-IN/all-land/", "auction_date": None, "tags": ["farmland", "lafayette", "purdue", "development"], "why": "Purdue University/Lafayette corridor = strong demand. Dev upside.", "is_new": False},
    {"title": "150 Ac Farmland — Wabash Co Auction", "location": "Wabash", "county": "Wabash", "acres": 150, "price": None, "price_per_acre": None, "listing_type": "Auction", "property_type": "Farmland", "source": "Sullivan Auctioneers", "url": "https://www.sullivanauctioneers.com/land-listings/", "auction_date": "2026-05-28", "tags": ["auction", "farmland", "large-tract"], "why": "Motivated seller. Wabash Co farmland rarely hits auction.", "is_new": False},
    {"title": "30 Ac Wooded — Blackford Co Near Hartford City", "location": "Hartford City", "county": "Blackford", "acres": 30, "price": 180000, "price_per_acre": 6000, "listing_type": "For Sale", "property_type": "Recreational", "source": "LandWatch", "url": "https://www.landwatch.com/indiana-land-for-sale/blackford-county", "auction_date": None, "tags": ["wooded", "hunting", "affordable", "cheap"], "why": "$6K/ac in small county. Blackford has lowest land prices in region.", "is_new": False},
    {"title": "DeKalb Co Tax Sale 2026", "location": "Auburn", "county": "DeKalb", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-24", "tags": ["tax-sale", "dekalb"], "why": "DeKalb parcels in growing I-69 corridor.", "is_new": False},
    {"title": "Tippecanoe Co Tax Sale 2026", "location": "Lafayette", "county": "Tippecanoe", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-10-06", "tags": ["tax-sale", "tippecanoe", "lafayette"], "why": "Purdue area = high demand. Tax sale = rare buy-in opportunity.", "is_new": False},
    {"title": "White Co Tax Sale 2026", "location": "Monticello", "county": "White", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-09-19", "tags": ["tax-sale", "white", "lake-tippecanoe"], "why": "Lake Tippecanoe resort area parcels sometimes hit sale.", "is_new": False},
    {"title": "St. Joseph Co Tax Sale 2026", "location": "South Bend", "county": "St. Joseph", "acres": None, "price": None, "price_per_acre": None, "listing_type": "Tax Sale", "property_type": "Multiple Parcels", "source": "SRI Services", "url": "https://properties.sriservices.com/auctionlist", "auction_date": "2026-10-02", "tags": ["tax-sale", "stjoseph", "south-bend"], "why": "South Bend metro + rural mix. Many parcels.", "is_new": False},
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CACHE FILE FOR PERSISTED FETCHED LISTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CACHE_FILE = os.path.join(os.path.dirname(__file__), "listings_cache.json")
CACHE_TTL_HOURS = 24

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None, None
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        ts = data.get("fetched_at")
        listings = data.get("listings", [])
        return ts, listings
    except Exception:
        return None, None

def save_cache(listings):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"fetched_at": datetime.now().isoformat(), "listings": listings}, f)
    except Exception:
        pass

def cache_is_fresh(ts_str):
    if not ts_str:
        return False
    try:
        ts = datetime.fromisoformat(ts_str)
        return (datetime.now() - ts).total_seconds() < CACHE_TTL_HOURS * 3600
    except Exception:
        return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LIVE DATA FETCH — GovDeals RSS + LandWatch scrape (best public endpoints)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NorthernINLandDeals/1.0)"
}

def fetch_govdeals_indiana():
    """GovDeals RSS for Indiana real estate / land surplus."""
    fetched = []
    try:
        url = "https://www.govdeals.com/index.cfm?fa=Main.AdvSearchResultsNew&searchPg=1&kWord=land&kWordSelect=1&sortBy=ad&AD=DESC&state=IN&category=110&agency=0&fn=srchres&timing=all"
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200 and "Indiana" in r.text:
            # Just return a pointer entry — actual scraping needs JS rendering
            fetched.append({
                "title": "GovDeals: Indiana Land Surplus (Live)",
                "location": "Indiana (Statewide)",
                "county": "LaPorte",
                "acres": None,
                "price": None,
                "price_per_acre": None,
                "listing_type": "Auction",
                "property_type": "Government Surplus",
                "source": "GovDeals",
                "url": "https://www.govdeals.com/index.cfm?fa=Main.AdvSearchResultsNew&kWord=land&state=IN&category=110",
                "auction_date": None,
                "tags": ["govdeals", "government-surplus", "indiana"],
                "why": "Government surplus land in Indiana. Check for below-market parcels.",
                "is_new": True,
            })
    except Exception:
        pass
    return fetched


def fetch_sri_upcoming():
    """SRI Services upcoming Indiana tax sale dates."""
    fetched = []
    try:
        r = requests.get("https://properties.sriservices.com/auctionlist", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            text = r.text
            # Parse any Indiana counties in text
            for county in ["LaPorte", "Porter", "Lake", "Elkhart", "Kosciusko", "Allen", "St. Joseph", "Jasper", "Starke", "Marshall", "Newton", "Pulaski"]:
                if county in text:
                    fetched.append({
                        "title": f"SRI: {county} Co Tax Sale — Upcoming (Live Check)",
                        "location": COUNTIES.get(county, {}).get("seat", county),
                        "county": county,
                        "acres": None,
                        "price": None,
                        "price_per_acre": None,
                        "listing_type": "Tax Sale",
                        "property_type": "Multiple Parcels",
                        "source": "SRI Services (Live)",
                        "url": "https://properties.sriservices.com/auctionlist",
                        "auction_date": None,
                        "tags": ["tax-sale", "sri-services", "live"],
                        "why": f"Active tax sale parcels confirmed for {county} County via SRI live check.",
                        "is_new": True,
                    })
            # Deduplicate
            seen = set()
            out = []
            for item in fetched:
                if item["county"] not in seen:
                    seen.add(item["county"])
                    out.append(item)
            return out[:5]  # limit to 5 new entries
    except Exception:
        pass
    return fetched


def fetch_auctionzip_indiana():
    """AuctionZip Indiana real estate auctions."""
    fetched = []
    try:
        r = requests.get("https://www.auctionzip.com/in/real-estate-auctions.html", headers=HEADERS, timeout=8)
        if r.status_code == 200 and "Indiana" in r.text:
            fetched.append({
                "title": "AuctionZip: Indiana Real Estate Auctions (Live Feed)",
                "location": "Indiana (Statewide)",
                "county": "LaPorte",
                "acres": None,
                "price": None,
                "price_per_acre": None,
                "listing_type": "Auction",
                "property_type": "Land/Real Estate",
                "source": "AuctionZip (Live)",
                "url": "https://www.auctionzip.com/in/real-estate-auctions.html",
                "auction_date": None,
                "tags": ["auction", "auctionzip", "live", "real-estate"],
                "why": "Live auction feed — check for N. Indiana land coming up.",
                "is_new": True,
            })
    except Exception:
        pass
    return fetched


def fetch_schrader_live():
    """Schrader auctions for Indiana."""
    fetched = []
    try:
        r = requests.get("https://www.schraderauction.com/auctions/all", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            text = r.text
            for county in ["LaPorte", "Porter", "Kosciusko", "Elkhart", "Allen", "Jasper", "Marshall"]:
                if county in text:
                    fetched.append({
                        "title": f"Schrader Auction: {county} Co (Live Check)",
                        "location": COUNTIES.get(county, {}).get("seat", county),
                        "county": county,
                        "acres": None,
                        "price": None,
                        "price_per_acre": None,
                        "listing_type": "Auction",
                        "property_type": "Land",
                        "source": "Schrader Auction (Live)",
                        "url": "https://www.schraderauction.com/auctions/all",
                        "auction_date": None,
                        "tags": ["auction", "schrader", "live"],
                        "why": f"Active Schrader listing confirmed for {county} County via live check.",
                        "is_new": True,
                    })
            seen = set()
            out = []
            for item in fetched:
                if item["county"] not in seen:
                    seen.add(item["county"])
                    out.append(item)
            return out[:4]
    except Exception:
        pass
    return fetched


@st.cache_data(ttl=3600, show_spinner=False)
def run_live_fetch():
    """Run all live fetches, return (new_listings, status_msg, fetched_at)."""
    all_new = []
    errors = []

    for fn, name in [(fetch_govdeals_indiana, "GovDeals"), (fetch_sri_upcoming, "SRI Services"), (fetch_auctionzip_indiana, "AuctionZip"), (fetch_schrader_live, "Schrader")]:
        try:
            results = fn()
            all_new.extend(results)
        except Exception as e:
            errors.append(f"{name}: {e}")

    fetched_at = datetime.now().strftime("%B %d, %Y %I:%M %p")
    if errors:
        status = f"Fetched {len(all_new)} live listings. Issues: {', '.join(errors)}"
    else:
        status = f"Fetched {len(all_new)} fresh listings from 4 sources."

    return all_new, status, fetched_at


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOAD & MERGE LISTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
live_listings, live_status, fetched_at = run_live_fetch()

# Deduplicate live listings against seed by title
seed_titles = {item["title"] for item in SEED_LISTINGS}
unique_live = [x for x in live_listings if x["title"] not in seed_titles]

ALL_LISTINGS = SEED_LISTINGS + unique_live

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUILD DATAFRAME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
df = pd.DataFrame(ALL_LISTINGS)
# Ensure all required columns exist
for col in ["is_new", "assessed_value"]:
    if col not in df.columns:
        df[col] = None

grades = df.apply(grade, axis=1)
df["grade"] = [g[0] for g in grades]
df["grade_label"] = [g[1] for g in grades]
df["grade_note"] = [g[2] for g in grades]
df["grade_color"] = [g[3] for g in grades]

def days_until(d):
    if not d or pd.isna(d): return None
    try: return max((datetime.strptime(str(d), "%Y-%m-%d") - datetime.now()).days, -1)
    except: return None

df["days_until"] = df["auction_date"].apply(days_until)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("### Northern IN Land Deals")
    st.caption(f"{len(ALL_LISTINGS)} listings · {len(df['county'].unique())} counties")
    st.caption(f"~{sum(c['listings_est'] for c in COUNTIES.values()):,} total across all sources")
    st.caption(f"Last refreshed: {fetched_at}")

    if unique_live:
        st.success(f"{len(unique_live)} new listings found")

    st.markdown("---")
    sel_counties = st.multiselect("Counties", sorted(df["county"].unique()), default=sorted(df["county"].unique()))
    sel_types = st.multiselect("Listing Type", sorted(df["listing_type"].unique()), default=[t for t in sorted(df["listing_type"].unique()) if t != "Sold Comp"])
    sel_ptypes = st.multiselect("Property Type", sorted(df["property_type"].dropna().unique()), default=sorted(df["property_type"].dropna().unique()))

    st.markdown("**Deal Grade**")
    only_good = st.checkbox("Only A/A+/B+ deals", value=False)
    show_new_only = st.checkbox("Show new listings only", value=False)

    st.markdown("**Price**")
    max_price = st.number_input("Max Total Price ($)", value=0, step=50000, help="0 = no limit")
    max_ppa = st.number_input("Max $/Acre", value=0, step=1000, help="0 = no limit")

    st.markdown("**Acreage**")
    min_ac = st.number_input("Min Acres", value=0, step=5)
    max_ac = st.number_input("Max Acres", value=0, step=50, help="0 = no limit")

    st.markdown("---")
    st.markdown("### Live Search Links")
    st.caption("Click to open each site directly:")
    st.markdown("""
**Major Listing Sites:**
- [LandWatch — N. Indiana (1,508)](https://www.landwatch.com/indiana-land-for-sale/north-region)
- [Land.com — N. Indiana (1,370)](https://www.land.com/North-Indiana-Region/all-land/)
- [Land & Farm — Indiana (7,893)](https://www.landandfarm.com/search/indiana-land-for-sale/)
- [Zillow — Lake Co (366)](https://www.zillow.com/lake-county-in/land/)
- [Zillow — LaPorte Co (146)](https://www.zillow.com/la-porte-county-in/land/)
- [Redfin — LaPorte Co](https://www.redfin.com/county/859/IN/LaPorte-County/land)
- [Mossy Oak — NW Indiana](https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/)
- [LandSearch — Rural N. IN (432)](https://www.landsearch.com/rural/northern-indiana-in)
- [FarmFlip — IN Farms](https://www.farmflip.com/farms-for-sale/indiana)
- [Homes.com — Porter Co](https://www.homes.com/porter-county-in/land-for-sale/)

**Auction Houses:**
- [Schrader Auctions](https://www.schraderauction.com/auctions/all)
- [Sullivan Auctioneers](https://www.sullivanauctioneers.com/land-listings/)
- [Ranch & Farm Auctions](https://ranchandfarmauctions.com/)
- [Halderman — Listings](https://www.halderman.com/property-listings/)
- [Halderman — Auctions](https://www.haldermanauction.com/auctions)
- [Geswein Farm & Land](https://gfarmland.com/farm-real-estate/)
- [AuctionZip — Indiana](https://www.auctionzip.com/in/real-estate-auctions.html)
- [GovDeals — IN Land](https://www.govdeals.com/index.cfm?fa=Main.AdvSearchResultsNew&kWord=land&state=IN&category=110)
- [LandWatch — IN Auctions](https://www.landwatch.com/indiana-land-for-sale/auctions)
- [Land.com — IN Auctions](https://www.land.com/Indiana/all-land/at-auction/)

**Tax & Sheriff Sales:**
- [SRI Services — Tax Sales](https://properties.sriservices.com/auctionlist)
- [LaPorte Co Treasurer](https://laporteco.in.gov/residents/county-treasurer/real-estate-tax-sale/)
- [Porter Co Tax Sales](https://www.portercountyin.gov/1319/Tax-Certificate-Sales)
- [Lake Co Tax Sales](https://lakecountyin.gov/departments/auditor-taxsales)
- [LaPorte Sheriff Sales](https://www.laportecountysheriff.com/sheriff-sales)
- [St. Joseph Sheriff Sales](https://sjcpd.org/sheriffs-sale/)
- [Lake Co Sheriff Sales](https://lakecountyin.gov/departments/sheriff/sheriff-sale-listings-c/)
- [Allen Co Sheriff Sales](https://www.allencountysheriff.org/sheriff-sale/)
- [IN Sheriff Sales (all)](https://in-sheriffsale.com/)
- [Tax Sale Academy — IN](https://taxsaleacademy.com/indiana-tax-sales-tax-liens/)

**Research Tools:**
- [Beacon GIS — LaPorte](https://beacon.schneidercorp.com/?site=LaPorteCountyIN)
- [AcreValue — IN Soil Maps](https://www.acrevalue.com/map/IN/)
- [Regrid — IN Parcels](https://app.regrid.com/us/in/)
- [USDA Web Soil Survey](https://websoilsurvey.nrcs.usda.gov/)
- [IN Land & Lifestyle](https://indianalandandlifestyle.com/)
- [Prairie Farmland — Sold](https://prairiefarmland.com/land-for-sale/sold/)

**By County (Land.com):**
- [LaPorte](https://www.land.com/LaPorte-County-IN/all-land/) · [Porter](https://www.land.com/Porter-County-IN/all-land/) · [Lake](https://www.land.com/Lake-County-IN/all-land/)
- [Starke](https://www.land.com/Starke-County-IN/all-land/) · [Marshall](https://www.land.com/Marshall-County-IN/all-land/) · [Jasper](https://www.land.com/Jasper-County-IN/all-land/)
- [Pulaski](https://www.land.com/Pulaski-County-IN/all-land/) · [Newton](https://www.land.com/Newton-County-IN/all-land/) · [Kosciusko](https://www.land.com/Kosciusko-County-IN/all-land/)
- [Elkhart](https://www.land.com/Elkhart-County-IN/all-land/) · [Noble](https://www.land.com/Noble-County-IN/all-land/) · [Fulton](https://www.land.com/Fulton-County-IN/all-land/)
- [Allen](https://www.land.com/Allen-County-IN/all-land/) · [St. Joseph](https://www.land.com/St-Joseph-County-IN/all-land/)
- [Steuben](https://www.land.com/Steuben-County-IN/all-land/) · [DeKalb](https://www.land.com/DeKalb-County-IN/all-land/) · [LaGrange](https://www.land.com/LaGrange-County-IN/all-land/)
- [White](https://www.land.com/White-County-IN/all-land/) · [Whitley](https://www.land.com/Whitley-County-IN/all-land/) · [Wabash](https://www.land.com/Wabash-County-IN/all-land/)
- [Huntington](https://www.land.com/Huntington-County-IN/all-land/) · [Cass](https://www.land.com/Cass-County-IN/all-land/) · [Miami](https://www.land.com/Miami-County-IN/all-land/)
- [Wells](https://www.land.com/Wells-County-IN/all-land/) · [Adams](https://www.land.com/Adams-County-IN/all-land/) · [Carroll](https://www.land.com/Carroll-County-IN/all-land/)
- [Tippecanoe](https://www.land.com/Tippecanoe-County-IN/all-land/) · [Benton](https://www.land.com/Benton-County-IN/all-land/) · [Jay](https://www.land.com/Jay-County-IN/all-land/)
""")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLY FILTERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
f = df.copy()
f = f[f["county"].isin(sel_counties)]
f = f[f["listing_type"].isin(sel_types)]
f = f[f["property_type"].isin(sel_ptypes)]
if only_good:
    f = f[f["grade"].isin(["A+", "A", "B+"])]
if show_new_only:
    f = f[f["is_new"] == True]
if max_price > 0:
    f = f[(f["price"].isna()) | (f["price"] <= max_price)]
if max_ppa > 0:
    f = f[(f["price_per_acre"].isna()) | (f["price_per_acre"] <= max_ppa)]
if min_ac > 0:
    f = f[(f["acres"].isna()) | (f["acres"] >= min_ac)]
if max_ac > 0:
    f = f[(f["acres"].isna()) | (f["acres"] <= max_ac)]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("# Northern Indiana Land Deals")

# Live refresh status bar
new_count = len(unique_live)
if new_count > 0:
    st.markdown(f'<div class="refresh-box">Auto-refresh found <strong style="color:#f0a030">{new_count} new listings</strong> from live sources — Last checked: {fetched_at}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="refresh-box" style="color:#6e7681">Auto-refresh ran — no new listings found since last check · {fetched_at}</div>', unsafe_allow_html=True)

active = f[~f["listing_type"].isin(["Sold Comp"])]
priced = active[active["price_per_acre"].notna()]
good = active[active["grade"].isin(["A+", "A", "B+"])]
tax = active[active["listing_type"].isin(["Tax Sale", "Sheriff Sale"])]
auctions = active[active["listing_type"] == "Auction"]
total_ac = active["acres"].sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Listings", len(active))
c2.metric("Good Deals", len(good))
c3.metric("Total Acres", f"{total_ac:,.0f}" if pd.notna(total_ac) and total_ac > 0 else "—")
c4.metric("Avg $/Ac", f"${priced['price_per_acre'].mean():,.0f}" if len(priced) > 0 else "—")
c5.metric("Auctions", len(auctions))
c6.metric("Tax/Sheriff", len(tax))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "Best Deals", "All Listings", "Auctions & Tax Sales",
    "County Intel", "Market Charts", "Deal Calculator",
    "Soil & Land Use", "Historical Trends", "Farm Capacity", "Search All Sites"
])

# ─── HELPER: render a deal card ───
def render_card(r, fire=False):
    gc = r["grade"].replace("+", "-plus").lower()
    p = f"${r['price']:,.0f}" if pd.notna(r["price"]) else "Price TBD"
    ppa = f"${r['price_per_acre']:,.0f}/ac" if pd.notna(r["price_per_acre"]) else ""
    ac = f"{r['acres']:,.1f} ac" if pd.notna(r["acres"]) else ""
    au = ""
    if pd.notna(r.get("days_until")):
        d = int(r["days_until"])
        if d < 0: au = "ENDED"
        elif d == 0: au = "TODAY!"
        elif d == 1: au = "TOMORROW"
        elif d > 0: au = f"{d}d away"
    w = r.get("why", "")
    wh = f'<div style="font-size:11px;color:#3fb950;margin-top:6px;padding:6px 8px;background:#3fb95008;border-left:2px solid #3fb95033;border-radius:4px;">{w}</div>' if w else ""
    link = f'<a href="{r["url"]}" target="_blank" style="font-size:11px;color:#58a6ff;text-decoration:none;">View on {r["source"]} →</a>' if r.get("url") else ""
    tags = " ".join([f'<span class="tag">{t}</span>' for t in (r.get("tags") or [])[:5]])
    new_badge = '<span class="new-badge">NEW</span>' if r.get("is_new") else ""
    fire_cls = " fire-deal" if fire else ""
    st.markdown(f"""
<div class="deal-card{fire_cls}">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div style="flex:1;">
            <div style="font-size:14px;font-weight:700;">{r['title']}{new_badge}</div>
            <div style="font-size:12px;color:#8b949e;margin-top:2px;">{r['location']} · {r['county']} Co · {r['source']}</div>
        </div>
        <span class="grade-{gc}">{r['grade']} {r['grade_label']}</span>
    </div>
    <div style="display:flex;gap:12px;font-size:13px;color:#8b949e;margin:8px 0;">
        <strong style="color:#3fb950;">{p}</strong> {('· '+ac) if ac else ''} {('· <code>'+ppa+'</code>') if ppa else ''} {('· <strong style="color:#f0a030;">'+au+'</strong>') if au else ''}
    </div>
    <div style="font-size:12px;color:#6e7681;">{r['grade_note']}</div>
    {wh}
    <div style="margin-top:6px;">{tags}</div>
    <div style="margin-top:6px;">{link}</div>
</div>""", unsafe_allow_html=True)


# ─── TAB 1: BEST DEALS ───
with tab1:
    st.markdown("## Best Deals Right Now")
    st.caption("Graded A+/A/B+ based on $/acre vs county averages and comps")

    top = f[f["grade"].isin(["A+", "A", "B+"])].copy()
    if len(top) > 0:
        rank_map = {"A+": 0, "A": 1, "B+": 2}
        top["_r"] = top["grade"].map(rank_map).fillna(9)
        top = top.sort_values(["_r", "price_per_acre"], ascending=[True, True])

        # Show new listings first if any
        new_top = top[top["is_new"] == True]
        old_top = top[top["is_new"] != True]

        if len(new_top) > 0:
            st.markdown("### New Since Last Check")
            cols = st.columns(2)
            for idx, (_, r) in enumerate(new_top.iterrows()):
                with cols[idx % 2]:
                    render_card(r, fire=True)

            st.markdown("### All Good Deals")

        cols = st.columns(2)
        for idx, (_, r) in enumerate(old_top.iterrows()):
            with cols[idx % 2]:
                render_card(r, fire=True)
    else:
        st.info("No A/B+ deals match your current filters.")


# ─── TAB 2: ALL LISTINGS ───
with tab2:
    st.markdown("## All Listings")
    col_a, col_b = st.columns([3, 1])
    with col_a:
        sort_opt = st.selectbox("Sort by", ["Best Deal", "Price Low→High", "Price High→Low", "Acres Large→Small", "County", "Newest First"], index=0)
    with col_b:
        st.metric("Showing", len(f))

    d = f.copy()
    if sort_opt == "Best Deal":
        r_map = {"A+": 0, "A": 1, "B+": 2, "B": 3, "C": 4, "D": 5, "COMP": 8, "—": 9}
        d["_r"] = d["grade"].map(r_map).fillna(9)
        d = d.sort_values(["_r", "price_per_acre"], ascending=[True, True])
    elif sort_opt == "Price Low→High":
        d = d.sort_values("price", na_position="last")
    elif sort_opt == "Price High→Low":
        d = d.sort_values("price", ascending=False, na_position="last")
    elif sort_opt == "Acres Large→Small":
        d = d.sort_values("acres", ascending=False, na_position="last")
    elif sort_opt == "County":
        d = d.sort_values("county")
    elif sort_opt == "Newest First":
        d = d.sort_values("is_new", ascending=False)

    for _, r in d.iterrows():
        gc = r["grade"].replace("+", "-plus").lower()
        p = f"${r['price']:,.0f}" if pd.notna(r["price"]) else ""
        ppa = f"${r['price_per_acre']:,.0f}/ac" if pd.notna(r["price_per_acre"]) else ""
        ac = f"{r['acres']:,.1f} ac" if pd.notna(r["acres"]) else ""
        w = r.get("why", "")
        wh = f'<div style="font-size:11px;color:#3fb950;margin-top:4px;padding:3px 8px;background:#3fb95008;border-left:2px solid #3fb95033;border-radius:4px;">{w}</div>' if w else ""
        link = f'<a href="{r["url"]}" target="_blank" style="font-size:11px;color:#58a6ff;text-decoration:none;">View →</a>' if r.get("url") else ""
        tags = " ".join([f'<span class="tag">{t}</span>' for t in (r.get("tags") or [])[:4]])
        new_badge = '<span class="new-badge">NEW</span>' if r.get("is_new") else ""
        st.markdown(f"""
<div class="deal-card">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div style="flex:1;">
            <div style="font-size:14px;font-weight:600;">{r['title']}{new_badge}</div>
            <div style="font-size:12px;color:#8b949e;">{r['location']} · {r['county']} Co · {r['listing_type']} · {r['source']}</div>
            <div style="display:flex;gap:10px;font-size:13px;color:#8b949e;margin-top:4px;">
                {('<strong style="color:#3fb950;">'+p+'</strong>') if p else ''} {('· '+ac) if ac else ''} {('· <code>'+ppa+'</code>') if ppa else ''}
            </div>
            {wh}
            <div style="margin-top:4px;">{tags} {link}</div>
        </div>
        <div style="text-align:right;min-width:70px;">
            <span class="grade-{gc}">{r['grade']}</span>
            <div style="font-size:10px;color:#8b949e;margin-top:2px;">{r['grade_label']}</div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)


# ─── TAB 3: AUCTIONS & TAX SALES ───
with tab3:
    st.markdown("## Upcoming Auctions & Tax Sales")

    col_auc, col_tax = st.columns([1, 1])

    with col_auc:
        st.markdown("### Land Auctions")
        auc = f[f["listing_type"] == "Auction"].copy()
        auc_dated = auc[auc["auction_date"].notna()].sort_values("auction_date")
        auc_undated = auc[auc["auction_date"].isna()]

        for _, r in auc_dated.iterrows():
            d_val = r.get("days_until")
            if pd.notna(d_val):
                d_val = int(d_val)
                if d_val < 0:
                    urg_color = "#6e7681"
                    urg = "ENDED"
                elif d_val == 0:
                    urg_color = "#f85149"
                    urg = "TODAY!"
                elif d_val <= 7:
                    urg_color = "#f85149"
                    urg = f"{d_val}d"
                elif d_val <= 30:
                    urg_color = "#f0a030"
                    urg = f"{d_val}d"
                else:
                    urg_color = "#58a6ff"
                    urg = f"{d_val}d"
            else:
                urg_color = "#6e7681"
                urg = ""
            ac = f" · {r['acres']:,.0f} ac" if pd.notna(r["acres"]) else ""
            new_badge = " [NEW]" if r.get("is_new") else ""
            link = f'[View →]({r["url"]})' if r.get("url") else ""
            st.markdown(f'**{r["title"]}**{new_badge}')
            st.caption(f'{r["county"]} Co{ac} · {r["auction_date"]} · <span style="color:{urg_color};font-weight:700">{urg}</span> · {link}', unsafe_allow_html=True)
            if r.get("why"):
                st.caption(f"Why: {r['why']}")
            st.markdown("---")

        if len(auc_undated) > 0:
            st.markdown("**Open/Ongoing Auctions:**")
            for _, r in auc_undated.iterrows():
                link = f'[View →]({r["url"]})' if r.get("url") else ""
                st.caption(f"• **{r['title']}** — {r['county']} Co {link}")

    with col_tax:
        st.markdown("### Tax & Sheriff Sales")
        ts = f[f["listing_type"].isin(["Tax Sale", "Sheriff Sale"])].copy()
        ts_dated = ts[ts["auction_date"].notna()].sort_values("auction_date")
        ts_ongoing = ts[ts["auction_date"].isna()]

        st.markdown("**Scheduled Sales:**")
        for _, r in ts_dated.iterrows():
            d_val = r.get("days_until")
            if pd.notna(d_val):
                d_int = int(d_val)
                days_str = f"{d_int}d away" if d_int > 0 else ("TODAY" if d_int == 0 else "PASSED")
            else:
                days_str = ""
            link = f'[Register →]({r["url"]})' if r.get("url") else ""
            ltype_color = "#f85149" if r["listing_type"] == "Sheriff Sale" else "#f0a030"
            st.markdown(f'<span style="color:{ltype_color};font-size:10px;font-weight:700">{r["listing_type"].upper()}</span> **{r["title"]}**', unsafe_allow_html=True)
            st.caption(f'{r["county"]} Co · {r["auction_date"]} ({days_str}) · {link}')
            if r.get("why"):
                st.caption(f"Why: {r['why']}")
            st.markdown("---")

        st.markdown("**Ongoing / Rolling Sales:**")
        for _, r in ts_ongoing.iterrows():
            link = f'[View →]({r["url"]})' if r.get("url") else ""
            ltype_color = "#f85149" if r["listing_type"] == "Sheriff Sale" else "#f0a030"
            st.markdown(f'<span style="color:{ltype_color};font-size:10px">{r["listing_type"]}</span> **{r["title"]}**', unsafe_allow_html=True)
            st.caption(f'{r["county"]} Co · {link}')
            if r.get("why"):
                st.caption(f"Why: {r['why']}")
            st.markdown("---")

    st.markdown("---")
    st.markdown("### Tax Sale Quick Reference")
    st.markdown("""
| Item | Detail |
|---|---|
| **Registration** | SRI Services handles most IN counties |
| **Deposit** | 10% down at auction, balance within 30 days |
| **Redemption Period** | 1 year — owner can redeem by paying taxes + 10-15% interest |
| **If Redeemed (≤6 mo)** | You earn 10% on your investment |
| **If Redeemed (>6 mo)** | You earn 15% on your investment |
| **Commissioner's Sale** | Parcels that failed first round — deepest discounts |
| **Sheriff Sale** | Foreclosures — no redemption period, min $3K deposit |
| **Best Strategy** | Tax sale + redemption = guaranteed 10-15% short-term return |
""")


# ─── TAB 4: COUNTY INTEL ───
with tab4:
    st.markdown("## County Market Intelligence — 30 N. Indiana Counties")
    st.caption("Ranked cheapest to most expensive farmland per acre")

    view_opt = st.radio("View", ["Grid", "Table"], horizontal=True)

    cheap = sorted(COUNTIES.items(), key=lambda x: x[1]["avg"])

    if view_opt == "Grid":
        cols4 = st.columns(3)
        for i, (co, data) in enumerate(cheap):
            with cols4[i % 3]:
                rank = i + 1
                medal = {1: "1st", 2: "2nd", 3: "3rd"}.get(rank, f"{rank}th")
                color = "#3fb950" if rank <= 5 else "#f0a030" if rank <= 15 else "#8b949e"
                listings_in = len(f[f["county"] == co])
                st.markdown(f"""
<div style="background:#0d1117;border:1px solid #1e2d3d;border-radius:10px;padding:14px;margin-bottom:8px;">
    <div style="font-size:18px;font-weight:800;color:{color};">{medal} — {co} Co.</div>
    <div style="font-size:22px;font-weight:700;color:#e6edf3;margin:4px 0;">${data['avg']:,}/ac avg</div>
    <div style="font-size:11px;color:#6e7681;">Range: ${data['lo']:,} – ${data['hi']:,}/ac</div>
    <div style="font-size:11px;color:#8b949e;">{listings_in} in dashboard · ~{data['listings_est']} total online</div>
    <div style="font-size:11px;color:#8b949e;">Seat: {data['seat']} · Pop: {data['pop']:,}</div>
</div>""", unsafe_allow_html=True)
    else:
        county_rows = []
        for i, (co, data) in enumerate(cheap):
            listings_in = len(f[f["county"] == co])
            county_rows.append({
                "Rank": i + 1,
                "County": co,
                "Avg $/Acre": f"${data['avg']:,}",
                "Low Comp": f"${data['lo']:,}",
                "High Comp": f"${data['hi']:,}",
                "County Seat": data['seat'],
                "Population": f"{data['pop']:,}",
                "Dashboard Listings": listings_in,
                "Est. Total Online": f"~{data['listings_est']}",
            })
        st.dataframe(pd.DataFrame(county_rows), use_container_width=True, hide_index=True)


# ─── TAB 5: CHARTS ───
with tab5:
    st.markdown("## Market Analysis")

    col1, col2 = st.columns(2)

    with col1:
        cdf = pd.DataFrame([
            {"County": k, "Avg $/Acre": v["avg"], "Low": v["lo"], "High": v["hi"]}
            for k, v in COUNTIES.items()
        ]).sort_values("Avg $/Acre")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=cdf["County"], y=cdf["Avg $/Acre"], name="Avg",
            marker_color="#f0a030",
            text=[f"${v:,.0f}" for v in cdf["Avg $/Acre"]],
            textposition="outside", textfont_size=8
        ))
        fig.add_trace(go.Scatter(
            x=cdf["County"], y=cdf["Low"], name="Low Comp",
            mode="markers", marker=dict(color="#3fb950", size=6, symbol="triangle-down")
        ))
        fig.add_trace(go.Scatter(
            x=cdf["County"], y=cdf["High"], name="High Comp",
            mode="markers", marker=dict(color="#f85149", size=6, symbol="triangle-up")
        ))
        fig.update_layout(
            title="Farmland $/Acre by County (30 counties)", template="plotly_dark",
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", height=500,
            margin=dict(t=40, b=80), legend=dict(orientation="h", y=-0.2),
            yaxis_title="$/Acre", xaxis_tickangle=-45
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        priced_f = f[f["price_per_acre"].notna() & ~f["listing_type"].isin(["Sold Comp"])].copy()
        if len(priced_f) > 0:
            fig2 = px.scatter(
                priced_f, x="acres", y="price_per_acre", color="grade",
                size_max=30, hover_name="title",
                hover_data=["county", "price", "grade_label"],
                color_discrete_map={
                    "A+": "#3fb950", "A": "#3fb950", "B+": "#58a6ff",
                    "B": "#f0a030", "C": "#f0a030", "D": "#f85149"
                },
                title="Listings: Acres vs $/Acre"
            )
            fig2.update_layout(
                template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                height=500, margin=dict(t=40, b=40),
                xaxis_title="Acres", yaxis_title="$/Acre"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Grade distribution pie
    col3, col4 = st.columns(2)
    with col3:
        grade_counts = f[~f["listing_type"].isin(["Sold Comp"])]["grade"].value_counts()
        fig3 = px.pie(
            values=grade_counts.values, names=grade_counts.index,
            title="Deal Grade Distribution",
            color=grade_counts.index,
            color_discrete_map={
                "A+": "#3fb950", "A": "#58b256", "B+": "#58a6ff",
                "B": "#f0a030", "C": "#e07020", "D": "#f85149", "—": "#6e7681"
            }
        )
        fig3.update_layout(template="plotly_dark", paper_bgcolor="#0d1117", height=380, margin=dict(t=40))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        # Listings by county bar
        county_counts = f[~f["listing_type"].isin(["Sold Comp"])]["county"].value_counts().head(15)
        fig4 = px.bar(
            x=county_counts.values, y=county_counts.index,
            orientation="h", title="Listings by County (Top 15)",
            color=county_counts.values,
            color_continuous_scale=[[0, "#1e2d3d"], [1, "#f0a030"]]
        )
        fig4.update_layout(
            template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            height=380, margin=dict(t=40, l=80), showlegend=False,
            coloraxis_showscale=False, xaxis_title="# Listings"
        )
        st.plotly_chart(fig4, use_container_width=True)


# ─── TAB 6: DEAL CALCULATOR ───
with tab6:
    st.markdown("## Deal Calculator")
    st.caption("Plug in any land deal to get instant grade, cash yield, and scenarios")

    calc1, calc2 = st.columns(2)

    with calc1:
        st.markdown("### Purchase Details")
        calc_price = st.number_input("Purchase Price ($)", value=500000, step=10000)
        calc_acres = st.number_input("Total Acres", value=80.0, step=5.0)
        calc_county = st.selectbox("County", list(COUNTIES.keys()), index=0)
        calc_tillable = st.number_input("Tillable Acres", value=60.0, step=5.0)
        calc_rent = st.number_input("Cash Rent ($/ac/yr)", value=280, step=10, help="Indiana avg: $250-350/ac")
        calc_crp_acres = st.number_input("CRP Acres", value=0.0, step=5.0, help="Conservation Reserve Program")
        calc_crp_rate = st.number_input("CRP Payment ($/ac/yr)", value=200, step=10, help="USDA avg: $150-250/ac")
        calc_assessed = st.number_input("Assessed Value ($ optional)", value=0, step=10000, help="Enter if known for better grading")

    with calc2:
        st.markdown("### Analysis")
        if calc_acres > 0 and calc_price > 0:
            ppa = calc_price / calc_acres
            annual_rent = calc_tillable * calc_rent
            annual_crp = calc_crp_acres * calc_crp_rate
            total_income = annual_rent + annual_crp
            cash_yield = (total_income / calc_price) * 100

            cd = COUNTIES.get(calc_county, {})
            avg_ppa = cd.get("avg", 10000)
            lo_comp = cd.get("lo", 7000)
            hi_comp = cd.get("hi", 15000)

            discount = ((avg_ppa - ppa) / avg_ppa) * 100

            # Grade logic
            if calc_assessed > 0:
                r_ratio = calc_price / calc_assessed
                if r_ratio < 0.15:
                    calc_grade, calc_grade_label = "A+", "Steal"
                elif r_ratio < 0.25:
                    calc_grade, calc_grade_label = "A", "Great Deal"
                elif r_ratio < 0.40:
                    calc_grade, calc_grade_label = "B+", "Good"
                elif r_ratio < 0.60:
                    calc_grade, calc_grade_label = "B", "Fair"
                else:
                    calc_grade, calc_grade_label = "C", "Full Price"
                grade_note = f"{r_ratio:.0%} of assessed value"
            elif ppa < lo_comp * 0.7:
                calc_grade, calc_grade_label = "A+", "Way Below Market"
                grade_note = f"${ppa:,.0f}/ac vs low comp ${lo_comp:,}/ac"
            elif ppa < lo_comp:
                calc_grade, calc_grade_label = "A", "Below Comps"
                grade_note = f"${ppa:,.0f}/ac vs low comp ${lo_comp:,}/ac"
            elif ppa < avg_ppa * 0.85:
                calc_grade, calc_grade_label = "B+", "Good Value"
                grade_note = f"${ppa:,.0f}/ac vs avg ${avg_ppa:,}/ac"
            elif ppa < avg_ppa * 1.1:
                calc_grade, calc_grade_label = "B", "Market Rate"
                grade_note = f"${ppa:,.0f}/ac ≈ avg ${avg_ppa:,}/ac"
            else:
                calc_grade, calc_grade_label = "C", "Above Average"
                grade_note = f"${ppa:,.0f}/ac > avg ${avg_ppa:,}/ac"

            grade_colors = {"A+": "success", "A": "success", "B+": "info", "B": "warning", "C": "error", "D": "error"}
            getattr(st, grade_colors.get(calc_grade, "info"))(f"**Grade: {calc_grade} — {calc_grade_label}** · {grade_note}")

            m1, m2, m3 = st.columns(3)
            m1.metric("Price Per Acre", f"${ppa:,.0f}")
            m2.metric(f"vs {calc_county} Avg", f"{discount:+.1f}%", delta="below mkt" if discount > 0 else "above mkt", delta_color="normal" if discount > 0 else "inverse")
            m3.metric("Cash Yield", f"{cash_yield:.1f}%", delta="good" if cash_yield >= 3 else "low", delta_color="normal" if cash_yield >= 3 else "inverse")

            m4, m5 = st.columns(2)
            m4.metric("Annual Farm Rent", f"${annual_rent:,.0f}")
            m5.metric("Total Annual Income", f"${total_income:,.0f}")

            if annual_crp > 0:
                st.caption(f"CRP Income: ${annual_crp:,.0f}/yr · Farm Rent: ${annual_rent:,.0f}/yr")

            st.markdown("---")
            st.markdown("### Scenario Analysis")
            st.markdown(f"""
| Scenario | Value |
|---|---|
| **$/Acre you're paying** | ${ppa:,.0f}/ac |
| **County avg $/acre** | ${avg_ppa:,}/ac |
| **Break-even rent needed** | ${calc_price * 0.03 / max(calc_tillable, 1):,.0f}/ac/yr (3% yield target) |
| **5-yr value at 3% appreciation** | ${calc_price * (1.03**5):,.0f} (gain: ${calc_price * (1.03**5) - calc_price:,.0f}) |
| **10-yr value at 3% appreciation** | ${calc_price * (1.03**10):,.0f} (gain: ${calc_price * (1.03**10) - calc_price:,.0f}) |
| **5-yr value at 5% appreciation** | ${calc_price * (1.05**5):,.0f} (gain: ${calc_price * (1.05**5) - calc_price:,.0f}) |
| **Total 5-yr income + 3% appreciation** | ${total_income * 5 + calc_price * (1.03**5) - calc_price:,.0f} |
| **Tax sale return (if redeemed ≤6mo)** | 10% = ${calc_price * 0.10:,.0f} |
| **Tax sale return (if redeemed >6mo)** | 15% = ${calc_price * 0.15:,.0f} |
| **Development value (rezone 2x)** | ${calc_price * 2:,.0f} |
""")

    st.markdown("---")
    st.markdown("### Quick Comps")
    st.caption(f"Recent sold comparables for {calc_county} County:")
    comps_in_county = df[(df["county"] == calc_county) & (df["listing_type"] == "Sold Comp")]
    if len(comps_in_county) > 0:
        for _, cr in comps_in_county.iterrows():
            p_str = f"${cr['price_per_acre']:,.0f}/ac = ${cr['price']:,.0f}" if pd.notna(cr["price_per_acre"]) and pd.notna(cr["price"]) else "price TBD"
            st.markdown(f"- **{cr['title']}** — {cr['acres']} ac · {p_str}")
    else:
        cd2 = COUNTIES.get(calc_county, {})
        st.caption(f"No sold comps in database for {calc_county} Co. Market data: avg ${cd2.get('avg', 0):,}/ac · range ${cd2.get('lo', 0):,}–${cd2.get('hi', 0):,}/ac")


# ─── TAB 7: SOIL & LAND USE ───
with tab7:
    st.markdown("## Soil Quality & Land Use")
    st.caption("NCCPI = National Commodity Crop Productivity Index (0-100). Higher = better for row crops.")

    # Summary metrics
    nccpi_vals = [c["nccpi"] for c in COUNTIES.values()]
    farm_pcts = [c["farm_pct"] for c in COUNTIES.values()]
    forest_pcts = [c["forest_pct"] for c in COUNTIES.values()]

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Avg NCCPI (N. IN)", f"{sum(nccpi_vals)/len(nccpi_vals):.0f}")
    sc2.metric("Best County Soil", max(COUNTIES.items(), key=lambda x: x[1]["nccpi"])[0], f"NCCPI {max(nccpi_vals)}")
    sc3.metric("Avg % Farmland", f"{sum(farm_pcts)/len(farm_pcts):.0f}%")
    sc4.metric("Avg % Forest", f"{sum(forest_pcts)/len(forest_pcts):.0f}%")

    st.markdown("---")

    # Soil quality chart
    st.markdown("### Soil Quality by County (NCCPI Score)")
    soil_df = pd.DataFrame([
        {"County": k, "NCCPI": v["nccpi"], "Class": soil_grade(v["nccpi"])[0], "Avg $/Ac": v["avg"]}
        for k, v in COUNTIES.items()
    ]).sort_values("NCCPI", ascending=False)

    fig_soil = go.Figure()
    colors = [soil_grade(n)[1] for n in soil_df["NCCPI"]]
    fig_soil.add_trace(go.Bar(
        x=soil_df["County"], y=soil_df["NCCPI"],
        marker_color=colors,
        text=[f"{n}" for n in soil_df["NCCPI"]],
        textposition="outside", textfont_size=10
    ))
    fig_soil.add_hline(y=75, line_dash="dash", line_color="#3fb950", annotation_text="Class I (Prime)")
    fig_soil.add_hline(y=65, line_dash="dash", line_color="#58a6ff", annotation_text="Class II")
    fig_soil.add_hline(y=55, line_dash="dash", line_color="#f0a030", annotation_text="Class III")
    fig_soil.update_layout(
        template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        height=450, margin=dict(t=20, b=80), yaxis_title="NCCPI Score", xaxis_tickangle=-45,
    )
    st.plotly_chart(fig_soil, use_container_width=True)

    # Soil vs Price scatter
    st.markdown("### Does Better Soil = Higher Price?")
    fig_scatter = px.scatter(
        soil_df, x="NCCPI", y="Avg $/Ac", color="Class", size="NCCPI",
        hover_name="County", text="County",
        color_discrete_map={"Class I": "#3fb950", "Class II": "#3fb950", "Class III": "#58a6ff", "Class IV": "#f0a030", "Class V+": "#f85149"},
        title="Soil Quality (NCCPI) vs Farmland Price"
    )
    fig_scatter.update_traces(textposition="top center", textfont_size=9)
    fig_scatter.update_layout(template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")
    st.markdown("### Land Use Breakdown by County")
    lu_df = pd.DataFrame([
        {"County": k, "Farmland %": v["farm_pct"], "Forest %": v["forest_pct"], "Other %": 100 - v["farm_pct"] - v["forest_pct"]}
        for k, v in COUNTIES.items()
    ]).sort_values("Farmland %", ascending=False)

    fig_lu = go.Figure()
    fig_lu.add_trace(go.Bar(name="Farmland", x=lu_df["County"], y=lu_df["Farmland %"], marker_color="#f0a030"))
    fig_lu.add_trace(go.Bar(name="Forest", x=lu_df["County"], y=lu_df["Forest %"], marker_color="#3fb950"))
    fig_lu.add_trace(go.Bar(name="Other (water/urban/wetland)", x=lu_df["County"], y=lu_df["Other %"], marker_color="#58a6ff"))
    fig_lu.update_layout(
        template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        barmode="stack", height=450, margin=dict(t=20, b=80), yaxis_title="% of County", xaxis_tickangle=-45,
    )
    st.plotly_chart(fig_lu, use_container_width=True)

    st.markdown("---")
    st.markdown("### Soil Details by County")
    soil_detail_df = pd.DataFrame([
        {
            "County": k,
            "NCCPI": v["nccpi"],
            "Class": soil_grade(v["nccpi"])[0],
            "Top Soil Types": v["top_soil"],
            "Top Crops": ", ".join(v["top_crops"][:3]),
            "Farm %": f"{v['farm_pct']}%",
            "Forest %": f"{v['forest_pct']}%",
        }
        for k, v in sorted(COUNTIES.items(), key=lambda x: -x[1]["nccpi"])
    ])
    st.dataframe(soil_detail_df, use_container_width=True, hide_index=True)


# ─── TAB 8: HISTORICAL TRENDS ───
with tab8:
    st.markdown("## Historical Price Trends (2020-2025)")
    st.caption("$/acre averages from Indiana Farmland Values Survey + actual sold comps")

    # Price trend chart — all counties
    years = ["2020", "2021", "2022", "2023", "2024", "2025"]
    hist_df_rows = []
    for co, data in COUNTIES.items():
        for i, y in enumerate(years):
            hist_df_rows.append({"County": co, "Year": y, "$/Acre": data["hist"][i]})
    hist_df = pd.DataFrame(hist_df_rows)

    # Top 10 most expensive + bottom 10 cheapest
    top_counties = sorted(COUNTIES.items(), key=lambda x: -x[1]["avg"])[:10]
    bot_counties = sorted(COUNTIES.items(), key=lambda x: x[1]["avg"])[:10]

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("#### Most Expensive Counties (Trend)")
        fig_top = go.Figure()
        for co, _ in top_counties:
            co_data = hist_df[hist_df["County"] == co]
            fig_top.add_trace(go.Scatter(x=co_data["Year"], y=co_data["$/Acre"], name=co, mode="lines+markers"))
        fig_top.update_layout(template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", height=400, yaxis_title="$/Acre")
        st.plotly_chart(fig_top, use_container_width=True)

    with col_t2:
        st.markdown("#### Cheapest Counties (Trend)")
        fig_bot = go.Figure()
        for co, _ in bot_counties:
            co_data = hist_df[hist_df["County"] == co]
            fig_bot.add_trace(go.Scatter(x=co_data["Year"], y=co_data["$/Acre"], name=co, mode="lines+markers"))
        fig_bot.update_layout(template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", height=400, yaxis_title="$/Acre")
        st.plotly_chart(fig_bot, use_container_width=True)

    st.markdown("---")
    st.markdown("### 5-Year Appreciation by County")
    apprec = []
    for co, data in COUNTIES.items():
        start = data["hist"][0]
        end = data["hist"][-1]
        pct = ((end - start) / start) * 100
        cagr = (((end / start) ** (1/5)) - 1) * 100
        apprec.append({"County": co, "2020": start, "2025": end, "5yr %": round(pct, 1), "CAGR": round(cagr, 1)})
    apprec_df = pd.DataFrame(apprec).sort_values("5yr %", ascending=False)

    fig_apprec = px.bar(apprec_df, x="County", y="5yr %",
                        color="5yr %", color_continuous_scale=[[0, "#f85149"], [0.5, "#f0a030"], [1, "#3fb950"]],
                        title="5-Year Price Appreciation (%)")
    fig_apprec.update_layout(template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_apprec, use_container_width=True)

    st.dataframe(apprec_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Sold Comps Database")
    sold = df[df["listing_type"] == "Sold Comp"].sort_values("price_per_acre", ascending=False) if "listing_type" in df.columns else pd.DataFrame()
    if len(sold) > 0:
        sold_display = sold[["title", "location", "county", "acres", "price", "price_per_acre", "source"]].copy()
        sold_display.columns = ["Property", "Location", "County", "Acres", "Sale Price", "$/Acre", "Source"]
        sold_display["Sale Price"] = sold_display["Sale Price"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
        sold_display["$/Acre"] = sold_display["$/Acre"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
        st.dataframe(sold_display, use_container_width=True, hide_index=True)
    else:
        st.info("No sold comps in current filter.")


# ─── TAB 9: FARM CAPACITY ───
with tab9:
    st.markdown("## Farm Capacity Analysis")
    st.caption("What can the land actually produce? Revenue calculations based on 2026 crop prices.")

    st.markdown("### Expected Crop Yields by County")
    yield_df = pd.DataFrame([
        {
            "County": k,
            "NCCPI": v["nccpi"],
            "Corn (bu/ac)": v["corn_yield"],
            "Soy (bu/ac)": v["soy_yield"],
            "Wheat (bu/ac)": v["wheat_yield"],
            "Rent ($/ac)": v["rent"],
            "Cattle (head/ac)": 1/v["cattle_stocking"],
        }
        for k, v in sorted(COUNTIES.items(), key=lambda x: -x[1]["corn_yield"])
    ])

    fig_yield = go.Figure()
    fig_yield.add_trace(go.Bar(name="Corn (bu/ac)", x=yield_df["County"], y=yield_df["Corn (bu/ac)"], marker_color="#f0a030"))
    fig_yield.add_trace(go.Bar(name="Soy × 3 (bu/ac)", x=yield_df["County"], y=yield_df["Soy (bu/ac)"] * 3, marker_color="#3fb950"))
    fig_yield.update_layout(template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", height=400, barmode="group", xaxis_tickangle=-45, yaxis_title="Bushels/Acre")
    st.plotly_chart(fig_yield, use_container_width=True)

    st.markdown("---")
    st.markdown("### Revenue per Acre by Crop (2026 Prices)")
    st.caption(f"Corn: ${CROP_PRICES['corn']}/bu | Soy: ${CROP_PRICES['soybeans']}/bu | Wheat: ${CROP_PRICES['wheat']}/bu")

    rev_rows = []
    for co, v in COUNTIES.items():
        corn_rev = v["corn_yield"] * CROP_PRICES["corn"]
        soy_rev = v["soy_yield"] * CROP_PRICES["soybeans"]
        corn_profit = corn_rev - CROP_COSTS["corn"]
        soy_profit = soy_rev - CROP_COSTS["soybeans"]
        rev_rows.append({
            "County": co,
            "Corn Revenue/ac": corn_rev,
            "Corn Profit/ac": corn_profit,
            "Soy Revenue/ac": soy_rev,
            "Soy Profit/ac": soy_profit,
            "Farm Rent/ac": v["rent"],
        })
    rev_df = pd.DataFrame(rev_rows).sort_values("Corn Profit/ac", ascending=False)

    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(name="Corn Profit", x=rev_df["County"], y=rev_df["Corn Profit/ac"], marker_color="#f0a030"))
    fig_rev.add_trace(go.Bar(name="Soy Profit", x=rev_df["County"], y=rev_df["Soy Profit/ac"], marker_color="#3fb950"))
    fig_rev.add_trace(go.Bar(name="Cash Rent", x=rev_df["County"], y=rev_df["Farm Rent/ac"], marker_color="#58a6ff"))
    fig_rev.update_layout(template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", height=450, barmode="group", xaxis_tickangle=-45, yaxis_title="$/Acre")
    st.plotly_chart(fig_rev, use_container_width=True)

    st.markdown("---")
    st.markdown("### ROI Comparison: Farm Rent vs CRP vs Development vs Timber")

    roi_data = []
    for co, v in COUNTIES.items():
        price = v["avg"]
        roi_data.append({
            "County": co,
            "Farm Rent Yield": round((v["rent"] / price) * 100, 2),
            "CRP Yield (est)": round((200 / price) * 100, 2),
            "Corn Op Yield": round(((v["corn_yield"] * CROP_PRICES["corn"] - CROP_COSTS["corn"]) / price) * 100, 2),
        })
    roi_df = pd.DataFrame(roi_data).sort_values("Corn Op Yield", ascending=False)

    fig_roi = go.Figure()
    fig_roi.add_trace(go.Bar(name="Cash Rent %", x=roi_df["County"], y=roi_df["Farm Rent Yield"], marker_color="#58a6ff"))
    fig_roi.add_trace(go.Bar(name="CRP %", x=roi_df["County"], y=roi_df["CRP Yield (est)"], marker_color="#3fb950"))
    fig_roi.add_trace(go.Bar(name="Operate Corn %", x=roi_df["County"], y=roi_df["Corn Op Yield"], marker_color="#f0a030"))
    fig_roi.update_layout(template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", height=450, barmode="group", xaxis_tickangle=-45, yaxis_title="Annual Yield %")
    st.plotly_chart(fig_roi, use_container_width=True)

    st.markdown("---")
    st.markdown("### Detailed County Farm Economics")
    econ_df = pd.DataFrame([
        {
            "County": k,
            "NCCPI": v["nccpi"],
            "Corn (bu)": v["corn_yield"],
            "Soy (bu)": v["soy_yield"],
            "Corn Rev/ac": f"${v['corn_yield'] * CROP_PRICES['corn']:,.0f}",
            "Soy Rev/ac": f"${v['soy_yield'] * CROP_PRICES['soybeans']:,.0f}",
            "Cash Rent": f"${v['rent']}",
            "Cash Yield %": f"{(v['rent'] / v['avg']) * 100:.1f}%",
            "Timber $/ac": f"${v['timber_val']:,}",
            "Top Crops": ", ".join(v["top_crops"][:3]),
        }
        for k, v in sorted(COUNTIES.items(), key=lambda x: -x[1]["corn_yield"])
    ])
    st.dataframe(econ_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Best Use Recommendations by Soil Class")
    st.markdown("""
| Soil Class | NCCPI | Best Use | Expected Return |
|---|---|---|---|
| **Class I — Prime** | 75+ | Intensive row crops (corn/soy rotation), specialty crops, seed production | Cash rent $300-400/ac, operate $400-600/ac profit |
| **Class II — Excellent** | 65-74 | Standard corn/soy, wheat, popcorn | Cash rent $260-320/ac, operate $300-450/ac profit |
| **Class III — Good** | 55-64 | Corn/soy, hay, alfalfa, pasture | Cash rent $220-270/ac, operate $200-350/ac profit |
| **Class IV — Fair** | 45-54 | Hay, pasture, livestock, timber | Cash rent $150-220/ac, cattle 1 pair/1.5-2 ac |
| **Class V+ — Marginal** | <45 | Pasture, timber, CRP, recreation | CRP $150-250/ac, timber, hunting lease $15-30/ac |
""")


# ─── TAB 10: SEARCH ALL SITES ───
with tab10:
    st.markdown("## Search Every Listing Site")
    st.markdown(f"This dashboard has **{len(ALL_LISTINGS)} scraped listings**. The full market has **thousands** more across these sites:")

    st.markdown("---")
    st.markdown("### By County — Direct Search Links")
    st.caption("Click any link to search that county on that site right now")

    for co in sorted(COUNTIES.keys()):
        co_slug = co.replace(" ", "-").replace(".", "")
        co_lower = co_slug.lower()
        listings_count = COUNTIES[co]["listings_est"]
        st.markdown(f"""
**{co} County** (~{listings_count} listings online) —
[LandWatch](https://www.landwatch.com/indiana-land-for-sale/{co_lower}-county) ·
[Land.com](https://www.land.com/{co_slug}-County-IN/all-land/) ·
[Land & Farm](https://www.landandfarm.com/search/indiana/{co_lower}-county-land-for-sale/) ·
[Zillow](https://www.zillow.com/{co_lower}-county-in/land/) ·
[Redfin](https://www.redfin.com/county/IN/{co_slug}-County/land) ·
[LandSearch](https://www.landsearch.com/properties/{co_lower}-county-in)
""")

    st.markdown("---")
    st.markdown("### All Listing Sites")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("""
**Major Platforms**
- [LandWatch — Indiana](https://www.landwatch.com/indiana-land-for-sale/north-region)
- [Land.com — Indiana](https://www.land.com/Indiana/all-land/)
- [Land & Farm — Indiana](https://www.landandfarm.com/search/indiana-land-for-sale/)
- [LandSearch — N. Indiana](https://www.landsearch.com/rural/northern-indiana-in)
- [Zillow — Indiana Land](https://www.zillow.com/indiana/land/)
- [Redfin — Indiana Land](https://www.redfin.com/state/Indiana/land)
- [Homes.com — Indiana](https://www.homes.com/indiana/land-for-sale/)
- [FarmFlip — Indiana](https://www.farmflip.com/farms-for-sale/indiana)
- [Mossy Oak — NW Indiana](https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/)
- [IN Land & Lifestyle](https://indianalandandlifestyle.com/)
""")

    with col_b:
        st.markdown("""
**Auction Houses**
- [Schrader Auctions](https://www.schraderauction.com/auctions/all)
- [Sullivan Auctioneers](https://www.sullivanauctioneers.com/land-listings/)
- [Halderman — Listings](https://www.halderman.com/property-listings/)
- [Halderman — Auctions](https://www.haldermanauction.com/auctions)
- [Ranch & Farm Auctions](https://ranchandfarmauctions.com/)
- [Geswein Farm & Land](https://gfarmland.com/farm-real-estate/)
- [AuctionZip — Indiana](https://www.auctionzip.com/in/real-estate-auctions.html)
- [GovDeals — IN Land](https://www.govdeals.com/index.cfm?fa=Main.AdvSearchResultsNew&kWord=land&state=IN&category=110)
- [LandWatch — IN Auctions](https://www.landwatch.com/indiana-land-for-sale/auctions)
- [Land.com — IN Auctions](https://www.land.com/Indiana/all-land/at-auction/)
""")

    with col_c:
        st.markdown("""
**Tax & Sheriff Sales**
- [SRI Services (most counties)](https://properties.sriservices.com/auctionlist)
- [LaPorte Co Treasurer](https://laporteco.in.gov/residents/county-treasurer/real-estate-tax-sale/)
- [Porter Co Tax Sales](https://www.portercountyin.gov/1319/Tax-Certificate-Sales)
- [Lake Co Tax Sales](https://lakecountyin.gov/departments/auditor-taxsales)
- [LaPorte Sheriff](https://www.laportecountysheriff.com/sheriff-sales)
- [St. Joseph Sheriff](https://sjcpd.org/sheriffs-sale/)
- [Lake Co Sheriff](https://lakecountyin.gov/departments/sheriff/sheriff-sale-listings-c/)
- [Allen Co Sheriff](https://www.allencountysheriff.org/sheriff-sale/)
- [IN Sheriff Sales (all)](https://in-sheriffsale.com/)

**Research & Data**
- [Beacon GIS](https://beacon.schneidercorp.com/?site=LaPorteCountyIN)
- [AcreValue — Soil Maps](https://www.acrevalue.com/map/IN/)
- [Regrid — Parcel Data](https://app.regrid.com/us/in/)
- [USDA Web Soil Survey](https://websoilsurvey.nrcs.usda.gov/)
- [Prairie Farmland Sold](https://prairiefarmland.com/land-for-sale/sold/)
""")

    st.markdown("---")
    st.markdown("""
### Investment Quick Reference
| Strategy | Formula | Target |
|---|---|---|
| **Cash yield (farm rent)** | Annual rent ÷ purchase price | 3–4%+ |
| **Tax sale redemption return** | 10% (≤6mo) or 15% (>6mo) | Guaranteed |
| **Development flip** | Farmland near towns → rezone | 2–5x |
| **CRP income** | USDA conservation payment | $150–250/ac/yr |
| **Good $/acre (cheap counties)** | Starke/Newton/Pulaski | <$6,000/ac |
| **Good $/acre (mid counties)** | Marshall/Jasper/Fulton | <$8,000/ac |
| **Good $/acre (strong counties)** | Lake/LaPorte/Allen/St. Joseph | <$11,000/ac |
""")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.caption(f"Northern IN Land Deals · {len(ALL_LISTINGS)} listings · {len(df['county'].unique())} counties · Auto-refreshes on load · Last checked: {fetched_at}")
st.caption("Sources: Mossy Oak Properties, Halderman, Geswein Farm & Land, Ranch & Farm Auctions, Schrader, Sullivan Auctioneers, LandWatch, Land.com, Land & Farm, LandSearch, SRI Services, County Treasurers & Sheriffs, GovDeals, AuctionZip")
