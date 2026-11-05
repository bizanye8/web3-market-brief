#!/usr/bin/env python3
"""Web3 Market Brief generator.

Fetches public market data (no API keys), renders one daily brief as
Markdown with SVG sparklines, and writes:
  - briefs/YYYY-MM-DD.md   (the archive)
  - latest.md              (always the newest brief)
  - assets/spark-<SYM>.svg (30-day sparklines)

Sources: Binance public market data (prices/klines), OKX public API
(perpetual funding rates), alternative.me (Fear & Greed Index).
Every source degrades independently: a failed fetch becomes "n/a",
never a failed brief.
"""

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = ["BTC", "ETH", "SOL", "SUI"]
GREEN, RED, MUT = "#3fb950", "#f85149", "#8b949e"


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "web3-market-brief/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def pct(now, then):
    return (now / then - 1) * 100 if then else None


def sparkline_svg(closes, width=280, height=64):
    if len(closes) < 2:
        return None
    lo, hi = min(closes), max(closes)
    rng = (hi - lo) or 1
    pts = []
    for i, c in enumerate(closes):
        x = 4 + i * (width - 8) / (len(closes) - 1)
        y = height - 6 - (c - lo) / rng * (height - 12)
        pts.append(f"{x:.1f},{y:.1f}")
    color = GREEN if closes[-1] >= closes[0] else RED
    area = f"4,{height - 2} " + " ".join(pts) + f" {width - 4},{height - 2}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" rx="8" fill="#0d1117"/>'
        f'<polygon points="{area}" fill="{color}" opacity="0.15"/>'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2"/>'
        f'<text x="8" y="16" font-family="monospace" font-size="10" fill="{MUT}">'
        f"30d · low {lo:,.2f} · high {hi:,.2f}</text></svg>"
    )


def money(v, dec=2):
    return f"${v:,.{dec}f}" if v is not None else "n/a"


def signed(v, suffix="%", dec=2):
    if v is None:
        return "n/a"
    return f"{'+' if v >= 0 else ''}{v:,.{dec}f}{suffix}"


def main():
    now_utc = datetime.now(timezone.utc)
    now_cst = now_utc.astimezone(timezone(timedelta(hours=8)))
    day = now_utc.strftime("%Y-%m-%d")

    rows, sparks = [], {}
    for sym in ASSETS:
        price = chg24 = chg7 = chg30 = None
        try:
            t = fetch(f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={sym}USDT")
            price = float(t["lastPrice"])
            chg24 = float(t["priceChangePercent"])
        except Exception:
            pass
        try:
            k = fetch(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}USDT&interval=1d&limit=31")
            closes = [float(c[4]) for c in k]
            if price is None and closes:
                price = closes[-1]
            if len(closes) >= 8:
                chg7 = pct(closes[-1], closes[-8])
            if len(closes) >= 2:
                chg30 = pct(closes[-1], closes[0])
                svg = sparkline_svg(closes)
                if svg:
                    sparks[sym] = svg
        except Exception:
            pass
        rows.append((sym, price, chg24, chg7, chg30))

    funding = {}
    for sym in ["BTC", "ETH", "SOL"]:
        try:
            d = fetch(f"https://www.okx.com/api/v5/public/funding-rate?instId={sym}-USDT-SWAP")
            funding[sym] = float(d["data"][0]["fundingRate"]) * 100
        except Exception:
            funding[sym] = None

    fng_val = fng_cls = None
    try:
        d = fetch("https://api.alternative.me/fng/?limit=1")
        fng_val = d["data"][0]["value"]
        fng_cls = d["data"][0]["value_classification"]
    except Exception:
        pass

    os.makedirs(os.path.join(ROOT, "briefs"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for sym, svg in sparks.items():
        with open(os.path.join(ROOT, "assets", f"spark-{sym}.svg"), "w") as f:
            f.write(svg)

    lines = []
    lines.append(f"# Web3 Market Brief — {day}")
    lines.append("")
    lines.append(f"*Generated {now_utc.strftime('%Y-%m-%d %H:%M UTC')} "
                 f"({now_cst.strftime('%H:%M')} CST) · Sources: Binance public data, OKX public API, alternative.me*")
    lines.append("")
    lines.append("## Prices")
    lines.append("")
    lines.append("| Asset | Price | 24h | 7d | 30d | Trend (30d) |")
    lines.append("|---|---|---|---|---|---|")
    for sym, price, c24, c7, c30 in rows:
        dec = 4 if (price or 0) < 1 else 2
        img = f'<img src="assets/spark-{sym}.svg" width="180">' if sym in sparks else "n/a"
        lines.append(f"| **{sym}** | {money(price, dec)} | {signed(c24)} | {signed(c7)} | {signed(c30)} | {img} |")
    lines.append("")
    lines.append("## Perpetual funding (per 8h, OKX)")
    lines.append("")
    lines.append("| Market | Funding | Annualized (approx.) |")
    lines.append("|---|---|---|")
    for sym, rate in funding.items():
        ann = rate * 3 * 365 if rate is not None else None
        lines.append(f"| {sym}-USDT perp | {signed(rate, '%', 4)} | {signed(ann, '%', 1)} |")
    lines.append("")
    lines.append("## Sentiment")
    lines.append("")
    if fng_val is not None:
        lines.append(f"**Fear & Greed Index: {fng_val} — {fng_cls}**")
    else:
        lines.append("**Fear & Greed Index: n/a** (source unreachable at generation time)")
    lines.append("")
    lines.append("---")
    lines.append("*Auto-generated by [scripts/brief.py](scripts/brief.py) via GitHub Actions. "
                 "Data is public and delayed by source; this brief is an information snapshot, not financial advice.*")
    lines.append("")

    text = "\n".join(lines)
    with open(os.path.join(ROOT, "briefs", f"{day}.md"), "w") as f:
        f.write(text)
    with open(os.path.join(ROOT, "latest.md"), "w") as f:
        f.write(text)
    print(f"Brief written for {day}: " + ", ".join(
        f"{s}={money(p)}" for s, p, *_ in rows))


if __name__ == "__main__":
    main()
