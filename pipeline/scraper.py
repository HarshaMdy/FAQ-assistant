# pipeline/scraper.py
"""
Phase 2: Document Scraper
Scrapes strictly the specified Groww mutual fund URLs defined in config.yaml.
Extracts both HTML text/tables and Next.js hydration props (mfServerSideData)
to capture exact scheme facts: Expense Ratio, Exit Load, Minimum SIP, Lock-in, Benchmark.
"""

import json
import os
import sys
import re
import yaml
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
import urllib.request
import urllib.error

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


def fetch_with_urllib(url: str) -> str:
    """Fetch page content using urllib with custom user-agent."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_next_data(html: str) -> dict:
    """Extract structured scheme properties from Next.js hydration payload."""
    facts = {}
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(\{.*?\})</script>', html, re.DOTALL)
    if not m:
        return facts

    try:
        data = json.loads(m.group(1))
        props = data.get("props", {}).get("pageProps", {})
        mf = props.get("mfServerSideData", {})

        if isinstance(mf, dict) and mf:
            if mf.get("scheme_name"):
                facts["Scheme Name"] = str(mf["scheme_name"])

            if mf.get("expense_ratio") is not None:
                facts["Expense Ratio"] = f"{mf['expense_ratio']}%"

            if mf.get("min_sip_investment") is not None:
                facts["Minimum SIP"] = f"₹{mf['min_sip_investment']}"

            if mf.get("min_investment_amount") is not None:
                facts["Minimum Investment Amount"] = f"₹{mf['min_investment_amount']}"

            if mf.get("exit_load") is not None:
                facts["Exit Load"] = str(mf["exit_load"])

            # Lock-in extraction
            lock_in = mf.get("lock_in")
            if isinstance(lock_in, dict):
                yrs = lock_in.get("years", 0)
                if yrs:
                    facts["Lock-in Period"] = f"{yrs} Years mandatory lock-in period for ELSS Tax Saver"
            elif mf.get("additional_details", {}).get("lock_in_yrs"):
                facts["Lock-in Period"] = f"{mf['additional_details']['lock_in_yrs']} Years mandatory lock-in"

            if mf.get("benchmark_name"):
                facts["Benchmark Index"] = str(mf["benchmark_name"])

            if mf.get("category"):
                facts["Category"] = str(mf["category"])

            if mf.get("fund_manager"):
                facts["Fund Manager"] = str(mf["fund_manager"])

            if mf.get("aum") is not None:
                facts["AUM (Fund Size)"] = f"₹{mf['aum']} Cr"

            if mf.get("groww_rating"):
                facts["Groww Rating"] = f"{mf['groww_rating']} / 5"

            # Capital gains statement procedure
            facts["Statement Download"] = (
                "To download account statement or capital gains statement: Log into Groww, "
                "navigate to Profile > Reports > Mutual Funds > Capital Gains Statement."
            )

    except Exception as e:
        print(f"  [Notice] Next.js payload parsing error: {e}")

    return facts


def parse_page(html: str) -> dict:
    """Extract clean text, Next.js facts, and tables from HTML."""
    # First extract Next.js structured facts
    next_facts = extract_next_data(html)

    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style tags for clean prose extraction
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    raw_text = soup.get_text(separator="\n", strip=True)

    tables = []

    # Inject Next.js key facts as primary table
    if next_facts:
        tables.append(next_facts)

    # Extract <table> rows
    for table in soup.find_all("table"):
        row_dict = {}
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) == 2:
                row_dict[cells[0]] = cells[1]
            elif len(cells) > 2:
                row_dict[cells[0]] = " | ".join(cells[1:])
        if row_dict:
            tables.append(row_dict)

    # Extract <dl> definition lists
    for dl in soup.find_all("dl"):
        dl_dict = {}
        dts = [dt.get_text(strip=True) for dt in dl.find_all("dt")]
        dds = [dd.get_text(strip=True) for dd in dl.find_all("dd")]
        for k, v in zip(dts, dds):
            if k and v:
                dl_dict[k] = v
        if dl_dict:
            tables.append(dl_dict)

    return {
        "raw_text": raw_text,
        "tables": tables
    }


def run_scraper():
    """Execute scraping strictly for configured URLs."""
    sources = CONFIG.get("data_sources", {}).get("urls", [])
    print(f"\n=======================================================")
    print(f" Phase 2: Scraping {len(sources)} Shared Target Links")
    print(f"=======================================================\n")

    results = []
    for idx, source in enumerate(sources, 1):
        url = source["url"]
        slug = source["slug"]
        print(f"[{idx}/{len(sources)}] Scraping: {slug}")
        print(f"      URL: {url}")

        try:
            html = fetch_with_urllib(url)
            parsed = parse_page(html)

            record = {
                "slug": slug,
                "url": url,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "raw_text": parsed["raw_text"],
                "tables": parsed["tables"],
                "char_count": len(parsed["raw_text"]),
                "table_count": len(parsed["tables"]),
            }

            out_path = RAW_DIR / f"{slug}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)

            print(f"      [OK] Extracted {len(parsed['raw_text'])} chars, {len(parsed['tables'])} table blocks")
            print(f"      [OK] Saved to: {out_path.name}\n")
            results.append(record)

        except Exception as e:
            print(f"      [FAIL] Error scraping {slug}: {e}\n")

    print(f"[Scraper] Completed. {len(results)}/{len(sources)} pages scraped successfully.\n")
    return results


if __name__ == "__main__":
    run_scraper()
