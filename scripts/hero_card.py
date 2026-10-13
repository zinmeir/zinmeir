#!/usr/bin/env python3
"""Render assets/hero.svg — animated profile header (starfield, orbiting planet, name, typed taglines).

Standard library only; reuses the fonts and width tables in stats_assets.json:
    python3 scripts/hero_card.py
Edit NAME / ROLES / TAGLINES below and re-run.
"""
import json, random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "hero.svg"
ASSETS = json.loads((HERE / "stats_assets.json").read_text())

NAME = "Muhammad Shaheer Akhtar"
ROLES = ["Machine Learning Engineer", "Full-Stack Developer", "Cybersecurity Specialist"]
TAGLINES = [
    "AI Engineer & Cybersecurity Specialist",
    "RAG Pipelines | LLMs | Cloud Systems",
    "Published Researcher in AI & Quantum Computing",
    "Building Production-Grade AI from Pakistan",
]

C = dict(bg0="#030014", bg1="#0F0A2E", text="#E8EAFF", muted="#9AA3C7", dim="#5B6390",
         purple="#8B5CF6", cyan="#00E5FF", pink="#FF2E97", green="#3DDC97")
W, H = 1000, 300
X0 = 56                                   # left text column


def width(text, size, font):
    w = ASSETS["widths"][font]
    return sum(w.get(ch, 0.6) for ch in text) * size


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- typewriter (SMIL, works inside <img>)
TS = 15                                   # tagline font size (mono)
CW = ASSETS["widths"]["mono"]["a"] * TS   # one monospace character
TYPE, HOLD, DEL, GAP = .055, 2.4, .022, .35
SLOT = [len(t) * TYPE + HOLD + len(t) * DEL + GAP for t in TAGLINES]
CYCLE = sum(SLOT)


def timeline(i):
    """[(t, chars)] for tagline i within one cycle."""
    s, n = sum(SLOT[:i]), len(TAGLINES[i])
    ev = [(s + k * TYPE, k) for k in range(1, n + 1)]
    t_del = s + n * TYPE + HOLD
    ev += [(t_del + (n - k) * DEL, k) for k in range(n - 1, -1, -1)]
    return ev


def smil(attr, events, f):
    """Discrete SMIL animation from absolute (t, value) events, value 0 before the first event."""
    ev = [(0.0, f(0))] + [(t, f(v)) for t, v in events if 0 < t < CYCLE]
    kt = ";".join(f"{t / CYCLE:.5f}" for t, _ in ev)
    vals = ";".join(f"{v:.1f}" for _, v in ev)
    return (f'<animate attributeName="{attr}" dur="{CYCLE:.2f}s" repeatCount="indefinite" begin="1.2s" '
            f'calcMode="discrete" keyTimes="{kt}" values="{vals}"/>')


def typewriter(tx, ty):
    clips, lines, all_ev = [], [], []
    for i, line in enumerate(TAGLINES):
        ev = timeline(i)
        all_ev += ev
        clips.append(f'<clipPath id="tc{i}"><rect x="{tx}" y="{ty - 16}" width="0" height="22">'
                     f'{smil("width", ev, lambda k: k * CW)}</rect></clipPath>')
        lines.append(f'<text x="{tx}" y="{ty}" class="ty" clip-path="url(#tc{i})">{esc(line)}</text>')
    all_ev.sort()
    caret = (f'<rect x="{tx}" y="{ty - 13}" width="8" height="16" rx="1" fill="{C["cyan"]}" class="caret">'
             f'{smil("x", all_ev, lambda k: tx + k * CW + 2)}</rect>')
    return "".join(clips), "".join(lines) + caret


# ---------------------------------------------------------------- scenery
def stars():
    rnd = random.Random(42)
    out = []
    for i in range(70):
        x, y = rnd.uniform(6, W - 6), rnd.uniform(6, H - 6)
        r = rnd.choice([.5, .6, .7, .8, 1, 1.2])
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" class="tw" '
                   f'style="animation-delay:-{rnd.uniform(0, 4):.1f}s;animation-duration:{rnd.uniform(2.6, 5.5):.1f}s"/>')
    return "".join(out)


