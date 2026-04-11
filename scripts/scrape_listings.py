"""
Scraper that pulls fresh land listings from multiple sources and saves to data/live_listings.json.
Runs on GitHub Actions cron every 6 hours.
Uses Playwright for JS-rendered sites, falls back to requests for static HTML.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_FILE = DATA_DIR / "live_listings.json"
NOW = datetime.now(timezone.utc).isoformat()

# Playwright is optional — if unavailable, fall back to requests
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("⚠ Playwright not available — using requests only", file=sys.stderr)


def playwright_get(url, wait_ms=3000, timeout_ms=30000):
    """Render a JS page with Playwright and return HTML"""
    if not HAS_PLAYWRIGHT:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=HEADERS["User-Agent"])
            page = ctx.new_page()
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            page.wait_for_timeout(wait_ms)  # let JS render
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"  [Playwright ERR] {url}: {e}", file=sys.stderr)
        return None


def safe_get(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
        print(f"  [{r.status_code}] {url}", file=sys.stderr)
    except Exception as e:
        print(f"  [ERR] {url}: {e}", file=sys.stderr)
    return None


def extract_text_near(html, url_pattern_snippet, max_chars=600):
    """Find text surrounding a URL in HTML"""
    idx = html.find(url_pattern_snippet)
    if idx < 0:
        return ""
    start = max(0, idx - max_chars)
    end = min(len(html), idx + max_chars)
    snippet = html[start:end]
    snippet = re.sub(r'<[^>]+>', ' ', snippet)
    snippet = re.sub(r'\s+', ' ', snippet)
    return snippet.strip()


def parse_acres(text):
    m = re.search(r'(\d+(?:[\.,]\d+)?)\s*[±+]?\s*(?:acres?|ac\b)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except:
            return None
    return None


def parse_price(text):
    m = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)', text)
    if m:
        try:
            return int(float(m.group(1).replace(",", "")))
        except:
            return None
    return None


def scrape_mossy_oak():
    """Scrape Mossy Oak NW Indiana"""
    listings = []
    for page_url in [
        "https://www.mossyoakproperties.com/land-for-sale/indiana/northwest/",
        "https://www.mossyoakproperties.com/land-for-sale/indiana/",
    ]:
        html = safe_get(page_url)
        # Try Playwright if requests returned no property URLs
        if not html or '/property/' not in (html or ''):
            html = playwright_get(page_url, wait_ms=4000) or html
        if not html:
            continue
        prop_urls = set(re.findall(r'href="(/property/[^"?]+/\d+/)"', html))
        for url_path in list(prop_urls)[:40]:
            try:
                slug = url_path.rstrip("/").split("/")[-2]
                title = slug.replace("-", " ").title()[:120]
                context = extract_text_near(html, url_path)
                acres = parse_acres(context) or parse_acres(slug)
                price = parse_price(context)
                ppa = int(price / acres) if (price and acres and acres > 0) else None
                listings.append({
                    "title": title,
                    "url": urljoin("https://www.mossyoakproperties.com", url_path),
                    "acres": acres,
                    "price": price,
                    "price_per_acre": ppa,
                    "source": "Mossy Oak Properties",
                    "status": "Active",
                    "state": "IN",
                    "scraped_at": NOW,
                })
            except Exception:
                continue
        if listings:
            break
    return listings


def scrape_halderman():
    """Scrape Halderman"""
    listings = []
    url = "https://www.halderman.com/property-listings/"
    html = safe_get(url)
    if not html or '/real-estate-listing/' not in html:
        html = playwright_get(url, wait_ms=4000) or html
    if not html:
        return listings
    prop_urls = set(re.findall(r'href="(/real-estate-listing/\?id=[a-f0-9-]+)"', html))
    for url_path in list(prop_urls)[:30]:
        context = extract_text_near(html, url_path, max_chars=400)
        acres = parse_acres(context)
        price = parse_price(context)
        title_match = re.search(r'([A-Z][A-Za-z0-9\s\'\.&,\-]{10,100}(?:Farm|Acres|Tract|Ground|Land|Co))', context)
        title = title_match.group(1).strip() if title_match else "Halderman Listing"
        listings.append({
            "title": title[:120],
            "url": urljoin("https://www.halderman.com", url_path),
            "acres": acres,
            "price": price,
            "price_per_acre": int(price/acres) if (price and acres) else None,
            "source": "Halderman",
            "status": "Active",
            "state": "IN",
            "scraped_at": NOW,
        })
    return listings


def scrape_ranchfarm():
    """Scrape Ranch & Farm Auctions"""
    listings = []
    url = "https://ranchandfarmauctions.com/auctions"
    html = safe_get(url)
    if not html or '/auction-event/' not in html:
        html = playwright_get(url, wait_ms=4000) or html
    if not html:
        return listings
    event_urls = set(re.findall(r'href="(/auction-event/[^"]+)"', html))
    for url_path in list(event_urls)[:30]:
        slug = url_path.rstrip("/").split("/")[-1]
        title = slug.replace("-", " ").title()
        acres = parse_acres(slug)
        listings.append({
            "title": title[:120],
            "url": urljoin("https://ranchandfarmauctions.com", url_path),
            "acres": acres,
            "price": None,
            "price_per_acre": None,
            "source": "Ranch & Farm Auctions",
            "status": "Auction",
            "listing_type": "Auction",
            "scraped_at": NOW,
        })
    return listings


def scrape_geswein():
    """Scrape Geswein Farm & Land"""
    listings = []
    url = "https://gfarmland.com/farm-real-estate/"
    html = safe_get(url)
    if not html or '/for-sale/' not in html:
        html = playwright_get(url, wait_ms=3000) or html
    if not html:
        return listings
    urls = set(re.findall(r'href="(https://gfarmland\.com/for-sale/[^"]+/)"', html))
    for url in list(urls)[:30]:
        slug = url.rstrip("/").split("/")[-1]
        title = slug.replace("-", " ").replace("_", " ").title()
        acres = parse_acres(slug)
        context = extract_text_near(html, url, max_chars=300)
        status = "Active"
        if "SOLD" in context.upper():
            status = "SOLD"
        elif "PENDING" in context.upper():
            status = "SALE PENDING"
        listings.append({
            "title": title[:120],
            "url": url,
            "acres": acres,
            "price": None,
            "price_per_acre": None,
            "source": "Geswein Farm & Land",
            "status": status,
            "state": "IN",
            "scraped_at": NOW,
        })
    return listings


def scrape_schrader():
    """Scrape Schrader Auctions"""
    listings = []
    html = safe_get("https://www.schraderauction.com/auctions/all")
    if not html:
        return listings
    auc_urls = set(re.findall(r'href="(/auctions/\d+)"', html))
    for url_path in list(auc_urls)[:25]:
        context = extract_text_near(html, url_path, max_chars=500)
        title_match = re.search(r'([A-Z][A-Z0-9\s±\+/\-\.,\']{20,200}(?:ACRES?|TRACTS?))', context)
        title = title_match.group(1).strip() if title_match else None
        if not title:
            continue
        acres = parse_acres(context)
        listings.append({
            "title": re.sub(r'\s+', ' ', title)[:150],
            "url": urljoin("https://www.schraderauction.com", url_path),
            "acres": acres,
            "price": None,
            "price_per_acre": None,
            "source": "Schrader Auction",
            "status": "Auction",
            "listing_type": "Auction",
            "scraped_at": NOW,
        })
    return listings


def scrape_sri():
    """Scrape SRI tax sale calendar (JS-rendered Angular app)"""
    listings = []
    url = "https://properties.sriservices.com/auctionlist"
    # SRI is a SPA — always use Playwright
    html = playwright_get(url, wait_ms=5000)
    if not html:
        html = safe_get(url)
    if not html:
        return listings
    rows = re.findall(
        r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+County[^<]*?(\d{1,2}/\d{1,2}/\d{4})',
        html
    )
    for county, date in rows[:60]:
        try:
            date_obj = datetime.strptime(date, "%m/%d/%Y")
            iso = date_obj.strftime("%Y-%m-%d")
            listings.append({
                "title": f"{county} County Tax Sale {date_obj.year}",
                "url": "https://properties.sriservices.com/auctionlist",
                "county": county,
                "acres": None,
                "price": None,
                "price_per_acre": None,
                "auction_date": iso,
                "source": "SRI Services",
                "status": "Scheduled",
                "listing_type": "Tax Sale",
                "scraped_at": NOW,
            })
        except:
            continue
    return listings


def main():
    all_listings = []
    sources = [
        ("Mossy Oak", scrape_mossy_oak),
        ("Halderman", scrape_halderman),
        ("Ranch & Farm Auctions", scrape_ranchfarm),
        ("Geswein", scrape_geswein),
        ("Schrader", scrape_schrader),
        ("SRI Tax Sales", scrape_sri),
    ]

    for name, fn in sources:
        print(f"Scraping {name}...")
        try:
            results = fn()
            results = [r for r in results if r.get("title") and len(r["title"]) > 3]
            print(f"  → {len(results)} listings")
            all_listings.extend(results)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)

    seen = set()
    unique = []
    for l in all_listings:
        url = l.get("url")
        if url and url not in seen:
            seen.add(url)
            unique.append(l)

    output = {
        "last_updated": NOW,
        "total_listings": len(unique),
        "sources_scraped": len(sources),
        "listings": unique,
    }

    OUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"\n✓ Saved {len(unique)} listings to {OUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
