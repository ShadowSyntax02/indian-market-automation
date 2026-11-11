#!/usr/bin/env python3
"""Send a daily Indian market summary. Python standard library only."""
import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

MARKETS = [
    ("Nifty 50", "^NSEI", "points"),
    ("Bank Nifty", "^NSEBANK", "points"),
    ("BSE Sensex", "^BSESN", "points"),
    ("USD/INR", "INR=X", "₹"),
]
IST = ZoneInfo("Asia/Kolkata")


def fetch_chart(symbol):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(symbol, safe="") + "?range=10d&interval=1d"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; market-report/1.0)", "Accept": "application/json"})
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(req, timeout=12) as response:
                payload = json.load(response)
            result = (payload.get("chart", {}).get("result") or [None])[0]
            if not result:
                raise ValueError(str(payload.get("chart", {}).get("error", "No data")))
            closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
            dates = result.get("timestamp", [])
            bars = [(datetime.fromtimestamp(t, IST).date(), float(c)) for t, c in zip(dates, closes) if c is not None]
            if len(bars) < 2:
                raise ValueError("Not enough closing prices")
            return bars[-2], bars[-1]
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"{symbol}: {last_error}")


def build_report(now=None, fetch=fetch_chart):
    now = now or datetime.now(IST)
    lines = [f"📊 *Daily Indian Market Report*", f"🕠 Generated: {now:%d %b %Y, %I:%M %p} IST", ""]
    errors = []
    index_dates = []
    for name, ticker, unit in MARKETS:
        try:
            (prev_date, prev), (date, value) = fetch(ticker)
            pct = (value - prev) / prev * 100 if prev else 0
            change = value - prev
            sign = "+" if change >= 0 else ""
            arrow = "🟢" if change >= 0 else "🔴"
            val = f"₹{value:,.4f}" if unit == "₹" else f"{value:,.2f}"
            lines.append(f"{arrow} *{name}*: {val} ({sign}{change:,.2f}, {sign}{pct:.2f}%) — {date:%d %b}")
            if ticker != "INR=X":
                index_dates.append(date)
        except Exception as exc:
            errors.append(name)
            lines.append(f"⚠️ *{name}*: unavailable")
            print(f"Fetch failed: {exc}", file=sys.stderr)
    lines += ["", "Source: Yahoo Finance chart data (unofficial; may be delayed)."]
    if index_dates and max(index_dates) < now.date():
        lines.append("⚠️ Indian indices reflect their latest available session, not today's close (holiday or data delay).")
    if errors:
        lines.append("⚠️ Missing data: " + ", ".join(errors))
    if len(errors) == len(MARKETS):
        raise RuntimeError("All market-data requests failed; no report sent")
    return "\n".join(lines)


def send_slack(message):
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        raise RuntimeError("Missing SLACK_WEBHOOK_URL GitHub Actions secret")
    req = Request(url, data=json.dumps({"text": message}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=15) as response:
        status = response.status
        body = response.read().decode("utf-8", errors="replace")
    if status >= 300 or body.strip() != "ok":
        raise RuntimeError(f"Slack delivery failed: HTTP {status}, {body[:120]}")


if __name__ == "__main__":
    report = build_report()
    print(report)
    if os.getenv("DRY_RUN") == "1":
        print("DRY_RUN=1: skipped Slack send")
    else:
        send_slack(report)
        print("Slack message delivered")