# little rocket pointing along +x (animateMotion rotate="auto" keeps it nose-first)
ROCKET = '''<g transform="scale(.95)">
  <g class="flame"><path d="M-8 -3 L-21 0 L-8 3Z" fill="url(#flameG)"/><path d="M-8 -1.6 L-14 0 L-8 1.6Z" fill="#FFE2A8"/></g>
  <path d="M-4 -4 L-11 -9 L-9.5 -3.2Z M-4 4 L-11 9 L-9.5 3.2Z" fill="#8B5CF6"/>
  <path d="M12 0C8 -5.4 -3 -6 -8.5 -4.2V4.2C-3 6 8 5.4 12 0Z" fill="#E8EAFF"/>
  <path d="M12 0C10 -3.2 7 -4.9 4.5 -5.2V5.2C7 4.9 10 3.2 12 0Z" fill="#FF2E97"/>
  <circle cx="0.5" cy="0" r="2.2" fill="#00E5FF" stroke="#1B0B45" stroke-width=".9"/>
</g>'''

ALIEN = '''<g fill="#3DDC97" stroke="#3DDC97" stroke-linecap="round">
  <path d="M-2 0V-3M2 0V-3" stroke-width="1.6"/>
  <ellipse cx="0" cy="-6" rx="3.6" ry="4.6" stroke="none"/>
  <path d="M-3 -7.5L-6.5 -4" stroke-width="1.5"/>
  <path d="M3 -7.5L7.5 -11.5" stroke-width="1.5" class="wave"/>
  <circle cx="0" cy="-14" r="5" stroke="none"/>
  <path d="M-2 -18.2L-4.2 -22.5M2 -18.2L4.2 -22.5" stroke-width="1" fill="none"/>
  <circle cx="-4.2" cy="-22.5" r="1.1" stroke="none" class="dot"/><circle cx="4.2" cy="-22.5" r="1.1" stroke="none" class="dot"/>
  <ellipse cx="-2.1" cy="-14.3" rx="1.5" ry="2.1" fill="#07041A" stroke="none" transform="rotate(-18 -2.1 -14.3)"/>
  <ellipse cx="2.1" cy="-14.3" rx="1.5" ry="2.1" fill="#07041A" stroke="none" transform="rotate(18 2.1 -14.3)"/>
</g>'''


