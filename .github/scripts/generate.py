#!/usr/bin/env python3
"""Regenerates the animated SVG panels used by README.md.

Run it with:   py .github/scripts/generate.py

Everything below is self-contained. Only the contribution grid and the ASCII
portrait touch the network, and both degrade gracefully when offline.

Pass --strict to turn those soft failures into a non-zero exit instead. The
scheduled workflow uses it, so a flaky API can never overwrite good panels
with zeroes and a blank avatar.

To personalise the README, edit the IDENTITY / LANGS / PROJECTS blocks below
and re-run. Nothing else needs to change.
"""
import io
import json
import os
import sys
import urllib.request

STRICT = False          # set from --strict in main()

# ---------------------------------------------------------------- identity ---
USER     = "Sir-Olexander"
NAME     = "Alexandre Belostecinic"
BANNER   = "OLEXANDER"            # drawn as block ASCII in the top panel
ROLE     = "Agentic Engineer"
STATUS   = "Shipping / Learning / Napping on weekends"
LOCATION = "Coimbra, Portugal"
CONTACT  = "github.com/" + USER

# name, percent-of-stack (used by the language panel)
LANGS = [
    ("TypeScript", 46),
    ("JavaScript", 22),
    ("HTML / CSS", 18),
    ("Python",      9),
    ("Scala",       5),
]

# name, description line 1, description line 2, language tag, completion %
PROJECTS = [
    ("Aura",      "React Native app on Expo Router, with Supabase",
                  "auth and a Zustand store. TypeScript throughout.",
                  "TypeScript", 100),
    ("Solus",     "Expo Router app styled with NativeWind. Supabase",
                  "backend, Zustand state, auth and quest flows.",
                  "TypeScript", 64),
    ("Zyvo",      "Newest build of the three: Expo 55 on React",
                  "Native 0.83, new architecture, Supabase-backed.",
                  "TypeScript", 41),
    ("Perkorsi",  "Trip planner with maps, itinerary builder and",
                  "printable exports. RevenueCat subs, Supabase.",
                  "TypeScript", 100),
]

# ------------------------------------------------------------- cyan / ice ----
BG     = "#06090f"
PANEL  = "#080e17"
PANEL2 = "#0b1220"
CYAN   = "#22d3ee"
SKY    = "#7dd3fc"
DEEP   = "#0369a1"
TEXT   = "#e2e8f0"
DIM    = "#5b7085"
GRID   = "#12283a"
LEVELS = ["#0d1a26", "#0e4f63", "#157f99", "#22b8d4", "#67e8f9"]
MONO   = ("ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,"
          "'Liberation Mono',monospace")

ASSETS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))

# ------------------------------------------------------------- block font ----
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#..##", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["....#", "....#", "....#", "....#", "#...#", "#...#", ".###."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
}


