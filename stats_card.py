#!/usr/bin/env python3
"""Render assets/stats.svg — live GitHub stats in the profile's card style.

Runs in GitHub Actions with only the Python standard library:
    GITHUB_TOKEN=... GH_LOGIN=zinmeir python3 scripts/stats_card.py
Use --sample to render with placeholder data (no network).
"""
import json, os, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "stats.svg"
ASSETS = json.loads((HERE / "stats_assets.json").read_text())

# Languages left out of the breakdown (markup/styling tends to swamp real code). Edit freely.
EXCLUDE = {"HTML", "CSS", "SCSS", "Less"}
TOP_N = 5

C = dict(bg0="#07041A", bg1="#0F0A2E", text="#E8EAFF", muted="#9AA3C7", dim="#5B6390",
         purple="#8B5CF6", cyan="#00E5FF", pink="#FF2E97")

QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, PULL_REQUEST_REVIEW]) { totalCount }
    contributionsCollection { totalCommitContributions }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, after: $after) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}"""


def gql(token, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-stats-card"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        sys.exit(f"GitHub API error: {body['errors']}")
    return body["data"]["user"]


def fetch(login, token):
    after, stars, langs, first = None, 0, {}, None
    while True:
        u = gql(token, {"login": login, "after": after})
        first = first or u
        repos = u["repositories"]
        for repo in repos["nodes"]:
            stars += repo["stargazerCount"]
            for e in repo["languages"]["edges"]:
                name = e["node"]["name"]
                size, color = langs.get(name, (0, e["node"]["color"]))
                langs[name] = (size + e["size"], color)
        if not repos["pageInfo"]["hasNextPage"]:
            break
        after = repos["pageInfo"]["endCursor"]
    cc = first["contributionsCollection"]
    return dict(
        commits=cc["totalCommitContributions"],
        repos=first["repositories"]["totalCount"],
        contributed=first["repositoriesContributedTo"]["totalCount"],
        stars=stars,
        languages=langs,
    )


SAMPLE = dict(commits=123, repos=24, contributed=13, stars=2,
              languages={"Python": (380, "#3572A5"), "JavaScript": (300, "#f1e05a"), "HTML": (150, "#e34c26"),
                         "C++": (120, "#f34b7d"), "PowerShell": (60, "#012456"), "TypeScript": (40, "#3178c6")})


# ---------------------------------------------------------------- rendering
def width(text, size, font):
    w = ASSETS["widths"][font]
    return sum(w.get(ch, 0.6) for ch in text) * size


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt(n):
    return f"{n/1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def readable(hex_color):
    """Lift very dark language colours so they stay visible on the dark card."""
    if not hex_color:
        return C["purple"]
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if lum < 70:
        k = 0.55
        r, g, b = (int(v + (255 - v) * k) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


QUOTES = [  # short, widely-quoted lines; rotated in the card
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Life is too short to run proprietary software.", "Bdale Garbee"),
    ("Simplicity is prerequisite for reliability.", "Edsger W. Dijkstra"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
]


def wrap(text, size, font, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and width(trial, size, font) > maxw:
            lines.append(cur); cur = word
        else:
            cur = trial
    return lines + [cur]


ICONS = {  # simple generic 16px line icons
    "commit": '<circle cx="8" cy="8" r="3"/><path d="M1 8h4M11 8h4"/>',
    "repo": '<path d="M3 2.5h8.5a1.5 1.5 0 0 1 1.5 1.5v9.5H4.5A1.5 1.5 0 0 1 3 12Z"/><path d="M3 12a1.5 1.5 0 0 1 1.5-1.5H13"/>',
    "contrib": '<circle cx="4" cy="3.5" r="1.8"/><circle cx="4" cy="12.5" r="1.8"/><circle cx="12" cy="8" r="1.8"/><path d="M4 5.3v5.4M5.6 4.4 10.4 7"/>',
    "star": '<path d="m8 1.8 1.9 3.9 4.3.6-3.1 3 .7 4.3L8 11.6l-3.8 2 .7-4.3-3.1-3 4.3-.6Z"/>',
}


def illustration(ox, oy):
    """Original scene: a developer with headphones at a laptop, training a model.
    Floating windows (code, training run, neural net) are linked to the laptop by flowing data lines."""
    code_rows = [(0, 40, C["purple"]), (8, 60, C["cyan"]), (8, 32, C["text"]), (16, 48, C["pink"]),
                 (8, 54, C["cyan"]), (0, 26, C["purple"])]
    code = "".join(
        f'<rect x="{10 + ind}" y="{22 + k * 8}" width="{w}" height="3.4" rx="1.7" fill="{col}" fill-opacity=".85" '
        f'class="cl" style="animation-name:c{k}"/>' for k, (ind, w, col) in enumerate(code_rows))

    # neural net: 2-3-2 nodes, edges, nodes fire left to right
    layers = [[(22, 28), (22, 52)], [(58, 20), (58, 40), (58, 60)], [(94, 30), (94, 50)]]
    edges = "".join(
        f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{C["purple"]}" stroke-opacity=".35" stroke-width="1"/>'
        for L in range(2) for a in layers[L] for b in layers[L + 1])
    nodes = "".join(
        f'<circle cx="{x}" cy="{y}" r="5" fill="#120C3A" stroke="{C["cyan"] if L != 1 else C["purple"]}" stroke-width="1.4"/>'
        f'<circle cx="{x}" cy="{y}" r="2.6" fill="{C["cyan"] if L != 1 else C["pink"]}" class="fire" style="animation-delay:{L * .45 + k * .12:.2f}s"/>'
        for L, layer in enumerate(layers) for k, (x, y) in enumerate(layer))

    stars = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{C["text"]}" class="tw" style="animation-delay:-{k * .7:.1f}s"/>'
        for k, (x, y, r) in enumerate([(20, 14, .9), (110, 10, .7), (250, 16, .8), (346, 120, .9), (12, 150, .7),
                                        (338, 200, .7), (60, 128, .6), (300, 140, .6)]))

    return f'''<g transform="translate({ox} {oy})">
  <circle cx="180" cy="176" r="150" fill="url(#halo)" class="glow"/>
  {stars}

  <!-- data flowing from the laptop to the floating windows -->
  <path d="M168 208C150 176 92 168 74 116" fill="none" stroke="url(#rim)" stroke-width="1.4" stroke-dasharray="3 6" class="flow" opacity=".7"/>
  <path d="M192 208C210 176 268 168 286 120" fill="none" stroke="url(#rim)" stroke-width="1.4" stroke-dasharray="3 6" class="flow" opacity=".7"/>

  <!-- code window -->
  <g class="bob"><g transform="translate(16 36)">
    <rect width="116" height="76" rx="9" fill="url(#scr)" stroke="#3A3380"/>
    <circle cx="10" cy="10" r="2" fill="{C["pink"]}"/><circle cx="17" cy="10" r="2" fill="#F5C451"/><circle cx="24" cy="10" r="2" fill="#3DDC97"/>
    <text x="106" y="12.5" class="stk" text-anchor="end">model.py</text>
    {code}
  </g></g>

  <!-- training run -->
  <g class="bob" style="animation-delay:-.9s"><g transform="translate(138 12)">
    <rect width="84" height="36" rx="9" fill="url(#scr)" stroke="{C["cyan"]}" stroke-opacity=".5"/>
    <text x="10" y="15" class="stk">training</text>
    <circle cx="74" cy="11.5" r="2.2" fill="#3DDC97" class="fire"/>
    <rect x="10" y="22" width="64" height="5" rx="2.5" fill="#241D57"/>
    <rect x="10" y="22" width="64" height="5" rx="2.5" fill="url(#rim)" class="prog"/>
  </g></g>

  <!-- neural network -->
  <g class="bob" style="animation-delay:-1.8s"><g transform="translate(228 40)">
    <rect width="116" height="80" rx="9" fill="url(#scr)" stroke="#3A3380"/>
    {edges}{nodes}
  </g></g>

  <!-- developer -->
  <path d="M84 312C86 236 118 204 180 200.5C242 204 274 236 276 312Z" fill="url(#hoodie)"/>
  <path d="M120 222C98 236 88 262 84 312" fill="none" stroke="{C["purple"]}" stroke-opacity=".75" stroke-width="2"/>
  <path d="M240 222C262 236 272 262 276 312" fill="none" stroke="{C["cyan"]}" stroke-opacity=".75" stroke-width="2"/>
  <g class="nod"><g transform="translate(180 207) scale(1.22) translate(-180 -214)">
    <rect x="170" y="194" width="20" height="26" rx="7" fill="#B07A5F"/>
    <path d="M165 209.5q15 11 30 0" fill="none" stroke="#D3D6E6" stroke-width="3.4" stroke-linecap="round"/>
    <path d="M166.5 211.5q13.5 9.5 27 0" fill="none" stroke="#A9AEC8" stroke-width=".8" stroke-linecap="round"/>
    <path d="M156 167C155.5 186 165 203.6 180 203.6C195 203.6 204.5 186 204 167C204.2 149 196 139 180 139C164 139 155.8 149 156 167Z" fill="#C8906C"/>
    <path d="M156 167C155.5 186 165 203.6 180 203.6C195 203.6 204.5 186 204 167C201.5 175.5 198 182 192.5 186.5C188.5 185.2 184.5 184.6 180 185C175.5 184.6 171.5 185.2 167.5 186.5C162 182 158.5 175.5 156 167Z" fill="#3A2630" fill-opacity=".55"/>
    <path d="M156 167C155.5 186 165 203.6 180 203.6C195 203.6 204.5 186 204 167C201.5 175.5 198 182 192.5 186.5C188.5 185.2 184.5 184.6 180 185C175.5 184.6 171.5 185.2 167.5 186.5C162 182 158.5 175.5 156 167Z" fill="url(#stubble)"/>
    <!-- black cap with the developer's initials -->
    <path d="M152 160C150 122 210 122 208 160Z" fill="url(#crown)"/>
    <path d="M167 136.5C163 143 161.5 150 161.3 157M193 136.5C197 143 198.5 150 198.7 157" fill="none" stroke="#24243A" stroke-width="1.1"/>
    <text x="180" y="148" class="capt" text-anchor="middle">SA</text>
    <path d="M147 158C160 152.5 200 152.5 213 158C213 164.3 206 168.3 180 169.3C154 168.3 147 164.3 147 158Z" fill="url(#brim)"/>
    <path d="M150 163.5C161.5 167.3 198.5 167.3 210 163.5" fill="none" stroke="#2C2C40" stroke-width="1" stroke-linecap="round"/>
        <path d="M180.5 179.5q-2.2 4.6.4 5.6" fill="none" stroke="#9A6448" stroke-width="1.3" stroke-linecap="round"/>
    <path d="M172.5 189.2C176 192.6 184 192.8 187.5 188.6C184 190 176 190.2 172.5 189.2Z" fill="#A86A55"/>
    <path d="M174.5 189.6q6 2.2 11.5-1.2" fill="none" stroke="#120A18" stroke-width="1.6" stroke-linecap="round"/>
    <!-- slim black rectangular shades -->
    <path d="M153.5 172h-1.5M206.5 172h1.5" stroke="#0B0B12" stroke-width="1.6" stroke-linecap="round"/>
    <path d="M177 172.5q3-1.8 6 0" fill="none" stroke="#0B0B12" stroke-width="1.6" stroke-linecap="round"/>
    <rect x="153.5" y="168.5" width="23.5" height="10" rx="1.8" fill="#08080E" stroke="#1E1E2A" stroke-width=".8"/>
    <rect x="183" y="168.5" width="23.5" height="10" rx="1.8" fill="#08080E" stroke="#1E1E2A" stroke-width=".8"/>
    <g clip-path="url(#shades)"><rect x="222" y="164" width="7" height="18" fill="#fff" fill-opacity=".55" transform="skewX(-25)" class="shine"/></g>
    <path d="M148.5 172C144 111 216 111 211.5 172" fill="none" stroke="#0B0822" stroke-width="6" stroke-linecap="round"/>
    <path d="M148.5 172C144 111 216 111 211.5 172" fill="none" stroke="url(#rim)" stroke-width="1.3" stroke-opacity=".85"/>
    <rect x="142" y="162" width="12" height="24" rx="5.5" fill="#0B0822" stroke="{C["purple"]}" stroke-opacity=".8"/>
    <rect x="206" y="162" width="12" height="24" rx="5.5" fill="#0B0822" stroke="{C["cyan"]}" stroke-opacity=".8"/>
    <circle cx="212" cy="174" r="1.9" fill="{C["cyan"]}" class="led"/>
  </g></g>

  <!-- laptop (lid faces the viewer) -->
  <rect x="106" y="206" width="148" height="64" rx="7" fill="url(#lid)" stroke="#3A3380"/>
  <rect x="112" y="207.5" width="136" height="1.2" rx=".6" fill="{C["cyan"]}" fill-opacity=".35"/>
  <circle cx="180" cy="238" r="9" fill="none" stroke="url(#rim)" stroke-width="2" class="led"/>
  <rect x="122" y="214" width="26" height="14" rx="4" fill="{C["pink"]}" fill-opacity=".85" transform="rotate(-8 135 221)"/>
  <text x="135" y="224.5" class="stk" text-anchor="middle" transform="rotate(-8 135 221)" style="fill:#fff">AI</text>
  <g transform="rotate(-4 216 245)">
    <rect x="190" y="238" width="52" height="14" rx="3.5" fill="#0B0822" stroke="{C["cyan"]}" stroke-width=".9"/>
    <text x="216" y="248" class="zin" text-anchor="middle">zinmeir</text>
  </g>
  <g transform="rotate(5 199 221)">
    <rect x="187" y="213" width="24" height="16" rx="2" fill="#006C35" stroke="#F4F5FF" stroke-width="1"/>
    <path d="M192 218.6c1.2-1 2-.2 3 .3 1-1.2 2-.4 3 .1 1-1.1 2-.4 3 .1 1-1 2-.4 3 .1 1-.8 1.6-.4 2.2 0" fill="none" stroke="#fff" stroke-width=".85" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M192.5 224.6h12.5M205 223.6l1.8 1-1.8 1" fill="none" stroke="#fff" stroke-width=".8" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M193 223.5v2.2" stroke="#fff" stroke-width=".8" stroke-linecap="round"/>
  </g>
  <path d="M228 215l7 4v8l-7 4-7-4v-8Z" fill="{C["purple"]}" fill-opacity=".85"/>
  <rect x="120" y="238" width="12" height="12" rx="6" fill="#3DDC97" fill-opacity=".8"/>
  <rect x="112" y="257" width="18" height="11" rx="5.5" fill="#B07A5F"/><rect x="115" y="256" width="15" height="10" rx="5" fill="#C8906C" class="tapL"/>
  <rect x="230" y="257" width="18" height="11" rx="5.5" fill="#B07A5F"/><rect x="230" y="256" width="15" height="10" rx="5" fill="#C8906C" class="tapR"/>
  <path d="M94 270h172l-8 7H102Z" fill="#241D57"/>

  <!-- desk -->
  <rect x="22" y="282" width="316" height="40" fill="#0D0930"/>
  <rect x="16" y="277" width="328" height="6" rx="3" fill="#1C1650"/>
  <rect x="16" y="277" width="328" height="1.4" fill="url(#deskG)"/>
  <!-- mug -->
  <path d="M38 258h18v13a4 4 0 0 1-4 4H42a4 4 0 0 1-4-4Z" fill="#2B2270" stroke="{C["purple"]}" stroke-opacity=".6"/>
  <path d="M56 261.5h2.6a3.4 3.4 0 0 1 0 6.8H56" fill="none" stroke="{C["purple"]}" stroke-opacity=".6" stroke-width="1.5"/>
  <path d="M44 254c-3-4 3-6 0-10" fill="none" stroke="{C["muted"]}" stroke-width="1.3" stroke-linecap="round" class="steam"/>
  <path d="M50 254c-3-4 3-6 0-10" fill="none" stroke="{C["muted"]}" stroke-width="1.3" stroke-linecap="round" class="steam" style="animation-delay:-1.5s"/>
  <!-- rubber debugging duck -->
  <g class="duck">
    <path d="M272 277c-2-9 4-13 12-12 5 .5 9 3 10 7l-1 5Z" fill="#F5C451"/>
    <circle cx="286" cy="261" r="6" fill="#F5C451"/>
    <path d="M291 260.5l5 1.5-5 1.6Z" fill="#FF8A3D"/>
    <circle cx="287.5" cy="259.5" r="1" fill="#1A1235"/>
  </g>
  <!-- plant -->
  <g class="sway"><path d="M316 260c-10-6-12-16-8-24 6 5 9 13 8 24Z" fill="#3DDC97" fill-opacity=".85"/>
    <path d="M318 260c3-10 10-16 18-17-1 8-8 15-18 17Z" fill="#2BB27A"/>
    <path d="M317 260c0-12 3-20 7-26 3 8 1 18-7 26Z" fill="#5FE6AC" fill-opacity=".9"/></g>
  <path d="M305 258h24l-3 19h-18Z" fill="#2B2270" stroke="{C["purple"]}" stroke-opacity=".6"/>
</g>'''


def render(d, login):
    W, M, G, PAD = 1000, 22, 14, 18
    QW, IW = 236, 368
    RW = W - 2 * M - QW - IW - 2 * G
    PH = 316
    RH = (PH - G) / 2
    H = M * 2 + PH
    qx, ix, rx = M, M + QW + G, M + QW + IW + 2 * G
    y0 = M

    def panel(x, y, w, h, n=None, title=None, acc=None):
        out = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" fill="url(#panel)" stroke="#2A2465"/>'
        if title:
            out += (f'<text x="{x + PAD:.1f}" y="{y + 28:.1f}" class="h"><tspan fill="{acc}">{n}</tspan>'
                    f'<tspan fill="{C["dim"]}"> // </tspan>{title}</text>'
                    f'<rect x="{x + PAD:.1f}" y="{y + 38:.1f}" width="{w - 2 * PAD:.1f}" height="1" fill="url(#rule)"/>')
        return out

    # ---- quote panel: quotes cross-fade; the first one is the static fallback
    n_q, slot = len(QUOTES), 6
    qsvg, qkf = [], []
    for k, (q, who) in enumerate(QUOTES):
        lines = wrap(q, 16, "sb", QW - 2 * PAD - 6)
        block = 26 + len(lines) * 23 + 30
        ty = y0 + 52 + (PH - 52 - block) / 2
        text = "".join(f'<text x="{qx + PAD:.1f}" y="{ty + 50 + i * 23:.1f}" class="q">{esc(l)}</text>'
                       for i, l in enumerate(lines))
        a, b = k / n_q * 100, (k + 1) / n_q * 100
        if k == 0:
            qkf.append(f"@keyframes q0{{0%,{b - 4:.1f}%{{opacity:1}}{b:.1f}%,{100 - 4:.1f}%{{opacity:0}}100%{{opacity:1}}}}")
        else:
            qkf.append(f"@keyframes q{k}{{0%,{a:.1f}%{{opacity:0}}{a + 4:.1f}%,{b - 4:.1f}%{{opacity:1}}{b:.1f}%,100%{{opacity:0}}}}")
        qsvg.append(f'''<g class="qr" style="animation-name:q{k};{'' if k == 0 else 'opacity:0'}">
      <text x="{qx + PAD - 2:.1f}" y="{ty + 30:.1f}" class="qm">“</text>
      {text}
      <text x="{qx + PAD:.1f}" y="{ty + 50 + len(lines) * 23 + 8:.1f}" class="qa">— {esc(who)}</text></g>''')

    # ---- languages panel: donut + legend
    langs = [(n, s, c) for n, (s, c) in d["languages"].items() if n not in EXCLUDE]
    langs.sort(key=lambda t: -t[1])
    total = sum(s for _, s, _ in langs) or 1
    top, rest = langs[:TOP_N], sum(s for _, s, _ in langs[TOP_N:])
    items = [(n, s / total, readable(c)) for n, s, c in top] + ([("Other", rest / total, C["dim"])] if rest else [])
    ly = y0
    dcx, dcy, dr = rx + RW - PAD - 46, ly + 38 + (RH - 38) / 2, 38
    donut, legend, acc = [], [], 0.0
    for k, (n, f, c) in enumerate(items):
        seg = max(f * 100 - .8, .3)
        donut.append(f'<circle cx="{dcx:.1f}" cy="{dcy:.1f}" r="{dr}" fill="none" stroke="{c}" stroke-width="13" pathLength="100" '
                     f'stroke-dasharray="{seg:.2f} {100 - seg:.2f}" stroke-dashoffset="{-acc:.2f}" '
                     f'transform="rotate(-90 {dcx:.1f} {dcy:.1f})" class="seg" style="animation-delay:{.3 + k * .12:.2f}s"/>')
        acc += f * 100
        yy = ly + 62 + k * 19
        pct = f"{f * 100:.0f}%" if f >= .005 else "<1%"
        legend.append(f'''<g class="up" style="animation-delay:{.4 + k * .07:.2f}s"><circle cx="{rx + PAD + 4:.1f}" cy="{yy - 4:.1f}" r="4" fill="{c}"/>
      <text x="{rx + PAD + 14:.1f}" y="{yy:.1f}" class="l">{esc(n)}</text>
      <text x="{dcx - dr - 20:.1f}" y="{yy:.1f}" class="m" text-anchor="end">{pct}</text></g>''')

    # ---- activity panel: icon rows
    sy = y0 + RH + G
    rows = [("star", "Stars earned", d["stars"]), ("commit", "Commits (1y)", d["commits"]),
            ("repo", "Repositories", d["repos"]), ("contrib", "Contributed to", d["contributed"])]
    act = []
    for k, (ic, lab, val) in enumerate(rows):
        yy = sy + 64 + k * 23
        act.append(f'''<g class="up" style="animation-delay:{.5 + k * .08:.2f}s">
      <g transform="translate({rx + PAD:.1f} {yy - 12:.1f})" fill="none" stroke="{C["cyan"]}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">{ICONS[ic]}</g>
      <text x="{rx + PAD + 26:.1f}" y="{yy:.1f}" class="lm">{lab}</text>
      <text x="{rx + RW - PAD:.1f}" y="{yy:.1f}" class="v" text-anchor="end">{fmt(val)}</text></g>''')

    code_kf = "".join(
        f"@keyframes c{k}{{0%,{4 + k * 11:.0f}%{{transform:scaleX(0)}}{11 + k * 11:.0f}%,88%{{transform:scaleX(1);opacity:1}}96%,100%{{transform:scaleX(1);opacity:0}}}}"
        for k in range(6))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ttl desc">
<title id="ttl">GitHub stats — {esc(login)}</title>
<desc id="desc">{d["stars"]} stars, {d["commits"]} commits in the last year, {d["repos"]} repositories, contributed to {d["contributed"]} repositories. Top languages: {esc(", ".join(f"{n} {f*100:.0f}%" for n, f, _ in items))}.</desc>
<style>
{ASSETS["css"]}
.q{{font:600 16px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["text"]}}}
.qm{{font:600 46px 'InterW','Inter',Georgia,serif;fill:{C["purple"]}}}
.qa{{font:12px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["pink"]}}}
.l{{font:500 13px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["text"]}}}
.lm{{font:500 13px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["muted"]}}}
.v{{font:600 15px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["text"]};font-variant-numeric:tabular-nums}}
.h{{font:12.5px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["text"]};letter-spacing:.3px}}
.m{{font:11.5px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["dim"]}}}
.mtag{{font:12px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["cyan"]}}}
.rise{{animation:rise .8s cubic-bezier(.2,.7,.2,1) both}}
@keyframes rise{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
.up{{animation:up .7s ease-out both}}
@keyframes up{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.seg{{animation:seg 1s cubic-bezier(.2,.7,.2,1) both}}
@keyframes seg{{from{{stroke-dasharray:0 100}}}}
.qr{{animation-duration:{n_q * slot}s;animation-iteration-count:infinite;animation-timing-function:linear}}
{"".join(qkf)}
.cl{{transform-box:fill-box;transform-origin:0 50%;animation-duration:6s;animation-iteration-count:infinite}}
{code_kf}
.bar{{transform-box:fill-box;transform-origin:50% 100%;animation:bar 2s ease-in-out infinite alternate}}
@keyframes bar{{from{{transform:scaleY(.45)}}to{{transform:none}}}}
.bob{{animation:bob 5s ease-in-out infinite}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-6px)}}}}
.blink{{transform-box:fill-box;transform-origin:50% 50%;animation:blink 4.5s infinite}}
@keyframes blink{{0%,92%,100%{{transform:none}}95%{{transform:scaleY(.1)}}}}
.tapL{{animation:tap .32s ease-in-out infinite alternate}}
.tapR{{animation:tap .32s ease-in-out infinite alternate-reverse}}
@keyframes tap{{from{{transform:translateY(0)}}to{{transform:translateY(-2.5px)}}}}
.led{{animation:led 2.4s ease-in-out infinite}}
@keyframes led{{0%,100%{{opacity:.45}}50%{{opacity:1}}}}
.glow{{animation:glow 5s ease-in-out infinite}}
@keyframes glow{{0%,100%{{opacity:.6}}50%{{opacity:1}}}}
.steam{{animation:steam 3s ease-in-out infinite}}
@keyframes steam{{0%{{transform:translateY(4px);opacity:0}}40%{{opacity:.55}}100%{{transform:translateY(-10px);opacity:0}}}}
.sway{{transform-box:fill-box;transform-origin:50% 100%;animation:sway 4s ease-in-out infinite}}
@keyframes sway{{0%,100%{{transform:rotate(-3deg)}}50%{{transform:rotate(3deg)}}}}
.stk{{font:8.5px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["dim"]}}}
.flow{{animation:flow 1.6s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-18}}}}
.fire{{animation:fire 1.8s ease-in-out infinite}}
@keyframes fire{{0%,100%{{opacity:.25}}20%{{opacity:1}}}}
.prog{{transform-box:fill-box;transform-origin:0 50%;animation:prog 4.5s cubic-bezier(.4,0,.2,1) infinite}}
@keyframes prog{{0%{{transform:scaleX(.04)}}85%{{transform:scaleX(1);opacity:1}}100%{{transform:scaleX(1);opacity:0}}}}
.nod{{transform-box:fill-box;transform-origin:50% 100%;animation:nod 6s ease-in-out infinite}}
@keyframes nod{{0%,100%{{transform:rotate(0)}}30%{{transform:rotate(-2deg)}}60%{{transform:rotate(1.5deg)}}}}
.look{{animation:look 7s ease-in-out infinite}}
@keyframes look{{0%,40%,100%{{transform:translateX(0)}}48%,62%{{transform:translateX(-2px)}}70%,82%{{transform:translateX(2px)}}}}
.flick{{animation:flick 3.5s ease-in-out infinite}}
@keyframes flick{{0%,100%{{opacity:.75}}50%{{opacity:1}}}}
.duck{{transform-box:fill-box;transform-origin:50% 100%;animation:duck 3.2s ease-in-out infinite}}
@keyframes duck{{0%,100%{{transform:rotate(0)}}50%{{transform:rotate(-6deg)}}}}
.zin{{font:9px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["cyan"]};letter-spacing:.4px}}
.capt{{font:600 12px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:#F4F5FF;stroke:#F4F5FF;stroke-width:.9px;stroke-linejoin:round;paint-order:stroke;letter-spacing:.9px}}
.shine{{animation:shine 4.5s ease-in-out infinite}}
@keyframes shine{{0%,62%{{transform:skewX(-25deg) translateX(0)}}82%,100%{{transform:skewX(-25deg) translateX(84px)}}}}
.tw{{animation:tw 3.6s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.2}}50%{{opacity:.9}}}}
.pt{{animation:pt 5s linear infinite}}
@keyframes pt{{0%{{transform:translateY(0);opacity:0}}20%{{opacity:.9}}100%{{transform:translateY(-60px);opacity:0}}}}
</style>
<defs>
  <linearGradient id="bgG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C["bg0"]}"/><stop offset="1" stop-color="{C["bg1"]}"/></linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}" stop-opacity=".55"/><stop offset=".5" stop-color="{C["purple"]}" stop-opacity=".15"/><stop offset="1" stop-color="{C["cyan"]}" stop-opacity=".55"/></linearGradient>
  <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#15104A" stop-opacity=".75"/><stop offset="1" stop-color="#0B0828" stop-opacity=".75"/></linearGradient>
  <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}" stop-opacity=".5"/><stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></linearGradient>
  <linearGradient id="scr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#16114D"/><stop offset="1" stop-color="#0A0726"/></linearGradient>
  <linearGradient id="barG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{C["cyan"]}"/><stop offset="1" stop-color="{C["purple"]}"/></linearGradient>
  <linearGradient id="rim" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}"/><stop offset="1" stop-color="{C["cyan"]}"/></linearGradient>
  <linearGradient id="hoodie" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E6E8F2"/><stop offset=".55" stop-color="#C3C7DA"/><stop offset="1" stop-color="#8F94B2"/></linearGradient>
  <linearGradient id="deskG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}" stop-opacity="0"/><stop offset=".4" stop-color="{C["purple"]}" stop-opacity=".9"/><stop offset=".8" stop-color="{C["cyan"]}" stop-opacity=".9"/><stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></linearGradient>
  <radialGradient id="halo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{C["purple"]}" stop-opacity=".35"/><stop offset=".6" stop-color="#3B0F6F" stop-opacity=".12"/><stop offset="1" stop-color="{C["bg0"]}" stop-opacity="0"/></radialGradient>
  <linearGradient id="lid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#211A5A"/><stop offset="1" stop-color="#15104A"/></linearGradient>
  <radialGradient id="faceGlow" cx=".5" cy=".7" r=".6"><stop offset="0" stop-color="{C["cyan"]}" stop-opacity=".14"/><stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></radialGradient>
  <clipPath id="shades"><rect x="153.5" y="168.5" width="23.5" height="10" rx="1.8"/><rect x="183" y="168.5" width="23.5" height="10" rx="1.8"/></clipPath>
  <linearGradient id="crown" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#16162A"/><stop offset=".55" stop-color="#0A0A10"/><stop offset="1" stop-color="#101826"/></linearGradient>
  <linearGradient id="brim" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1C1C28"/><stop offset="1" stop-color="#0C0C12"/></linearGradient>
  <pattern id="stubble" width="2.2" height="2.2" patternUnits="userSpaceOnUse"><circle cx=".6" cy=".6" r=".42" fill="#1A1020" fill-opacity=".8"/><circle cx="1.7" cy="1.6" r=".36" fill="#1A1020" fill-opacity=".6"/></pattern>
  <linearGradient id="beardG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#33241D"/><stop offset=".6" stop-color="#241914"/><stop offset="1" stop-color="#1A1210"/></linearGradient>
  <filter id="beardF" x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="2" seed="4" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="2.6" xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feGaussianBlur in="d" stdDeviation=".35"/>
  </filter>
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="1.8 .7" numOctaves="2" seed="9" result="t"/>
    <feColorMatrix in="t" type="matrix" values="0 0 0 0 .55  0 0 0 0 .42  0 0 0 0 .36  0 0 0 2.2 -1.15"/>
  </filter>
  <clipPath id="beardClip"><path d="M155.2 164A25 32.5 0 1 0 204.8 164L202.6 164.5C203 171 202 176.5 199 180.5C196 183.6 191 184 187 184.4C184.5 184.1 182 184.3 180 184.7C178 184.3 175.5 184.1 173 184.4C169 184 164 183.6 161 180.5C158 176.5 157 171 157.4 164.5Z"/></clipPath>
  <filter id="soft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation=".9"/></filter>
  <filter id="stubF" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="2.4" numOctaves="1" seed="12" result="t"/>
    <feColorMatrix in="t" type="matrix" values="0 0 0 0 .12  0 0 0 0 .08  0 0 0 0 .09  0 0 0 3.2 -1.75"/>
  </filter>
  <clipPath id="illus"><rect x="{ix}" y="{y0}" width="{IW}" height="{PH}" rx="14"/></clipPath>
</defs>
<rect width="{W}" height="{H}" rx="20" fill="url(#bgG)"/>

<g class="rise" style="animation-delay:.05s">{panel(qx, y0, QW, PH, "01", "fortune", C["pink"])}
  {"".join(qsvg)}
</g>
<g class="rise" style="animation-delay:.15s">{panel(ix, y0, IW, PH)}
  <g clip-path="url(#illus)">{illustration(ix + (IW - 360) / 2, y0 + PH - 312 + 2)}</g>
</g>
<g class="rise" style="animation-delay:.25s">{panel(rx, ly, RW, RH, "02", "languages", C["purple"])}
  <circle cx="{dcx:.1f}" cy="{dcy:.1f}" r="{dr}" fill="none" stroke="#1A1545" stroke-width="13"/>
  {"".join(donut)}
  {"".join(legend)}
</g>
<g class="rise" style="animation-delay:.35s">{panel(rx, sy, RW, RH, "03", "activity", C["cyan"])}
  {"".join(act)}
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.5" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>'''


def main():
    login = os.environ.get("GH_LOGIN", "zinmeir")
    if "--sample" in sys.argv:
        data = SAMPLE
    else:
        token = os.environ.get("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN is not set")
        data = fetch(login, token)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(data, login))
    print(f"wrote {OUT}: {data['commits']} commits, {data['repos']} repos, {data['stars']} stars")


if __name__ == "__main__":
    main()