def extras():
    """Mars (with a waving alien), a UFO with its pilot, two small planets and a couple of asteroids."""
    mx, my, mr = 722, 62, 26
    craters = "".join(f'<circle cx="{mx + dx}" cy="{my + dy}" r="{cr}" fill="#7A2414" opacity=".55"/>'
                      f'<circle cx="{mx + dx - .6}" cy="{my + dy - .6}" r="{cr}" fill="none" stroke="#F7A07A" stroke-opacity=".35" stroke-width=".8"/>'
                      for dx, dy, cr in ((-12, -6, 4), (6, 4, 5.5), (-3, 13, 3), (16, -9, 2.6), (-30, 2, 4.5), (34, 8, 4), (26, -12, 3)))
    lights = "".join(f'<circle cx="{lx}" cy="2" r="1.6" fill="{col}" class="lamp" style="animation-delay:{i * .25:.2f}s"/>'
                     for i, (lx, col) in enumerate(((-15, C["pink"]), (-7.5, "#F5C451"), (0, C["cyan"]), (7.5, "#F5C451"), (15, C["pink"]))))
    rock = lambda x, y, s, d, cls: (f'<g transform="translate({x} {y}) scale({s})"><g class="{cls}" style="animation-duration:{d}s">'
                                    f'<path d="M-6 -3L-2 -7L5 -5L7 1L3 6L-4 5L-7 1Z" fill="#3A3366" stroke="#5B6390" stroke-width=".8"/>'
                                    f'<circle cx="-1.5" cy="-1" r="1.6" fill="#2A2455"/><circle cx="3" cy="2.5" r="1" fill="#2A2455"/></g></g>')
    return f'''
  <!-- mars + resident -->
  <g class="fade" style="animation-delay:.4s">
    <circle cx="{mx}" cy="{my}" r="{mr * 1.7:.0f}" fill="url(#marsHalo)"/>
    <g transform="translate({mx + 9} {my - mr + 2.6})"><g class="bob">{ALIEN}</g></g>
    <g transform="translate({mx} {my}) rotate(-20)" clip-path="url(#mback)"><circle r="3.2" fill="#B8B2D6"><animateMotion dur="6s" repeatCount="indefinite" path="M-41,0 a41,9 0 1,0 82,0 a41,9 0 1,0 -82,0"/></circle></g>
    <circle cx="{mx}" cy="{my}" r="{mr}" fill="url(#marsG)"/>
    <g clip-path="url(#mclip)"><g class="spin-x">{craters}</g>
      <ellipse cx="{mx - 4}" cy="{my - mr + 2}" rx="9" ry="3.2" fill="#FFF1EA" opacity=".85"/>
      <circle cx="{mx + 16}" cy="{my + 14}" r="{mr}" fill="{C["bg0"]}" opacity=".5" filter="url(#soft)"/></g>
    <circle cx="{mx}" cy="{my}" r="{mr - .6}" fill="none" stroke="#FF8A5B" stroke-opacity=".35"/>
    <g transform="translate({mx} {my}) rotate(-20)" clip-path="url(#mfront)"><circle r="3.2" fill="#B8B2D6"><animateMotion dur="6s" repeatCount="indefinite" path="M-41,0 a41,9 0 1,0 82,0 a41,9 0 1,0 -82,0"/></circle></g>
  </g>

  <!-- ufo with its pilot + tractor beam -->
  <g transform="translate(944 46) scale(1.3)"><g class="hover">
    <path d="M-8 6L8 6L19 62L-19 62Z" fill="url(#beamG)" class="beam"/>
    <g class="abduct"><g class="tumble">{COW}</g></g>
    <path d="M-10 0A10 9.5 0 0 1 10 0Z" fill="{C["cyan"]}" fill-opacity=".18" stroke="{C["cyan"]}" stroke-opacity=".6" stroke-width=".9"/>
    <g transform="translate(0 0) scale(.62)"><g fill="#3DDC97"><circle cx="0" cy="-8" r="6"/></g>
      <ellipse cx="-2.4" cy="-8.4" rx="1.7" ry="2.4" fill="#07041A" transform="rotate(-18 -2.4 -8.4)"/>
      <ellipse cx="2.4" cy="-8.4" rx="1.7" ry="2.4" fill="#07041A" transform="rotate(18 2.4 -8.4)"/></g>
    <ellipse cx="0" cy="1" rx="23" ry="6.2" fill="url(#ufoG)"/>
    <ellipse cx="0" cy="5" rx="12" ry="3" fill="#1B0B45"/>
    {lights}
  </g></g>

  <!-- more worlds -->
  <g class="fade" style="animation-delay:.6s">
    <circle cx="962" cy="254" r="15" fill="url(#iceG)"/>
    <g transform="rotate(18 962 254)"><ellipse cx="962" cy="254" rx="25" ry="5" fill="none" stroke="#7DF3FF" stroke-opacity=".5" stroke-width="1.3"/></g>
    <circle cx="962" cy="254" r="15" fill="none" stroke="#A5F3FC" stroke-opacity=".3"/>
    <circle cx="664" cy="266" r="8" fill="url(#pinkG)"/>
    <circle cx="664" cy="266" r="12" fill="none" stroke="{C["pink"]}" stroke-opacity=".18"/>
    {rock(706, 206, .9, 16, "spin")}{rock(792, 270, .6, 22, "spin")}{rock(905, 22, .5, 19, "spin")}
  </g>'''