def block_rows(word):
    """Render `word` as seven rows of '#'/'.', one blank column between glyphs."""
    rows = [""] * 7
    for ch in word.upper():
        glyph = FONT.get(ch, FONT[" "])
        for i in range(7):
            rows[i] += glyph[i] + "."
    return rows


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def write(name, body):
    path = os.path.join(ASSETS, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    print("  wrote assets/" + name)


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "readme-generator"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ----------------------------------------------------------- shared pieces ---
def defs(extra=""):
    return f"""  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{CYAN}" stop-opacity=".95"/>
      <stop offset="55%" stop-color="{DEEP}" stop-opacity=".55"/>
      <stop offset="100%" stop-color="{SKY}" stop-opacity=".85"/>
    </linearGradient>
    <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{CYAN}" stop-opacity=".10"/>
      <stop offset="100%" stop-color="{BG}" stop-opacity="0"/>
    </linearGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="soft" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.1" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
{extra}  </defs>
"""


def frame(w, h, title=None, cmd=None):
    """Terminal chrome: rounded panel, gradient border, traffic lights."""
    out = [
        f'  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="16" '
        f'fill="{PANEL}" stroke="url(#edge)" stroke-width="1.6"/>',
        f'  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="16" '
        f'fill="url(#sheen)"/>',
    ]
    for i, c in enumerate(("#ef4444", "#f59e0b", "#22c55e")):
        out.append(f'  <circle cx="{26 + i * 17}" cy="26" r="5" fill="{c}" '
                   f'opacity=".85"/>')
    if title:
        out.append(f'  <text x="86" y="30" font-family="{MONO}" font-size="10.5" '
                   f'letter-spacing="1.6" fill="{DIM}">{esc(title)}</text>')
    if cmd:
        out.append(f'  <text x="{w - 24}" y="30" text-anchor="end" '
                   f'font-family="{MONO}" font-size="10.5" fill="{DIM}">'
                   f'{esc(cmd)}</text>')
    out.append(f'  <line x1="14" y1="44" x2="{w - 14}" y2="44" stroke="{GRID}" '
               f'stroke-width="1"/>')
    return "\n".join(out) + "\n"


def scanline(w, h, dur="7s", y0=60):
    """The slow vertical sweep every panel in the reference video shares."""
    return (f'  <rect x="10" y="{y0}" width="{w - 20}" height="46" '
            f'fill="url(#sheen)" opacity=".5">\n'
            f'    <animate attributeName="y" values="{y0};{h - 40};{y0}" '
            f'dur="{dur}" repeatCount="indefinite" calcMode="spline" '
            f'keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>\n'
            f'  </rect>\n')


# =================================================================== banner ==
def build_banner():
    w, h = 900, 250
    rows = block_rows(BANNER)
    cols = max(len(r) for r in rows)
    fs, adv, lh = 20, 12.0, 18.0
    x0, y0 = 40, 94
    span = cols * adv

    clip = (f'    <clipPath id="reveal">\n'
            f'      <rect x="{x0 - 4}" y="{y0 - 18}" height="{lh * 7 + 8}" '
            f'width="0">\n'
            f'        <animate attributeName="width" '
            f'values="0;{span + 8};{span + 8}" dur="3.4s" keyTimes="0;0.72;1" '
            f'fill="freeze"/>\n'
            f'      </rect>\n    </clipPath>\n')

    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(BANNER)}">',
            defs(clip),
            f'  <rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
            frame(w, h, "IDENTITY", USER + "@github")]

    body.append(f'  <text x="{x0}" y="66" font-family="{MONO}" font-size="12" '
                f'fill="{DIM}"><tspan fill="{CYAN}">$</tspan> ./whoami '
                f'--render ascii</text>')

    body.append('  <g clip-path="url(#reveal)" filter="url(#glow)">')
    for i, row in enumerate(rows):
        line = row.replace("#", "█").replace(".", " ")
        body.append(f'    <text x="{x0}" y="{y0 + i * lh:.0f}" '
                    f'font-family="{MONO}" font-size="{fs}" xml:space="preserve" '
                    f'fill="{CYAN}" opacity=".92">{esc(line)}</text>')
    body.append('  </g>')

    body.append(f'  <rect y="{y0 - 16}" width="10" height="{lh * 7:.0f}" '
                f'fill="{SKY}" opacity=".75">\n'
                f'    <animate attributeName="x" '
                f'values="{x0};{x0 + span};{x0 + span}" dur="3.4s" '
                f'keyTimes="0;0.72;1" fill="freeze"/>\n'
                f'    <animate attributeName="opacity" '
                f'values=".75;.75;0;.75;0;.75" dur="5s" '
                f'keyTimes="0;0.68;0.76;0.84;0.92;1" repeatCount="indefinite"/>\n'
                f'  </rect>')

    body.append(f'  <text x="{x0}" y="228" font-family="{MONO}" font-size="12.5" '
                f'fill="{DIM}">{esc(ROLE)} <tspan fill="{GRID}">|</tspan> '
                f'<tspan fill="{SKY}" opacity=".8">{esc(LOCATION)}</tspan></text>')
    body.append("</svg>")
    write("banner.svg", "\n".join(body) + "\n")


