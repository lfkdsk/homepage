#!/usr/bin/env python3
"""
Scan lfkdsk.org subdomains via certificate transparency logs (crt.sh)
and regenerate list.html.
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not installed, run: pip install requests", file=sys.stderr)
    sys.exit(1)

DOMAIN = "lfkdsk.org"
SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
META_FILE = SCRIPT_DIR / "subdomains-meta.json"
OUTPUT_FILE = REPO_DIR / "list.html"

# Subdomains to exclude from the listing
EXCLUDE = {"mail", "smtp", "imap", "pop", "ftp", "cpanel", "webmail", "autodiscover"}

PALETTE = [
    "#2563eb", "#e74c3c", "#3498db", "#1abc9c", "#f39c12",
    "#16a085", "#e67e22", "#c0392b", "#9b59b6", "#2980b9",
    "#27ae60", "#d35400", "#8e44ad", "#2ecc71", "#e91e63",
]

DEFAULT_ICON_SVG = (
    '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z'
    "m-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93z"
    "m6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7"
    "h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z\"/>"
)


def stable_color(subdomain: str) -> str:
    h = int(hashlib.md5(subdomain.encode()).hexdigest(), 16)
    return PALETTE[h % len(PALETTE)]


def fetch_subdomains() -> list[str]:
    url = f"https://crt.sh/?q=%.{DOMAIN}&output=json"
    print(f"Querying crt.sh for *.{DOMAIN} ...", flush=True)
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"ERROR fetching crt.sh: {exc}", file=sys.stderr)
        sys.exit(1)

    seen: set[str] = set()
    for entry in data:
        for name in entry.get("name_value", "").split("\n"):
            name = name.strip().lstrip("*.")
            if not name.endswith(f".{DOMAIN}"):
                continue
            prefix = name[: -len(f".{DOMAIN}")]
            # Skip wildcards, nested subdomains, and excluded prefixes
            if not prefix or "." in prefix or prefix in EXCLUDE:
                continue
            seen.add(name)

    result = sorted(seen)
    print(f"Found {len(result)} subdomains: {', '.join(result)}")
    return result


def build_card(subdomain: str, meta: dict) -> str:
    info = meta.get(subdomain, {})
    name = info.get("name", subdomain.split(".")[0])
    color = info.get("color", stable_color(subdomain))
    icon_svg = info.get("icon_svg", DEFAULT_ICON_SVG)
    return f"""\
            <a href="https://{subdomain}" class="card">
                <div class="icon" style="background-color: {color};">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
                        {icon_svg}
                    </svg>
                </div>
                <div class="domain-name">{name}</div>
                <div class="full-domain">{subdomain}</div>
            </a>"""


def render(subdomains: list[str], meta: dict) -> str:
    cards = "\n\n".join(build_card(s, meta) for s in subdomains)
    year = datetime.now().year
    updated = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>lfkdsk.org 功能合集 </title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background-color: #f5f5f7;
            color: #1d1d1f;
            margin: 0;
            padding: 0;
            line-height: 1.5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        header {{
            text-align: center;
            margin-bottom: 50px;
        }}
        h1 {{
            font-size: 48px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .subtitle {{
            font-size: 20px;
            font-weight: 400;
            color: #86868b;
            margin-bottom: 30px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 20px;
        }}
        .card {{
            background-color: white;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 25px 15px;
            text-decoration: none;
            color: inherit;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        .icon {{
            width: 60px;
            height: 60px;
            border-radius: 13px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .icon svg {{
            width: 60%;
            height: 60%;
        }}
        .domain-name {{
            font-size: 17px;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .full-domain {{
            font-size: 14px;
            color: #86868b;
        }}
        footer {{
            text-align: center;
            margin-top: 50px;
            color: #86868b;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>lfkdsk.org</h1>
            <div class="subtitle">所有可用的子域名</div>
        </header>

        <div class="grid">
{cards}
        </div>

        <footer>
            <p>&copy; {year} lfkdsk.org. 保留所有权利。</p>
            <p style="font-size:12px;">自动生成于 {updated}</p>
        </footer>
    </div>
</body>
</html>
"""


def main():
    meta = json.loads(META_FILE.read_text()) if META_FILE.exists() else {}

    # Base list: all subdomains explicitly configured in metadata
    known = set(meta.keys())

    # Supplement with crt.sh discoveries (catches new subdomains not yet in metadata)
    discovered = set(fetch_subdomains())

    # Merge: known first (preserves order), then any new ones found by crt.sh
    all_subdomains = sorted(known | discovered)

    if not all_subdomains:
        print("No subdomains found, aborting.", file=sys.stderr)
        sys.exit(1)

    print(f"Total subdomains: {len(all_subdomains)}")
    html = render(all_subdomains, meta)
    OUTPUT_FILE.write_text(html)
    print(f"Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