ASTRONAUT = '''<g>
  <path d="M-9 -9 Q-30 -26 -44 -14" fill="none" stroke="#9AA3C7" stroke-opacity=".45" stroke-width=".9" stroke-dasharray="2 2"/>
  <rect x="-7.5" y="-7" width="15" height="14" rx="3.5" fill="#9AA3C7"/>
  <path d="M-5 -2L-11 3M5 -2L10.5 -7.5" stroke="#E8EAFF" stroke-width="3.4" stroke-linecap="round"/>
  <path d="M-2.6 7L-4.5 13.5M2.6 7L4.8 13" stroke="#E8EAFF" stroke-width="3.6" stroke-linecap="round"/>
  <rect x="-5.5" y="-5" width="11" height="13" rx="4.5" fill="#E8EAFF"/>
  <rect x="-2.5" y="-1" width="5" height="3.4" rx="1" fill="#FF2E97"/><circle cx="1.5" cy="4.4" r=".9" fill="#00E5FF"/>
  <circle cx="0" cy="-10.5" r="7" fill="#E8EAFF"/>
  <ellipse cx="1.2" cy="-10.5" rx="4.6" ry="3.7" fill="url(#visorG)"/>
  <ellipse cx="2.6" cy="-11.8" rx="1.4" ry=".9" fill="#fff" opacity=".8"/>
</g>'''

COW = '''<g transform="scale(.8)">
  <path d="M-3 2.6V5.5M-1 2.8V5.5M2 2.8V5.5M4 2.6V5.5" stroke="#E8EAFF" stroke-width="1.1" stroke-linecap="round"/>
  <ellipse cx="0" cy="0" rx="5.5" ry="3.2" fill="#F4F5FF"/>
  <circle cx="-2" cy="-.8" r="1.5" fill="#1B0B45"/><circle cx="2" cy="1" r="1.1" fill="#1B0B45"/>
  <circle cx="6.2" cy="-1.6" r="2.3" fill="#F4F5FF"/><ellipse cx="7.6" cy="-1" rx="1.1" ry=".8" fill="#FF9BCB"/>
  <path d="M5.3 -3.6L4.6 -5M7 -3.6L7.7 -5" stroke="#E8EAFF" stroke-width=".8" stroke-linecap="round"/>
</g>'''

SPARK = '<path d="M0-6L1.1-1.1L6 0L1.1 1.1L0 6L-1.1 1.1L-6 0L-1.1-1.1Z" fill="#fff"/>'


def extras2():
    """Background details: constellation, galaxy, comet, satellite, astronaut, sparkles."""
    pts = [(296, 30), (334, 48), (371, 26), (409, 41), (447, 20), (470, 52)]
    path = "M" + " L".join(f"{x} {y}" for x, y in pts)
    cons = (f'<path d="{path}" fill="none" stroke="#9AA3C7" stroke-opacity=".28" stroke-width=".8" pathLength="100" class="draw"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="1.5" fill="#E8EAFF" class="tw" style="animation-delay:-{i * .6:.1f}s"/>'
                      for i, (x, y) in enumerate(pts)))
    sparks = "".join(f'<g transform="translate({x} {y}) scale({s})"><g class="spark" style="animation-delay:-{d}s">{SPARK}</g></g>'
                     for x, y, s, d in ((560, 38, .9, 0), (980, 160, .7, 1.4), (640, 214, .6, 2.6), (262, 282, .7, 3.4), (812, 16, .6, 2)))
    return f'''
  <!-- constellation -->
  <g class="fade" style="animation-delay:.8s">{cons}</g>
  <!-- distant spiral galaxy -->
  <g transform="translate(548 270) rotate(-20)" opacity=".8"><g class="glow">
    <ellipse rx="34" ry="11" fill="url(#galaxyG)" opacity=".55"/>
    <ellipse rx="24" ry="6.5" fill="url(#galaxyG)" transform="rotate(10)"/>
    <ellipse rx="16" ry="4" fill="url(#galaxyG)" transform="rotate(-8)"/>
    <path d="M-22 3C-10 9 8 7 14 -1M22 -3C10 -9 -8 -7 -14 1" fill="none" stroke="#C4B5FD" stroke-opacity=".35" stroke-width="1.6" stroke-linecap="round"/>
    <circle r="2.6" fill="#fff" opacity=".95" filter="url(#glow)"/></g></g>
  <!-- slow comet along the bottom -->
  <g class="comet"><g transform="translate(-60 300) rotate(-9)">
    <rect x="-90" y="-2" width="90" height="4" rx="2" fill="url(#cometG)"/>
    <rect x="-55" y="-5" width="55" height="10" rx="5" fill="url(#cometG)" opacity=".35"/>
    <circle r="3" fill="#fff" filter="url(#glow)"/></g></g>
  <!-- satellite -->
  <g transform="translate(452 268)"><g class="sat">
    <path d="M-15 -3H-6M6 -3H15" stroke="#5B6390" stroke-width="1"/>
    <rect x="-24" y="-7" width="13" height="8" rx="1" fill="#2A4A9F" stroke="#7DA2FF" stroke-width=".7"/>
    <rect x="11" y="-7" width="13" height="8" rx="1" fill="#2A4A9F" stroke="#7DA2FF" stroke-width=".7"/>
    <path d="M-17.5 -7V1M17.5 -7V1" stroke="#7DA2FF" stroke-width=".5"/>
    <rect x="-5.5" y="-8" width="11" height="10" rx="2" fill="#F5C451" stroke="#B4882A" stroke-width=".7"/>
    <path d="M0 -8V-12" stroke="#9AA3C7" stroke-width=".9"/><path d="M-3.4 -12.4A3.4 2 0 0 0 3.4 -12.4Z" fill="#E8EAFF"/>
    <circle cx="0" cy="-15.5" r="1.3" fill="#FF2E97" class="lamp"/></g></g>
  <!-- astronaut drifting near mars -->
  <g transform="translate(628 48)"><g class="drift">{ASTRONAUT}</g></g>
  {sparks}'''