# ===================================================================== hero ==
def build_hero(dots, contributions):
    w, h = 900, 250
    extra = ('    <linearGradient id="card" x1="0" y1="0" x2="1" y2="1">\n'
             '      <stop offset="0%" stop-color="#0a1b28"/>\n'
             '      <stop offset="45%" stop-color="#071620"/>\n'
             '      <stop offset="100%" stop-color="#040a12"/>\n'
             '    </linearGradient>\n'
             '    <clipPath id="av"><circle cx="92" cy="128" r="50"/></clipPath>\n')

    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(NAME)}">',
            defs(extra),
            f'  <rect width="{w}" height="{h}" rx="18" fill="{BG}"/>',
            f'  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" '
            f'fill="url(#card)" stroke="url(#edge)" stroke-width="1.8"/>',
            scanline(w, h, "9s", 20)]

    # Avatar as a dot matrix. Drawn with plain SVG shapes rather than an
    # embedded raster, because GitHub proxies these files with a strict CSP
    # and a data: URI in <image> is not reliably allowed through it.
    body.append(f'  <circle cx="92" cy="128" r="50" fill="{PANEL2}"/>')
    if dots:
        body.append('  <g clip-path="url(#av)">')
        for cx, cy, r, col in dots:
            body.append(f'    <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
                        f'fill="{col}"/>')
        body.append('  </g>')

    body.append(f'  <circle cx="92" cy="128" r="51" fill="none" stroke="{CYAN}" '
                f'stroke-width="2" opacity=".9" filter="url(#soft)"/>')
    body.append(f'  <circle cx="92" cy="128" r="57" fill="none" stroke="{CYAN}" '
                f'stroke-width="1" opacity=".35" stroke-dasharray="4 7">\n'
                f'    <animateTransform attributeName="transform" type="rotate" '
                f'from="0 92 128" to="360 92 128" dur="24s" '
                f'repeatCount="indefinite"/>\n  </circle>')

    body.append(f'  <text x="172" y="76" font-family="{MONO}" font-size="12.5" '
                f'letter-spacing="1.2" fill="{CYAN}" opacity=".9">@{USER}</text>')
    body.append(f'  <text x="172" y="118" font-family="{MONO}" font-size="32" '
                f'font-weight="700" fill="{TEXT}" filter="url(#soft)">'
                f'{esc(NAME)}</text>')
    body.append(f'  <text x="172" y="146" font-family="{MONO}" font-size="12.5" '
                f'fill="{SKY}" opacity=".88">{esc(ROLE)}</text>')
    body.append(f'  <text x="172" y="169" font-family="{MONO}" font-size="11" '
                f'fill="{DIM}"><tspan fill="{GRID}">// </tspan>'
                f'{esc(STATUS)}</text>')

    x = 172
    for lang, _ in LANGS[:4]:
        pw = len(lang) * 7.4 + 22
        body.append(f'  <g opacity=".92">'
                    f'<rect x="{x:.0f}" y="188" width="{pw:.0f}" height="24" '
                    f'rx="12" fill="{PANEL2}" stroke="{DEEP}" stroke-width="1"/>'
                    f'<text x="{x + pw / 2:.0f}" y="204" text-anchor="middle" '
                    f'font-family="{MONO}" font-size="10.5" fill="{SKY}">'
                    f'{esc(lang)}</text></g>')
        x += pw + 10

    body.append(f'  <text x="{w - 40}" y="112" text-anchor="end" '
                f'font-family="{MONO}" font-size="40" font-weight="700" '
                f'fill="{CYAN}" filter="url(#soft)">{contributions:,}'
                f'<animate attributeName="opacity" values="0;1" dur="1.2s" '
                f'fill="freeze"/></text>')
    body.append(f'  <text x="{w - 40}" y="132" text-anchor="end" '
                f'font-family="{MONO}" font-size="9.5" letter-spacing="2" '
                f'fill="{DIM}">CONTRIBUTIONS / YR</text>')
    body.append("</svg>")
    write("hero.svg", "\n".join(body) + "\n")


