#!/usr/bin/env python3
"""Render assets/publications.svg — animated research-publications card in the profile's style.

Standard library only; reuses the fonts and width tables in stats_assets.json:
    python3 scripts/publications_card.py
To add a paper, append an entry to PAPERS and re-run. Text wraps automatically.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "publications.svg"
ASSETS = json.loads((HERE / "stats_assets.json").read_text())

C = dict(bg0="#07041A", bg1="#0F0A2E", text="#E8EAFF", muted="#9AA3C7", dim="#5B6390",
         purple="#8B5CF6", cyan="#00E5FF", pink="#FF2E97")
LIGHT = {C["purple"]: "#C4B5FD", C["cyan"]: "#8AF3FF", C["pink"]: "#FF9BCB"}

PAPERS = [
    dict(label="quantum computing", icon="atom", acc=C["purple"], sec=C["cyan"],
         title="Performance Analysis of Grover's Algorithm under Depolarizing Noise in NISQ Devices",
         summary="Investigating quantum algorithm robustness under realistic noise conditions in near-term quantum hardware.",
         tags=["Quantum Algorithms", "Grover's Search", "Depolarizing Noise", "NISQ"]),
    dict(label="privacy-preserving ml", icon="fed", acc=C["pink"], sec=C["purple"],
         title="Federated Learning for Mental Health Applications: Adaptive and Privacy-Preserving Early Detection",
         summary="Privacy-first federated architecture for early mental health condition detection, no sensitive data ever centralised.",
         tags=["Federated Learning", "Privacy-Preserving", "Early Detection", "Mental Health"]),
    dict(label="agentic ai · cloud", icon="cloud", acc=C["cyan"], sec=C["purple"],
         title="CloudAIde: An Agentic Framework for Autonomous Cloud Infrastructure Remediation Using Large Language Models",
         summary="End-to-end LLM agent framework for detecting, diagnosing, and self-healing cloud infrastructure incidents autonomously.",
         tags=["LLM Agents", "AIOps", "Self-Healing", "Cloud Infrastructure"]),
]

W, M, G = 1000, 22, 14          # card width, outer margin, gap between panels
PW = W - 2 * M                  # panel width
PAD, T = 24, 60                 # panel padding, icon tile size
TX = PAD + T + 22               # text column offset inside a panel
TW = PW - TX - 40               # text column width
TS, SS, CS = 17, 14.5, 11.5     # title / summary / chip font sizes


def width(text, size, font):
    w = ASSETS["widths"][font]
    return sum(w.get(ch, 0.6) for ch in text) * size


def wrap(text, size, font, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and width(trial, size, font) > maxw:
            lines.append(cur); cur = word
        else:
            cur = trial
    return lines + [cur]


def balanced(text, size, font, maxw):
    """Wrap into the fewest lines, then even out their lengths so no line ends up as a lone orphan."""
    n = len(wrap(text, size, font, maxw))
    lo, hi = maxw / n, maxw
    while hi - lo > 1:
        mid = (lo + hi) / 2
        if len(wrap(text, size, font, mid)) > n:
            lo = mid
        else:
            hi = mid
    return wrap(text, size, font, hi)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- icons (drawn in a 60x60 tile)
def icon(kind, acc, sec, k):
    if kind == "atom":
        orbit = "M11,30 a19,7 0 1,0 38,0 a19,7 0 1,0 -38,0"
        rings = "".join(f'<ellipse cx="30" cy="30" rx="19" ry="7" transform="rotate({a} 30 30)" stroke="{c}"/>'
                        for a, c in ((0, acc), (60, sec), (120, acc)))
        electrons = "".join(
            f'<g transform="rotate({a} 30 30)"><circle r="2.3" fill="{LIGHT[c]}" filter="url(#glow)">'
            f'<animateMotion dur="{d}s" begin="-{b}s" repeatCount="indefinite" path="{orbit}"/></circle></g>'
            for a, c, d, b in ((0, sec, 2.4, 0), (60, acc, 3.1, 1.2), (120, sec, 2.7, .6)))
        return (f'<g fill="none" stroke-width="1.4" stroke-opacity=".75">{rings}</g>'
                f'<circle cx="30" cy="30" r="4.4" fill="url(#ic{k})" filter="url(#glow)" class="beat"/>{electrons}')
    if kind == "fed":
        pts = [(15, 15), (45, 15), (15, 45), (45, 45)]
        links = "".join(f'<path d="M{x} {y}L30 30" class="flow" style="animation-delay:-{i * .2:.1f}s"/>' for i, (x, y) in enumerate(pts))
        nodes = "".join(f'<circle cx="{x}" cy="{y}" r="4.2"/><circle cx="{x}" cy="{y}" r="1.8" fill="{LIGHT[acc]}" stroke="none" '
                        f'class="fire" style="animation-delay:{i * .35:.2f}s"/>' for i, (x, y) in enumerate(pts))
        return (f'<g stroke="{LIGHT[acc]}" stroke-width="1.4" stroke-opacity=".8" fill="none">{links}</g>'
                f'<g fill="{C["bg0"]}" stroke="{acc}" stroke-width="1.6">{nodes}</g>'
                f'<circle cx="30" cy="30" r="5" fill="none" stroke="{sec}" stroke-width="1.3" class="ring"/>'
                f'<circle cx="30" cy="30" r="5.4" fill="url(#ic{k})" filter="url(#glow)"/>')
    # cloud with a self-healing heartbeat
    return (f'<g class="bob2"><g transform="translate(-0.5 1.5) scale(1.25)">'
            f'<path d="M15 36h19a7 7 0 0 0 1-13.9a10 10 0 0 0-19.3-2.4A8 8 0 0 0 15 36z" fill="{acc}" fill-opacity=".1" '
            f'stroke="url(#ic{k})" stroke-width="1.4" stroke-linejoin="round"/>'
            f'<polyline points="12.5,28.5 18,28.5 20.5,24 23.5,32.5 26.5,25.5 28.5,28.5 35.5,28.5" fill="none" stroke="{LIGHT[acc]}" '
            f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" pathLength="100" class="pulse" filter="url(#glow)"/>'
            f'</g></g>')


# ---------------------------------------------------------------- layout + render
def panel(p, k, y):
    acc, sec = p["acc"], p["sec"]
    x = M
    tl = balanced(p["title"], TS, "sb", TW)
    sl = balanced(p["summary"], SS, "md", TW)
    ty0 = y + 66
    sy0 = ty0 + (len(tl) - 1) * 24 + 28
    cy = sy0 + (len(sl) - 1) * 21 + 18
    h = cy + 24 + 24 - y
    d0 = .1 + k * .16                                     # entrance delay for this panel

    titles = "".join(f'<text x="{x + TX}" y="{ty0 + i * 24}" class="t">{esc(l)}</text>' for i, l in enumerate(tl))
    sums = "".join(f'<text x="{x + TX}" y="{sy0 + i * 21}" class="s">{esc(l)}</text>' for i, l in enumerate(sl))

    chips, cx = [], x + TX
    for j, tag in enumerate(p["tags"]):
        c = acc if j < 2 else sec
        cw = width(tag, CS, "mono") + 22
        chips.append(f'<g class="pop" style="animation-delay:{d0 + .55 + j * .08:.2f}s">'
                     f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="24" rx="12" fill="{c}" fill-opacity=".1" stroke="{c}" stroke-opacity=".4"/>'
                     f'<text x="{cx + cw / 2:.1f}" y="{cy + 16}" class="c" text-anchor="middle" fill="{LIGHT[c]}">{esc(tag)}</text></g>')
        cx += cw + 8

    svg = f'''
<g class="rise" style="animation-delay:{d0:.2f}s">
  <defs>
    <clipPath id="pc{k}"><rect x="{x}" y="{y}" width="{PW}" height="{h}" rx="14"/></clipPath>
    <linearGradient id="ic{k}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{acc}"/><stop offset="1" stop-color="{sec}"/></linearGradient>
    <linearGradient id="bar{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{acc}"/><stop offset="1" stop-color="{sec}"/></linearGradient>
    <radialGradient id="hl{k}" cx="0" cy="0" r="1"><stop offset="0" stop-color="{acc}" stop-opacity=".16"/><stop offset="1" stop-color="{acc}" stop-opacity="0"/></radialGradient>
  </defs>
  <rect x="{x}" y="{y}" width="{PW}" height="{h}" rx="14" fill="url(#panel)" stroke="#2A2465"/>
  <g clip-path="url(#pc{k})">
    <circle cx="{x + 40}" cy="{y + 40}" r="230" fill="url(#hl{k})"/>
    <text x="{x + PW - 24}" y="{y + h - 16}" class="n" text-anchor="end" fill="{acc}">0{k + 1}</text>
    <rect x="{x}" y="{y}" width="110" height="{h}" fill="url(#shineG)" class="shine" style="animation-delay:{2.6 + k * 1.1:.1f}s"/>
  </g>
  <rect x="{x + .5}" y="{y + .5}" width="{PW - 1}" height="{h - 1}" rx="13.5" fill="none" stroke="url(#ic{k})" class="edge" style="animation-delay:{k * 1.5:.1f}s"/>
  <rect x="{x}" y="{y + 22}" width="3" height="{h - 44}" rx="1.5" fill="url(#bar{k})" class="grow" style="animation-delay:{d0 + .25:.2f}s"/>

  <g transform="translate({x + PAD} {y + 24})">
    <rect width="{T}" height="{T}" rx="15" fill="{acc}" fill-opacity=".08" stroke="url(#ic{k})" stroke-opacity=".55" class="tile" style="animation-delay:{k * .8:.1f}s"/>
    {icon(p["icon"], acc, sec, k)}
  </g>

  <g class="up" style="animation-delay:{d0 + .15:.2f}s">
    <text x="{x + TX}" y="{y + 36}" class="h"><tspan fill="{acc}">0{k + 1}</tspan><tspan fill="{C["dim"]}"> // </tspan>{esc(p["label"])}</text>
  </g>
  <g class="up" style="animation-delay:{d0 + .25:.2f}s">{titles}</g>
  <g class="up" style="animation-delay:{d0 + .38:.2f}s">{sums}</g>
  {"".join(chips)}
</g>'''
    return svg, h


def render():
    body, y = [], M
    for k, p in enumerate(PAPERS):
        s, h = panel(p, k, y)
        body.append(s)
        y += h + G
    H = y - G + M

    stars = "".join(
        f'<circle cx="{sx}" cy="{sy * H / 100:.1f}" r="{r}" fill="{C["text"]}" class="tw" style="animation-delay:-{i * .7:.1f}s"/>'
        for i, (sx, sy, r) in enumerate([(12, 6, .9), (990, 12, .8), (6, 48, .7), (994, 55, .9), (11, 93, .8), (988, 90, .7),
                                         (500, 2, .7), (760, 98.6, .8), (240, 98.8, .7)]))

    desc = " ".join(f"{i + 1}. {p['title']} — {p['summary']}" for i, p in enumerate(PAPERS))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ttl desc">
<title id="ttl">Research publications</title>
<desc id="desc">{esc(desc)}</desc>
<style>
{ASSETS["css"]}
.t{{font:600 {TS}px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["text"]}}}
.s{{font:500 {SS}px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["muted"]}}}
.h{{font:12.5px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["muted"]};letter-spacing:.3px}}
.c{{font:{CS}px 'MonoW','JetBrains Mono',Consolas,monospace}}
.n{{font:600 64px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill-opacity:.07}}
.rise{{animation:rise .8s cubic-bezier(.2,.7,.2,1) both}}
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
.up{{animation:up .7s ease-out both}}
@keyframes up{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.pop{{transform-box:fill-box;transform-origin:50% 50%;animation:pop .5s cubic-bezier(.2,.8,.2,1.2) both}}
@keyframes pop{{from{{opacity:0;transform:scale(.7)}}to{{opacity:1;transform:none}}}}
.grow{{transform-box:fill-box;transform-origin:50% 0;animation:grow .9s cubic-bezier(.2,.7,.2,1) both}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:none}}}}
.edge{{stroke-opacity:.2;animation:edge 4.5s ease-in-out infinite}}
@keyframes edge{{0%,100%{{stroke-opacity:.15}}50%{{stroke-opacity:.6}}}}
.shine{{transform-box:fill-box;transform-origin:50% 50%;transform:translateX(-160px) skewX(-20deg);animation:shine 9s ease-in-out infinite}}
@keyframes shine{{0%{{transform:translateX(-160px) skewX(-20deg)}}22%,100%{{transform:translateX({PW + 160}px) skewX(-20deg)}}}}
.tile{{animation:tile 3.6s ease-in-out infinite}}
@keyframes tile{{0%,100%{{fill-opacity:.06}}50%{{fill-opacity:.14}}}}
.flow{{stroke-dasharray:2 3.5;animation:flow 1s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-11}}}}
.fire{{animation:fire 1.8s ease-in-out infinite}}
@keyframes fire{{0%,100%{{opacity:.25}}20%{{opacity:1}}}}
.ring{{transform-box:fill-box;transform-origin:50% 50%;animation:ring 2.4s ease-out infinite}}
@keyframes ring{{from{{transform:scale(.6);opacity:.9}}to{{transform:scale(3.1);opacity:0}}}}
.beat{{transform-box:fill-box;transform-origin:50% 50%;animation:beat 2.4s ease-in-out infinite}}
@keyframes beat{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.25)}}}}
.pulse{{stroke-dasharray:100;animation:pulse 2.8s ease-in-out infinite}}
@keyframes pulse{{0%{{stroke-dashoffset:100}}45%,70%{{stroke-dashoffset:0}}100%{{stroke-dashoffset:-100}}}}
.bob2{{animation:bob2 4s ease-in-out infinite}}
@keyframes bob2{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-2.5px)}}}}
.tw{{animation:tw 3.6s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:.85}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
  <linearGradient id="bgG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C["bg0"]}"/><stop offset="1" stop-color="{C["bg1"]}"/></linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}" stop-opacity=".55"/><stop offset=".5" stop-color="{C["purple"]}" stop-opacity=".15"/><stop offset="1" stop-color="{C["cyan"]}" stop-opacity=".55"/></linearGradient>
  <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#15104A" stop-opacity=".75"/><stop offset="1" stop-color="#0B0828" stop-opacity=".75"/></linearGradient>
  <linearGradient id="shineG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".06"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="1.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="{W}" height="{H}" rx="20" fill="url(#bgG)"/>
{stars}
{"".join(body)}
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.5" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>'''


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render())
    print(f"wrote {OUT}: {len(PAPERS)} papers")


if __name__ == "__main__":
    main()