EXTRA_DEFS = '''
  <linearGradient id="visorG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#00E5FF"/><stop offset="1" stop-color="#5B21B6"/></linearGradient>
  <radialGradient id="galaxyG" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#F4F5FF" stop-opacity=".9"/><stop offset=".35" stop-color="#C4B5FD" stop-opacity=".45"/><stop offset="1" stop-color="#8B5CF6" stop-opacity="0"/></radialGradient>
  <linearGradient id="cometG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00E5FF" stop-opacity="0"/><stop offset="1" stop-color="#C9FBFF"/></linearGradient>
  <clipPath id="mback"><rect x="-60" y="-30" width="120" height="30"/></clipPath>
  <clipPath id="mfront"><rect x="-60" y="0" width="120" height="30"/></clipPath>
  <linearGradient id="flameG" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#FFB86B"/><stop offset=".5" stop-color="#FF2E97"/><stop offset="1" stop-color="#FF2E97" stop-opacity="0"/></linearGradient>
  <radialGradient id="marsG" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#F7A07A"/><stop offset=".5" stop-color="#C8452B"/><stop offset="1" stop-color="#4A140E"/></radialGradient>
  <radialGradient id="marsHalo" cx=".5" cy=".5" r=".5"><stop offset=".55" stop-color="#FF6A3D" stop-opacity=".25"/><stop offset="1" stop-color="#FF6A3D" stop-opacity="0"/></radialGradient>
  <radialGradient id="iceG" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#CFFAFE"/><stop offset=".5" stop-color="#0891B2"/><stop offset="1" stop-color="#0B2A4A"/></radialGradient>
  <radialGradient id="pinkG" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#FFC2DE"/><stop offset=".55" stop-color="#DB2777"/><stop offset="1" stop-color="#4A0A2A"/></radialGradient>
  <linearGradient id="ufoG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E8EAFF"/><stop offset=".55" stop-color="#9AA3C7"/><stop offset="1" stop-color="#3A3366"/></linearGradient>
  <linearGradient id="beamG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3DDC97" stop-opacity=".55"/><stop offset="1" stop-color="#3DDC97" stop-opacity="0"/></linearGradient>
  <clipPath id="mclip"><circle cx="722" cy="62" r="26"/></clipPath>'''