# ================================================================= projects ==
def build_projects():
    w, h = 900, 430
    cw, ch = 414, 160
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="Featured projects">',
            defs(),
            f'  <rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
            frame(w, h, "PROJECTS.LIST", "./projects.sh --all")]

    for i, (title, d1, d2, lang, pct) in enumerate(PROJECTS):
        cx = 26 + (i % 2) * (cw + 20)
        cy = 66 + (i // 2) * (ch + 18)
        delay = i * 0.22
        body.append(f'  <g opacity="0"><animate attributeName="opacity" '
                    f'values="0;1" dur=".6s" begin="{delay:.2f}s" fill="freeze"/>')
        body.append(f'    <rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" '
                    f'rx="12" fill="{PANEL2}" stroke="{DEEP}" stroke-width="1.2" '
                    f'opacity=".95"/>')
        body.append(f'    <text x="{cx + 18}" y="{cy + 22}" font-family="{MONO}" '
                    f'font-size="9.5" letter-spacing="1.4" fill="{DIM}">'
                    f'▸ {esc(title.lower())}</text>')
        body.append(f'    <text x="{cx + 18}" y="{cy + 52}" font-family="{MONO}" '
                    f'font-size="17" font-weight="700" fill="{CYAN}" '
                    f'filter="url(#soft)">{esc(title)}</text>')
        body.append(f'    <text x="{cx + 18}" y="{cy + 78}" font-family="{MONO}" '
                    f'font-size="10.5" fill="{DIM}">{esc(d1)}</text>')
        body.append(f'    <text x="{cx + 18}" y="{cy + 94}" font-family="{MONO}" '
                    f'font-size="10.5" fill="{DIM}">{esc(d2)}</text>')

        pw = len(lang) * 6.6 + 20
        body.append(f'    <rect x="{cx + 18}" y="{cy + 112}" width="{pw:.0f}" '
                    f'height="21" rx="10.5" fill="{PANEL}" stroke="{DEEP}" '
                    f'stroke-width="1"/>'
                    f'<text x="{cx + 18 + pw / 2:.0f}" y="{cy + 126}" '
                    f'text-anchor="middle" font-family="{MONO}" font-size="9.5" '
                    f'fill="{SKY}">{esc(lang)}</text>')

        rx, ry, r = cx + cw - 52, cy + ch // 2, 24
        circ = 2 * 3.14159265 * r
        body.append(f'    <circle cx="{rx}" cy="{ry}" r="{r}" fill="none" '
                    f'stroke="{GRID}" stroke-width="5"/>')
        body.append(f'    <circle cx="{rx}" cy="{ry}" r="{r}" fill="none" '
                    f'stroke="{CYAN}" stroke-width="5" stroke-linecap="round" '
                    f'transform="rotate(-90 {rx} {ry})" '
                    f'stroke-dasharray="{circ:.1f}" '
                    f'stroke-dashoffset="{circ:.1f}" filter="url(#soft)">'
                    f'<animate attributeName="stroke-dashoffset" '
                    f'values="{circ:.1f};{circ * (1 - pct / 100):.1f}" dur="1.3s" '
                    f'begin="{delay + 0.3:.2f}s" fill="freeze" calcMode="spline" '
                    f'keySplines="0.2 0.7 0.3 1"/></circle>')
        body.append(f'    <text x="{rx}" y="{ry + 5}" text-anchor="middle" '
                    f'font-family="{MONO}" font-size="12.5" font-weight="700" '
                    f'fill="{TEXT}">{pct}%</text>')
        body.append("  </g>")
    body.append("</svg>")
    write("projects.svg", "\n".join(body) + "\n")


# ===================================================================== scan ==
def build_scan(ascii_rows, info):
    w, h = 900, 400
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="Profile scan">',
            defs(),
            f'  <rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
            frame(w, h, "VISUAL.MAP", f"{USER}@github ~ $ ./profile-scan --live")]

    # two inner panes
    for px, pw in ((18, 414), (450, 432)):
        body.append(f'  <rect x="{px}" y="56" width="{pw}" height="326" rx="10" '
                    f'fill="{PANEL2}" stroke="{DEEP}" stroke-width="1" '
                    f'opacity=".9"/>')

    body.append(f'  <text x="34" y="76" font-family="{MONO}" font-size="9" '
                f'letter-spacing="1.6" fill="{DIM}">VISUAL.MAP</text>')
    body.append(f'  <text x="466" y="76" font-family="{MONO}" font-size="9" '
                f'letter-spacing="1.6" fill="{DIM}">SYSTEM.INFO</text>')
    body.append(f'  <circle cx="866" cy="72" r="3.5" fill="{CYAN}">'
                f'<animate attributeName="opacity" values="1;.15;1" dur="2s" '
                f'repeatCount="indefinite"/></circle>')
    body.append(f'  <text x="852" y="76" text-anchor="end" font-family="{MONO}" '
                f'font-size="8.5" letter-spacing="1.4" fill="{CYAN}" '
                f'opacity=".7">LIVE</text>')

    # ASCII portrait, revealed row by row
    lh, y0 = 11.4, 100
    for i, row in enumerate(ascii_rows):
        body.append(f'  <text x="46" y="{y0 + i * lh:.1f}" font-family="{MONO}" '
                    f'font-size="11" xml:space="preserve" fill="{CYAN}" '
                    f'opacity="0" filter="url(#soft)">{esc(row)}'
                    f'<animate attributeName="opacity" values="0;.85" dur=".35s" '
                    f'begin="{i * 0.06:.2f}s" fill="freeze"/></text>')

    # key / value readout
    ry = 104
    for k, v in info:
        body.append(f'  <text x="470" y="{ry}" font-family="{MONO}" '
                    f'font-size="10.5" fill="{DIM}">{esc(k)}</text>')
        body.append(f'  <text x="866" y="{ry}" text-anchor="end" '
                    f'font-family="{MONO}" font-size="10.5" fill="{TEXT}" '
                    f'opacity="0">{esc(v)}<animate attributeName="opacity" '
                    f'values="0;1" dur=".4s" begin="{0.4 + ry * 0.004:.2f}s" '
                    f'fill="freeze"/></text>')
        ry += 27
    body.append("</svg>")
    write("scan.svg", "\n".join(body) + "\n")


