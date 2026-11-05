# Web3 Market Brief

[![Daily Brief](https://github.com/bizanye8/web3-market-brief/actions/workflows/daily-brief.yml/badge.svg)](https://github.com/bizanye8/web3-market-brief/actions/workflows/daily-brief.yml)
![Updates](https://img.shields.io/badge/updates-daily%2009%3A15%20CST-3fb950?style=flat-square)
![Automation](https://img.shields.io/badge/automation-GitHub%20Actions-2f81f7?style=flat-square)
![API keys](https://img.shields.io/badge/API%20keys-none%20required-f0b429?style=flat-square)

**A market brief that writes itself.** Every morning at 09:15 (Asia/Shanghai), a GitHub Action fetches public market data — no API keys, no server — and commits a dated brief to this repository.

### 📄 Read the latest brief → [latest.md](latest.md) · Archive → [briefs/](briefs/)

## What each brief contains

- **Prices** — BTC, ETH, SOL, SUI: last price, 24h / 7d / 30d change, and a 30-day sparkline chart (green = up, red = down)
- **Perpetual funding rates** — BTC / ETH / SOL perps, per-8h rate with an annualized approximation
- **Sentiment** — the Fear & Greed Index

## How it works

```
GitHub Actions (cron 01:15 UTC)
        │
        ▼
scripts/brief.py  ──►  Binance public data · OKX public API · alternative.me
        │
        ▼
briefs/YYYY-MM-DD.md  +  latest.md  +  assets/spark-*.svg   (committed by the bot)
```

- Pure Python standard library — zero dependencies to install or break
- Every data source degrades independently: a failed fetch renders as `n/a`, never as a failed brief
- The full history lives in git: every day's market, diff-able forever

## Run it yourself

```bash
python3 scripts/brief.py   # writes briefs/<today>.md, latest.md, assets/
```

---

*An information snapshot, not financial advice. Built and operated by [BizAnyE](https://github.com/bizanye8) — Web3 operations & community, 3+ years trading spot and perpetuals.*