EXTRA_CSS = '''
.flame{transform-box:fill-box;transform-origin:100% 50%;animation:flame .18s ease-in-out infinite alternate}
@keyframes flame{from{transform:scaleX(.7)}to{transform:scaleX(1.15)}}
.wave{transform-box:view-box;transform-origin:3px -7.5px;animation:wave 1.2s ease-in-out infinite alternate}
@keyframes wave{from{transform:rotate(-25deg)}to{transform:rotate(25deg)}}
.bob{animation:bob 2.4s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-1.5px)}}
.spin-x{animation:spinx 14s ease-in-out infinite alternate}
@keyframes spinx{from{transform:translateX(-12px)}to{transform:translateX(12px)}}
.hover{animation:hover 4s ease-in-out infinite}
@keyframes hover{0%,100%{transform:translate(-7px,-3px) rotate(-4deg)}50%{transform:translate(7px,3px) rotate(4deg)}}
.beam{animation:beam 3s ease-in-out infinite}
@keyframes beam{0%,100%{opacity:.25}50%{opacity:1}}
.lamp{animation:lamp 1.25s steps(1) infinite}
@keyframes lamp{0%,40%{opacity:1}41%,100%{opacity:.25}}
.spin{transform-box:fill-box;transform-origin:50% 50%;animation:spin 16s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.draw{stroke-dasharray:100;animation:draw 2.4s ease-out 1s both}
@keyframes draw{from{stroke-dashoffset:100}to{stroke-dashoffset:0}}
.spark{transform-box:fill-box;transform-origin:50% 50%;animation:spark 3.2s ease-in-out infinite}
@keyframes spark{0%,100%{opacity:0;transform:scale(.3) rotate(0deg)}50%{opacity:.9;transform:scale(1) rotate(45deg)}}
.comet{opacity:0;animation:comet 16s linear 4s infinite}
@keyframes comet{0%{opacity:0;transform:translate(0,0)}3%{opacity:1}30%{opacity:1}36%,100%{opacity:0;transform:translate(760px,-120px)}}
.sat{animation:sat 9s ease-in-out infinite}
@keyframes sat{0%,100%{transform:translate(-6px,2px) rotate(-8deg)}50%{transform:translate(6px,-3px) rotate(8deg)}}
.drift{animation:drift 10s ease-in-out infinite}
@keyframes drift{0%,100%{transform:translate(0,0) rotate(-14deg)}50%{transform:translate(-6px,7px) rotate(12deg)}}
.abduct{animation:abduct 4.5s ease-in-out infinite}
@keyframes abduct{0%{opacity:0;transform:translateY(58px)}15%{opacity:1}80%{opacity:1;transform:translateY(16px)}95%,100%{opacity:0;transform:translateY(12px)}}
.tumble{transform-box:fill-box;transform-origin:50% 50%;animation:tumble 1.6s ease-in-out infinite alternate}
@keyframes tumble{from{transform:rotate(-14deg)}to{transform:rotate(14deg)}}'''


def planet(cx, cy, r):
    bands = "".join(
        f'<rect x="{cx - r - 40}" y="{cy + dy}" width="{2 * r + 80}" height="{h}" rx="{h / 2}" fill="{col}" opacity="{op}"/>'
        for dy, h, col, op in ((-34, 9, "#C4B5FD", .18), (-18, 5, C["cyan"], .14), (-6, 12, "#2A0F5E", .45),
                               (12, 6, "#C4B5FD", .16), (24, 10, "#1B0B45", .5), (40, 5, C["cyan"], .12)))
    orbit = (f"M{cx - r * 2.25:.0f},{cy} a{r * 2.25:.0f},{r * .62:.0f} 0 1,0 {r * 4.5:.0f},0 "
             f"a{r * 2.25:.0f},{r * .62:.0f} 0 1,0 -{r * 4.5:.0f},0")

    def rocket(half):
        return (f'<g transform="rotate(-16 {cx} {cy})" clip-path="url(#{half})"><g>{ROCKET}'
                f'<animateMotion dur="11s" repeatCount="indefinite" rotate="auto" path="{orbit}"/></g></g>')
    ring = f'<ellipse cx="{cx}" cy="{cy}" rx="{r * 1.85:.0f}" ry="{r * .42:.0f}" fill="none" stroke="url(#ringG)" '
    return f'''<g class="float">
  <circle cx="{cx}" cy="{cy}" r="{r * 1.9:.0f}" fill="url(#halo)" class="glow"/>
  <g transform="rotate(-16 {cx} {cy})">{ring}stroke-width="2.4" opacity=".55"/>{ring}stroke-width="9" opacity=".08"/></g>
  <g transform="rotate(-16 {cx} {cy})"><path d="{orbit}" fill="none" stroke="#9AA3C7" stroke-opacity=".18" stroke-dasharray="2 5"/></g>
  {rocket("back")}
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#planetG)"/>
  <g clip-path="url(#pclip)"><g class="bands">{bands}</g>
    <circle cx="{cx + r * .55:.0f}" cy="{cy + r * .5:.0f}" r="{r * 1.05:.0f}" fill="{C["bg0"]}" opacity=".55" filter="url(#soft)"/></g>
  <circle cx="{cx}" cy="{cy}" r="{r - .8}" fill="none" stroke="{C["cyan"]}" stroke-opacity=".35" stroke-width="1.2"/>
  <g transform="rotate(-16 {cx} {cy})" clip-path="url(#front)">{ring}stroke-width="2.4"/>{ring}stroke-width="9" opacity=".12"/></g>
  {rocket("front")}
</g>'''