# ================================================================= activity ==
def build_activity(days, total):
    w, h = 900, 250
    cell, gap = 11.0, 2.6
    pitch = cell + gap
    weeks = (len(days) + 6) // 7
    grid_w = weeks * pitch
    x0 = (w - grid_w) / 2
    y0 = 104
    flight = 9.0

    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{total} contributions in the last year">',
            defs(),
            f'  <rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
            frame(w, h, "ACTIVITY", "--last-year")]

    body.append(f'  <text x="26" y="70" font-family="{MONO}" font-size="15" '
                f'font-weight="700" fill="{TEXT}">Contribution Activity</text>')
    body.append(f'  <text x="26" y="88" font-family="{MONO}" font-size="11" '
                f'fill="{CYAN}" opacity=".85">{total:,} contributions in the '
                f'last year</text>')

    lx = w - 26 - 5 * 13 - 44
    body.append(f'  <text x="{lx}" y="88" font-family="{MONO}" font-size="9.5" '
                f'fill="{DIM}">Less</text>')
    for i, col in enumerate(LEVELS):
        body.append(f'  <rect x="{lx + 30 + i * 13}" y="79" width="9" height="9" '
                    f'rx="2" fill="{col}"/>')
    body.append(f'  <text x="{lx + 30 + 5 * 13 + 4}" y="88" font-family="{MONO}" '
                f'font-size="9.5" fill="{DIM}">More</text>')

    busiest = []
    for idx, d in enumerate(days):
        wk, dow = idx // 7, idx % 7
        cx = x0 + wk * pitch
        cy = y0 + dow * pitch
        lvl = int(d.get("level", 0))
        body.append(f'  <rect x="{cx:.1f}" y="{cy:.1f}" width="{cell}" '
                    f'height="{cell}" rx="2.4" fill="{LEVELS[lvl]}" opacity="0">'
                    f'<animate attributeName="opacity" values="0;1" dur=".5s" '
                    f'begin="{wk * 0.012:.2f}s" fill="freeze"/></rect>')
        if lvl >= 3:
            busiest.append((wk, cx, cy, d.get("count", 0)))

    # the jet: crosses the year left to right, fires on the busy days
    jy = y0 + 3 * pitch + cell / 2
    body.append(f'  <g filter="url(#glow)">')
    body.append(f'    <g transform="translate({x0 - 40} {jy})">')
    body.append(f'      <animateTransform attributeName="transform" '
                f'type="translate" values="{x0 - 40} {jy};{x0 + grid_w + 40} '
                f'{jy}" dur="{flight}s" repeatCount="indefinite"/>')
    body.append(f'      <path d="M-10 0 L10 0 M10 0 L2 -5 M10 0 L2 5" '
                f'stroke="{SKY}" stroke-width="1.2" opacity=".55" fill="none"/>')
    body.append(f'      <path d="M0 -6 L14 0 L0 6 L4 0 Z" fill="{TEXT}" '
                f'stroke="{CYAN}" stroke-width="1"/>')
    body.append(f'    </g>')
    body.append(f'  </g>')

    for wk, cx, cy, _cnt in busiest[:26]:
        begin = (wk * pitch) / grid_w * flight
        body.append(f'  <circle cx="{cx + cell / 2:.1f}" cy="{cy + cell / 2:.1f}" '
                    f'r="2" fill="{SKY}" opacity="0">'
                    f'<animate attributeName="r" values="2;13" dur=".8s" '
                    f'begin="{begin:.2f}s;{begin + flight:.2f}s" '
                    f'repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values=".9;0" dur=".8s" '
                    f'begin="{begin:.2f}s;{begin + flight:.2f}s" '
                    f'repeatCount="indefinite"/></circle>')

    body.append(f'  <text x="{w / 2}" y="230" text-anchor="middle" '
                f'font-family="{MONO}" font-size="10" fill="{DIM}">A jet flies '
                f'the length of the year and fires at the busiest days. Give it '
                f'a few seconds.</text>')
    body.append("</svg>")
    write("activity.svg", "\n".join(body) + "\n")


