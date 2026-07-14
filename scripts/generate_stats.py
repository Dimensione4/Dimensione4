#!/usr/bin/env python3
"""
Genera le card statistiche del profilo GitHub in stile Dimensione 4.
Gira dentro una GitHub Action con GITHUB_TOKEN standard: nessun servizio esterno.
Output: dist/stats-card.svg e dist/langs-card.svg
"""
import json
import os
import urllib.request
from datetime import datetime, timezone

USER = "Dimensione4"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = "dist"

# palette brand D4
BG = "#0A0E12"
BG2 = "#0E2226"
TEAL = "#00D4D4"
TEAL_DARK = "#0E7C7B"
CREAM = "#F4F1EA"
DIM = "#93A6A6"
BORDER = "#134C4C"

LANG_RAMP = ["#00D4D4", "#2BC5C5", "#33B3B3", "#1E9C9B", "#0E7C7B", "#0B5F5E"]

FONT = "Segoe UI, Helvetica, Arial, sans-serif"
MONO = "Consolas, 'Courier New', monospace"


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def collect():
    user = api("/users/" + USER)
    repos = api("/users/" + USER + "/repos?per_page=100&type=owner")
    own = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    years = max(1, int((datetime.now(timezone.utc) - created).days / 365.25))
    langs = {}
    for r in own[:30]:
        try:
            for lang, size in api("/repos/%s/%s/languages" % (USER, r["name"])).items():
                langs[lang] = langs.get(lang, 0) + size
        except Exception:
            continue
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda x: -x[1])[:6]
    top = [(name, size * 100.0 / total) for name, size in top]
    return {
        "repos": user.get("public_repos", len(repos)),
        "stars": stars,
        "followers": user.get("followers", 0),
        "years": years,
        "langs": top,
    }


def card_frame(width, height, title):
    return [
        '<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">' % (width, height, width, height),
        '<defs><radialGradient id="bg" cx="80%" cy="20%" r="90%">'
        '<stop offset="0%" stop-color="' + BG2 + '"/><stop offset="100%" stop-color="' + BG + '"/></radialGradient></defs>',
        '<rect x="0.5" y="0.5" width="%d" height="%d" rx="14" fill="url(#bg)" stroke="%s"/>' % (width - 1, height - 1, BORDER),
        '<circle cx="26" cy="27" r="3.5" fill="%s"><animate attributeName="opacity" values="1;0.25;1" dur="2.2s" repeatCount="indefinite"/></circle>' % TEAL,
        '<text x="40" y="32" font-family="%s" font-size="12" letter-spacing="3" fill="%s">%s</text>' % (MONO, TEAL, title),
        '<line x1="20" y1="46" x2="%d" y2="46" stroke="%s" stroke-opacity="0.35"/>' % (width - 20, TEAL_DARK),
    ]


def fmt(n):
    return "{:,}".format(n).replace(",", ".")


def stats_card(d):
    w, h = 430, 175
    s = card_frame(w, h, "TELEMETRIA GITHUB")
    items = [
        (fmt(d["repos"]), "REPOSITORY"),
        (fmt(d["stars"]), "STELLE"),
        (fmt(d["followers"]), "FOLLOWER"),
        (str(d["years"]) + "+", "ANNI ATTIVO"),
    ]
    cell = (w - 40) / 4.0
    for i, (val, lab) in enumerate(items):
        cx = 20 + cell * i + cell / 2
        if i:
            s.append('<line x1="%.0f" y1="72" x2="%.0f" y2="130" stroke="%s" stroke-opacity="0.3"/>' % (20 + cell * i, 20 + cell * i, TEAL_DARK))
        s.append('<text x="%.0f" y="108" text-anchor="middle" font-family="%s" font-size="30" font-weight="700" fill="%s">%s</text>' % (cx, FONT, TEAL, val))
        s.append('<text x="%.0f" y="132" text-anchor="middle" font-family="%s" font-size="9" letter-spacing="2" fill="%s">%s</text>' % (cx, MONO, DIM, lab))
    s.append('<text x="20" y="158" font-family="%s" font-size="9" letter-spacing="1" fill="%s">github.com/%s · aggiornata ogni notte</text>' % (MONO, TEAL_DARK, USER))
    s.append("</svg>")
    return "\n".join(s)


def langs_card(d):
    w, h = 430, 175
    s = card_frame(w, h, "LINGUAGGI PRINCIPALI")
    bar_x, bar_w = 130, 220
    y = 62
    if not d["langs"]:
        s.append('<text x="20" y="100" font-family="%s" font-size="11" fill="%s">nessun dato disponibile</text>' % (MONO, DIM))
    for i, (name, pct) in enumerate(d["langs"]):
        color = LANG_RAMP[i % len(LANG_RAMP)]
        bw = max(3, bar_w * pct / 100.0)
        s.append('<text x="20" y="%d" font-family="%s" font-size="11" fill="%s">%s</text>' % (y + 9, FONT, CREAM, name[:14]))
        s.append('<rect x="%d" y="%d" width="%d" height="10" rx="5" fill="%s" fill-opacity="0.18"/>' % (bar_x, y, bar_w, TEAL_DARK))
        s.append('<rect x="%d" y="%d" width="0" height="10" rx="5" fill="%s">'
                 '<animate attributeName="width" from="0" to="%.1f" dur="1.2s" begin="%.1fs" fill="freeze"/></rect>'
                 % (bar_x, y, color, bw, 0.15 * i))
        s.append('<text x="%d" y="%d" font-family="%s" font-size="10" fill="%s">%.1f%%</text>' % (bar_x + bar_w + 10, y + 9, MONO, DIM, pct))
        y += 18
    s.append("</svg>")
    return "\n".join(s)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    data = collect()
    open(os.path.join(OUT_DIR, "stats-card.svg"), "w").write(stats_card(data))
    open(os.path.join(OUT_DIR, "langs-card.svg"), "w").write(langs_card(data))
    print("Card generate:", data)


if __name__ == "__main__":
    main()