def render():
    cx, cy, r = 838, 150, 56
    name_w = width(NAME, 46, "sb")
    roles = "  ·  ".join(ROLES)
    clips, typed = typewriter(X0 + 22, 230)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ttl desc">
<title id="ttl">{esc(NAME)}</title>
<desc id="desc">{esc(" · ".join(ROLES))}. {esc(" · ".join(TAGLINES))}.</desc>
<style>
{ASSETS["css"]}
.nm{{font:600 46px 'InterW','Inter','Segoe UI',system-ui,sans-serif;letter-spacing:-.5px}}
.rl{{font:500 15.5px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["muted"]}}}
.lb{{font:13px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["cyan"]};letter-spacing:.4px}}
.ty{{font:{TS}px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["text"]}}}
.pr{{font:{TS}px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["pink"]}}}
.st{{font:12px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["muted"]}}}
.up{{animation:up .9s cubic-bezier(.2,.7,.2,1) both}}
@keyframes up{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
.fade{{animation:fade 1.6s ease-out both}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
.rule{{transform-box:fill-box;transform-origin:0 50%;animation:rule 1.2s cubic-bezier(.65,0,.35,1) .5s both}}
@keyframes rule{{from{{transform:scaleX(0)}}to{{transform:none}}}}
.tw{{animation:tw 3.6s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:.95}}}}
.caret{{animation:blink 1s linear infinite}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
.dot{{animation:dot 2s ease-in-out infinite}}
@keyframes dot{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.ping{{transform-box:fill-box;transform-origin:50% 50%;animation:ping 2s ease-out infinite}}
@keyframes ping{{from{{transform:scale(1);opacity:.7}}to{{transform:scale(3);opacity:0}}}}
.float{{animation:float 7s ease-in-out infinite}}
@keyframes float{{0%,100%{{transform:translateY(-4px)}}50%{{transform:translateY(5px)}}}}
.bands{{animation:bands 14s ease-in-out infinite alternate}}
@keyframes bands{{from{{transform:translateX(-30px)}}to{{transform:translateX(30px)}}}}
.glow{{animation:glow 5s ease-in-out infinite}}
@keyframes glow{{0%,100%{{opacity:.7}}50%{{opacity:1}}}}
.neb1{{animation:neb1 18s ease-in-out infinite alternate}}
@keyframes neb1{{to{{transform:translate(70px,20px)}}}}
.neb2{{animation:neb2 22s ease-in-out infinite alternate}}
@keyframes neb2{{to{{transform:translate(-60px,-25px)}}}}
.shoot{{opacity:0;animation:shoot 9s linear infinite}}
@keyframes shoot{{0%{{opacity:0;transform:translate(0,0)}}2%{{opacity:1}}9%{{opacity:0;transform:translate(260px,110px)}}100%{{opacity:0;transform:translate(260px,110px)}}}}
.shimmer{{animation:shimmer 6s ease-in-out infinite}}
{EXTRA_CSS}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.shoot{{display:none}}}}
</style>
<defs>
  <linearGradient id="bgG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C["bg0"]}"/><stop offset=".6" stop-color="#0B0626"/><stop offset="1" stop-color="{C["bg1"]}"/></linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}" stop-opacity=".55"/><stop offset=".5" stop-color="{C["purple"]}" stop-opacity=".15"/><stop offset="1" stop-color="{C["cyan"]}" stop-opacity=".55"/></linearGradient>
  <linearGradient id="nameG" x1="0" y1="0" x2="{name_w:.0f}" y2="0" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#F4F5FF"/><stop offset=".45" stop-color="#C4B5FD"/><stop offset=".7" stop-color="#8AF3FF"/><stop offset="1" stop-color="#F4F5FF"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-{name_w:.0f} 0;{name_w:.0f} 0" dur="7s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="nameBase" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F4F5FF"/><stop offset="1" stop-color="#D9DCFF"/></linearGradient>
  <linearGradient id="ruleG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}"/><stop offset=".7" stop-color="{C["cyan"]}"/><stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></linearGradient>
  <linearGradient id="ringG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["cyan"]}" stop-opacity=".2"/><stop offset=".5" stop-color="{C["cyan"]}"/><stop offset="1" stop-color="{C["purple"]}"/></linearGradient>
  <linearGradient id="shootG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>
  <radialGradient id="planetG" cx=".32" cy=".3" r=".8"><stop offset="0" stop-color="#A78BFA"/><stop offset=".45" stop-color="#5B21B6"/><stop offset="1" stop-color="#120A3A"/></radialGradient>
  <radialGradient id="halo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{C["purple"]}" stop-opacity=".45"/><stop offset=".55" stop-color="#3B0F6F" stop-opacity=".15"/><stop offset="1" stop-color="{C["bg0"]}" stop-opacity="0"/></radialGradient>
  <clipPath id="pclip"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>
  <clipPath id="front"><rect x="{cx - 200}" y="{cy}" width="400" height="80"/></clipPath>
  <clipPath id="back"><rect x="{cx - 200}" y="{cy - 80}" width="400" height="80"/></clipPath>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="45"/></filter>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
  <filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  {EXTRA_DEFS}
  {clips}