# =================================================================== signal ==
def build_signal(tiles):
    w, h = 900, 210
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="Profile signal">',
            defs(),
            f'  <rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
            frame(w, h, "SIGNAL", "--activity-only")]

    body.append(f'  <text x="26" y="70" font-family="{MONO}" font-size="15" '
                f'font-weight="700" fill="{TEXT}">Profile Signal</text>')
    body.append(f'  <text x="26" y="88" font-family="{MONO}" font-size="10.5" '
                f'fill="{DIM}">Activity metrics, pulled live from the GitHub '
                f'contribution graph</text>')

    tw, gap = 200, 18
    for i, (label, value, frac) in enumerate(tiles):
        tx = 26 + i * (tw + gap)
        ty = 104
        body.append(f'  <rect x="{tx}" y="{ty}" width="{tw}" height="76" rx="10" '
                    f'fill="{PANEL2}" stroke="{DEEP}" stroke-width="1" '
                    f'opacity=".95"/>')
        body.append(f'    <text x="{tx + 16}" y="{ty + 22}" font-family="{MONO}" '
                    f'font-size="9" letter-spacing="1.5" fill="{DIM}">'
                    f'{esc(label)}</text>')
        body.append(f'    <text x="{tx + 16}" y="{ty + 50}" font-family="{MONO}" '
                    f'font-size="24" font-weight="700" fill="{CYAN}" '
                    f'filter="url(#soft)" opacity="0">{esc(value)}'
                    f'<animate attributeName="opacity" values="0;1" dur=".5s" '
                    f'begin="{i * 0.14:.2f}s" fill="freeze"/></text>')
        body.append(f'    <rect x="{tx + 16}" y="{ty + 60}" width="{tw - 32}" '
                    f'height="4" rx="2" fill="{GRID}"/>')
        body.append(f'    <rect x="{tx + 16}" y="{ty + 60}" width="0" height="4" '
                    f'rx="2" fill="{CYAN}" opacity=".9">'
                    f'<animate attributeName="width" '
                    f'values="0;{(tw - 32) * frac:.0f}" dur="1.1s" '
                    f'begin="{i * 0.14 + 0.2:.2f}s" fill="freeze" '
                    f'calcMode="spline" keySplines="0.2 0.7 0.3 1"/></rect>')
    body.append("</svg>")
    write("signal.svg", "\n".join(body) + "\n")


