#!/usr/bin/env python3
"""Render assets/btn-*.svg — animated link buttons in the profile's card style.

Standard library only; reuses the fonts in stats_assets.json:
    python3 scripts/buttons_card.py
Each button is its own image so it can be wrapped in its own link in README.md.
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets"
ASSETS = json.loads((HERE / "stats_assets.json").read_text())
# buttons only need the semibold sans + mono faces
CSS = "".join(f for f in re.findall(r"@font-face\{.*?\}", ASSETS["css"]) if "font-weight:500" not in f)

C = dict(text="#E8EAFF", purple="#8B5CF6", cyan="#00E5FF", pink="#FF2E97")

# generic line icons, drawn in a 20x20 box centred on 0,0
ICONS = {
    "connect": '<circle cx="-2" cy="-4" r="3.6"/><path d="M-9 7c0-4 3-6.5 7-6.5s7 2.5 7 6.5"/><path d="M6.5 -5v6M3.5 -2h6"/>',
    "mail": '<rect x="-8" y="-6" width="16" height="12" rx="2.2"/><path d="M-7.5 -5l7.5 6 7.5-6"/>',
    "rocket": ('<path d="M0 -9c4 3 5 8 3 13H-3c-2-5-1-10 3-13z"/><circle cx="0" cy="-2.5" r="1.8"/>'
               '<path d="M-3 4l-3.5 3 .5-5M3 4l3.5 3-.5-5"/><path d="M-1.5 7.5L0 10.5 1.5 7.5" class="fl"/>'),
}

BUTTONS = [
    dict(file="btn-linkedin.svg", label="LinkedIn", sub="let's connect", icon="connect", acc=C["cyan"], acc2=C["purple"], delay=0),
    dict(file="btn-email.svg", label="Email", sub="say hello", icon="mail", acc=C["purple"], acc2=C["pink"], delay=.15),
    dict(file="btn-portfolio.svg", label="Portfolio", sub="view my work", icon="rocket", acc=C["pink"], acc2=C["cyan"], delay=.3),
]

W, H = 214, 62                   # image size; the visible pill is inset so buttons get gaps between them
BX, BY, BW, BH = 7, 6, 200, 50


def width(text, size, font):
    w = ASSETS["widths"][font]
    return sum(w.get(ch, 0.6) for ch in text) * size


def render(b):
    acc, acc2, d = b["acc"], b["acc2"], b["delay"]
    ax = BX + BW - 26                                   # arrow position
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{b["label"]} — {b["sub"]}">
<title>{b["label"]} — {b["sub"]}</title>
<style>
{CSS}
.lb{{font:600 15px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["text"]}}}
.sb{{font:10.5px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{acc};letter-spacing:.3px}}
.in{{animation:in .7s cubic-bezier(.2,.7,.2,1) {d}s both}}
@keyframes in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.edge{{animation:edge 3.2s ease-in-out {d}s infinite}}
@keyframes edge{{0%,100%{{stroke-opacity:.45}}50%{{stroke-opacity:1}}}}
.shine{{animation:shine 5s ease-in-out {1 + d * 4}s infinite}}
@keyframes shine{{0%{{transform:translateX(-80px) skewX(-20deg)}}25%,100%{{transform:translateX({BW + 80}px) skewX(-20deg)}}}}
.ic{{transform-box:fill-box;transform-origin:50% 50%;animation:ic 3s ease-in-out {d}s infinite}}
@keyframes ic{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-1.5px)}}}}
.ring{{transform-box:fill-box;transform-origin:50% 50%;animation:ring 2.6s ease-out {d}s infinite}}
@keyframes ring{{from{{transform:scale(1);opacity:.6}}to{{transform:scale(1.55);opacity:0}}}}
.arr{{animation:arr 1.6s ease-in-out infinite}}
@keyframes arr{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX(3px)}}}}
.fl{{animation:fl .25s ease-in-out infinite alternate}}
@keyframes fl{{to{{opacity:.3}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#15104A"/><stop offset="1" stop-color="#07041A"/></linearGradient>
  <linearGradient id="st" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{acc}"/><stop offset="1" stop-color="{acc2}"/></linearGradient>
  <linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".12"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <radialGradient id="gl" cx=".12" cy=".5" r=".6"><stop offset="0" stop-color="{acc}" stop-opacity=".22"/><stop offset="1" stop-color="{acc}" stop-opacity="0"/></radialGradient>
  <clipPath id="pill"><rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="{BH / 2}"/></clipPath>
</defs>
<g class="in">
  <rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="{BH / 2}" fill="url(#bg)"/>
  <g clip-path="url(#pill)">
    <rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" fill="url(#gl)"/>
    <rect x="{BX}" y="{BY}" width="60" height="{BH}" fill="url(#sh)" class="shine"/>
  </g>
  <rect x="{BX + .75}" y="{BY + .75}" width="{BW - 1.5}" height="{BH - 1.5}" rx="{(BH - 1.5) / 2}" fill="none" stroke="url(#st)" stroke-width="1.5" class="edge"/>

  <circle cx="{BX + 27}" cy="{BY + BH / 2}" r="15" fill="{acc}" fill-opacity=".12" stroke="{acc}" stroke-opacity=".5"/>
  <circle cx="{BX + 27}" cy="{BY + BH / 2}" r="15" fill="none" stroke="{acc}" class="ring"/>
  <g transform="translate({BX + 27} {BY + BH / 2})"><g class="ic" fill="none" stroke="{acc}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[b["icon"]]}</g></g>

  <text x="{BX + 52}" y="{BY + 23}" class="lb">{b["label"]}</text>
  <text x="{BX + 52}" y="{BY + 38}" class="sb">{b["sub"]}</text>

  <g transform="translate({ax} {BY + BH / 2})"><g class="arr" fill="none" stroke="{C["text"]}" stroke-opacity=".7" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M-5 0H5M1 -4L5 0L1 4"/></g></g>
</g>
</svg>'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for b in BUTTONS:
        (OUT / b["file"]).write_text(render(b))
        print("wrote", OUT / b["file"])


if __name__ == "__main__":
    main()