</defs>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bgG)"/>
  <circle cx="230" cy="60" r="150" fill="#3B0F6F" opacity=".55" filter="url(#blur)" class="neb1"/>
  <circle cx="640" cy="290" r="140" fill="#00C9FF" opacity=".12" filter="url(#blur)" class="neb2"/>
  <circle cx="900" cy="40" r="110" fill="{C["pink"]}" opacity=".07" filter="url(#blur)" class="neb1"/>
  <g class="fade">{stars()}</g>
  <g class="shoot" style="animation-delay:2.5s"><rect x="420" y="18" width="70" height="1.4" rx=".7" fill="url(#shootG)" transform="rotate(23 490 18)"/></g>
  <g class="shoot" style="animation-delay:7s;animation-duration:13s"><rect x="80" y="150" width="56" height="1.2" rx=".6" fill="url(#shootG)" transform="rotate(23 136 150)"/></g>
  {extras2()}
  {extras()}
  <g class="fade" style="animation-delay:.2s">{planet(cx, cy, r)}</g>
</g>

<g class="up" style="animation-delay:.15s"><text x="{X0}" y="98" class="lb">// hello, world — i'm</text></g>
<g class="up" style="animation-delay:.3s">
  <text x="{X0 - 2}" y="148" class="nm" fill="url(#nameBase)">{esc(NAME)}</text>
  <text x="{X0 - 2}" y="148" class="nm" fill="url(#nameG)" opacity=".9">{esc(NAME)}</text>
</g>
<rect x="{X0}" y="166" width="{name_w * .55:.0f}" height="2" rx="1" fill="url(#ruleG)" class="rule"/>
<g class="up" style="animation-delay:.5s"><text x="{X0}" y="196" class="rl">{esc(roles)}</text></g>
<g class="up" style="animation-delay:.7s">
  <text x="{X0}" y="230" class="pr">&gt;</text>
  {typed}
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.5" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>'''


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render())
    print(f"wrote {OUT} (typing cycle {CYCLE:.1f}s)")


if __name__ == "__main__":
    main()