# ==================================================================== langs ==
def build_langs():
    w, h = 900, 190
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="Language stack">',
            defs(),
            f'  <rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
            frame(w, h, "LANGUAGE.STACK", "--by-usage")]

    body.append(f'  <text x="26" y="70" font-family="{MONO}" font-size="15" '
                f'font-weight="700" fill="{TEXT}">Language Stack</text>')

    bar_x, bar_w, bar_y = 26, w - 52, 88
    total = sum(p for _, p in LANGS) or 1
    x = bar_x
    shades = [CYAN, "#22b8d4", "#157f99", "#0e4f63", "#0d2a3a"]
    body.append(f'  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="18" '
                f'rx="9" fill="{GRID}"/>')
    for i, (name, pct) in enumerate(LANGS):
        seg = bar_w * pct / total
        col = shades[i % len(shades)]
        body.append(f'  <rect x="{x:.1f}" y="{bar_y}" width="0" height="18" '
                    f'fill="{col}" opacity=".95">'
                    f'<animate attributeName="width" values="0;{seg:.1f}" '
                    f'dur=".9s" begin="{i * 0.12:.2f}s" fill="freeze" '
                    f'calcMode="spline" keySplines="0.2 0.7 0.3 1"/></rect>')
        x += seg

    lx = 26
    for i, (name, pct) in enumerate(LANGS):
        col = shades[i % len(shades)]
        body.append(f'  <circle cx="{lx + 6}" cy="{h - 52}" r="4.5" '
                    f'fill="{col}"/>')
        body.append(f'  <text x="{lx + 18}" y="{h - 48}" font-family="{MONO}" '
                    f'font-size="11" fill="{TEXT}">{esc(name)}</text>')
        body.append(f'  <text x="{lx + 18}" y="{h - 30}" font-family="{MONO}" '
                    f'font-size="10" fill="{DIM}">{pct}%</text>')
        lx += len(name) * 7.6 + 46
    body.append("</svg>")
    write("langs.svg", "\n".join(body) + "\n")


# ===================================================================== data ==
def load_contributions():
    """Real contribution calendar. Returns (days, total, active, streak)."""
    url = f"https://github-contributions-api.jogruber.de/v4/{USER}?y=last"
    try:
        data = json.loads(fetch(url))
    except Exception as exc:                                  # offline / rate-limited
        if STRICT:
            raise SystemExit("FATAL: contribution API unavailable: " + str(exc))
        print("  ! contribution API unavailable (" + str(exc) + "), using blanks")
        return [{"count": 0, "level": 0} for _ in range(371)], 0, 0, 0

    days = data.get("contributions", [])
    total = data.get("total", {}).get("lastYear", 0)
    active = sum(1 for d in days if d.get("count", 0) > 0)
    streak = best = 0
    for d in days:
        if d.get("count", 0) > 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return days, total, active, best


def _mix(a, b, t):
    """Linear blend between two #rrggbb strings."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(
        int(round(pa[i] + (pb[i] - pa[i]) * t)) for i in range(3))


def load_avatar():
    """Returns (dot-matrix circles for the hero, ASCII rows for the scan)."""
    cols, rows = 46, 23
    grid = 34                       # dot matrix resolution for the hero avatar
    ramp = " .:-=+*#%@"
    try:
        from PIL import Image
        raw = fetch("https://avatars.githubusercontent.com/u/94408698?v=4&s=400")
        img = Image.open(io.BytesIO(raw)).convert("RGB")

        # -- hero: square dot matrix, brightness drives radius and tint
        sq = img.convert("L").resize((grid, grid), Image.LANCZOS)
        sp = list(sq.getdata())
        lo, hi = min(sp), max(sp)
        rng = (hi - lo) or 1
        pitch = 104.0 / grid
        ox, oy = 92 - 52.0 + pitch / 2, 128 - 52.0 + pitch / 2
        dots = []
        for r in range(grid):
            for c in range(grid):
                v = (sp[r * grid + c] - lo) / rng
                if v < 0.06:
                    continue
                dots.append((ox + c * pitch, oy + r * pitch,
                             0.35 + 1.15 * v, _mix(DEEP, SKY, v)))

        # -- scan panel: character ramp
        small = img.convert("L").resize((cols, rows), Image.LANCZOS)
        px = list(small.getdata())
        lo, hi = min(px), max(px)
        rng = (hi - lo) or 1
        art = []
        for r in range(rows):
            line = ""
            for c in range(cols):
                v = (px[r * cols + c] - lo) / rng
                line += ramp[min(len(ramp) - 1, int(v * len(ramp)))]
            art.append(line)
        return dots, art
    except Exception as exc:
        if STRICT:
            raise SystemExit("FATAL: avatar unavailable: " + str(exc))
        print("  ! avatar unavailable (" + str(exc) + "), using placeholder")
        return [], ["" for _ in range(rows)]


def main():
    global STRICT
    STRICT = "--strict" in sys.argv
    os.makedirs(ASSETS, exist_ok=True)
    print("Generating README panels for @" + USER
          + (" [strict]" if STRICT else ""))

    days, total, active, streak = load_contributions()
    avatar_dots, ascii_rows = load_avatar()

    info = [
        ("Subject",       NAME),
        ("Handle",        "@" + USER),
        ("Role",          ROLE),
        ("Status",        STATUS),
        ("Languages",     ", ".join(n for n, _ in LANGS[:3])),
        ("Contributions", f"{total:,}"),
        ("Active Days",   str(active)),
        ("Longest Streak", f"{streak} days"),
        ("Location",      LOCATION),
        ("Contact",       CONTACT),
    ]

    tiles = [
        ("CONTRIBUTIONS", f"{total:,}",     min(1.0, total / 1000)),
        ("ACTIVE DAYS",   str(active),      min(1.0, active / 365)),
        ("LONGEST STREAK", f"{streak}d",    min(1.0, streak / 60)),
        ("LANGUAGES",     str(len(LANGS)),  min(1.0, len(LANGS) / 8)),
    ]

    build_banner()
    build_hero(avatar_dots, total)
    build_projects()
    build_scan(ascii_rows, info)
    build_activity(days, total)
    build_signal(tiles)
    build_langs()
    print(f"Done. {total:,} contributions / {active} active days / "
          f"{streak}-day streak.")


if __name__ == "__main__":
    main()
