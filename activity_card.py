#!/usr/bin/env python3
"""Render assets/activity.svg — contribution grid with a comet sweep, plus streak stats, in the profile's card style.

Replaces the third-party snake + streak widgets. Standard library only; reuses stats_assets.json:
    GITHUB_TOKEN=... GH_LOGIN=zinmeir python3 scripts/activity_card.py
Use --sample to render with placeholder data (no network).
Streaks are counted in STREAK_TZ (default Asia/Karachi); today with no contributions yet doesn't break a streak.
"""
import json, os, random, sys, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "activity.svg"
ASSETS = json.loads((HERE / "stats_assets.json").read_text())
TZ = os.environ.get("STREAK_TZ", "Asia/Karachi")

C = dict(bg0="#07041A", bg1="#0F0A2E", text="#E8EAFF", muted="#9AA3C7", dim="#5B6390",
         purple="#8B5CF6", cyan="#00E5FF", pink="#FF2E97", empty="#1A1545")
LEVEL = {"NONE": C["empty"], "FIRST_QUARTILE": "#3B0F6F", "SECOND_QUARTILE": "#6D28D9",
         "THIRD_QUARTILE": C["purple"], "FOURTH_QUARTILE": C["cyan"]}

CAL = "contributionCalendar { totalContributions weeks { contributionDays { date contributionCount contributionLevel } } }"
Q_MAIN = "query($login: String!) { user(login: $login) { contributionsCollection { contributionYears %s } } }" % CAL
Q_YEAR = ("query($login: String!, $from: DateTime!, $to: DateTime!) { user(login: $login) { "
          "contributionsCollection(from: $from, to: $to) { %s } } }" % CAL)


# ---------------------------------------------------------------- data
def gql(token, query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-activity-card"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        sys.exit(f"GitHub API error: {body['errors']}")
    return body["data"]["user"]["contributionsCollection"]


def fetch(login, token):
    cc = gql(token, Q_MAIN, {"login": login})
    cal = cc["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"], d["contributionLevel"]) for d in w["contributionDays"]]
             for w in cal["weeks"]]
    days, now = {}, datetime.now(timezone.utc)
    for y in sorted(cc["contributionYears"]):          # whole history, one year per request
        to = min(datetime(y, 12, 31, 23, 59, 59, tzinfo=timezone.utc), now)
        c = gql(token, Q_YEAR, {"login": login, "from": f"{y}-01-01T00:00:00Z",
                                "to": to.strftime("%Y-%m-%dT%H:%M:%SZ")})["contributionCalendar"]
        for w in c["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    for w in weeks:                                    # the rolling-year calendar is the freshest view
        for dt, n, _ in w:
            days[dt] = n
    return dict(weeks=weeks, days=days, year_total=cal["totalContributions"])


def sample(today):
    rnd = random.Random(11)
    start = today - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # weeks start on Sunday, like GitHub's
    lvl = lambda n: ("NONE", "FIRST_QUARTILE", "FIRST_QUARTILE", "SECOND_QUARTILE", "SECOND_QUARTILE",
                     "THIRD_QUARTILE", "THIRD_QUARTILE")[n] if n < 7 else "FOURTH_QUARTILE"
    weeks, days, d = [], {}, start
    while d <= today:
        burst = 230 < (today - d).days < 262 or 40 < (today - d).days < 60 or (today - d).days < 12
        n = rnd.choice([1, 1, 2, 3, 4, 6, 9]) if rnd.random() < (.55 if burst else .07) else 0
        if d == today: n = 2
        if d == today - timedelta(1): n = 0
        days[d.isoformat()] = n
        if not weeks or (d.weekday() + 1) % 7 == 0:
            weeks.append([])
        weeks[-1].append((d.isoformat(), n, lvl(n)))
        d += timedelta(1)
    for k in range(400, 700):                           # an older year, for all-time totals
        if rnd.random() < .12:
            days[(today - timedelta(k)).isoformat()] = rnd.choice([1, 2, 3])
    return dict(weeks=weeks, days=days, year_total=sum(n for w in weeks for _, n, _ in w))


def streaks(days, today):
    has = lambda d: days.get(d.isoformat(), 0) > 0
    d = today if has(today) else today - timedelta(1)
    end, n = d, 0
    while has(d):
        n, d = n + 1, d - timedelta(1)
    cur = (n, d + timedelta(1), end)

    active = sorted(date.fromisoformat(k) for k, v in days.items() if v > 0)
    best, run, start, prev = (0, None, None), 0, None, None
    for d in active:
        run, start = (run + 1, start) if prev and d == prev + timedelta(1) else (1, d)
        prev = d
        if run > best[0]:
            best = (run, start, d)
    return cur, best, (active[0] if active else None)


# ---------------------------------------------------------------- rendering helpers
def width(text, size, font):
    w = ASSETS["widths"][font]
    return sum(w.get(ch, 0.6) for ch in text) * size


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fdate(d, today):
    return f"{d:%b} {d.day}" + (f", {d.year}" if d.year != today.year else "")


def span(a, b, today):
    return fdate(a, today) if a == b else f"{fdate(a, today)} — {fdate(b, today)}"


W, M, G, PAD = 1000, 22, 14, 18
PW = W - 2 * M


def panel(x, y, w, h, n, title, acc):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" fill="url(#panel)" stroke="#2A2465"/>'
            f'<text x="{x + PAD:.1f}" y="{y + 28:.1f}" class="h"><tspan fill="{acc}">{n}</tspan>'
            f'<tspan fill="{C["dim"]}"> // </tspan>{title}</text>'
            f'<rect x="{x + PAD:.1f}" y="{y + 38:.1f}" width="{w - 2 * PAD:.1f}" height="1" fill="url(#rule)"/>')


def render(d, login, today):
    weeks, days = d["weeks"], d["days"]
    (cur, cs, ce), (best, bs, be), first = streaks(days, today)
    total = sum(days.values())

    # ---- contribution grid
    ncol = len(weeks)
    gx, y0 = M + PAD + 34, M
    pitch = min(17.0, (PW - 2 * PAD - 34) / ncol)
    cell = pitch - 3.6
    gy = y0 + 72
    T0, TRAVEL, CYCLE = 1.9, 6.0, 10.0                   # comet: start, crossing time, loop length (s)
    cx0, cx1 = gx - 80, gx + ncol * pitch + 80
    cells, zaps, months, last_m = [], [], [], -9
    for c, wk in enumerate(weeks):
        for dt, n, lv in wk:
            r = (date.fromisoformat(dt).weekday() + 1) % 7
            x, y = gx + c * pitch, gy + r * pitch
            cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="3" fill="{LEVEL[lv]}" '
                         f'class="cell" style="animation-delay:{.15 + (c + r) * .012:.3f}s"><title>{n} on {dt}</title></rect>')
            if n:
                t = T0 + TRAVEL * (x + cell / 2 - cx0) / (cx1 - cx0)
                zaps.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="3" fill="#C9FBFF" '
                            f'class="zap" style="animation-delay:{t:.2f}s"/>')
        m = date.fromisoformat(wk[0][0])
        if m.day <= 7 and c - last_m > 2:
            months.append(f'<text x="{gx + c * pitch:.1f}" y="{gy - 10:.1f}" class="m">{m:%b}</text>')
            last_m = c
    days_lbl = "".join(f'<text x="{M + PAD:.1f}" y="{gy + r * pitch + cell - 2:.1f}" class="m">{t}</text>'
                       for r, t in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    ly = gy + 7 * pitch + 22
    sw = "".join(f'<rect x="{M + PW - PAD - 30 - (5 - i) * 15:.1f}" y="{ly - 10:.1f}" width="11" height="11" rx="2.5" fill="{col}"/>'
                 for i, col in enumerate(LEVEL.values()))
    legend = (f'<text x="{gx:.1f}" y="{ly:.1f}" class="m"><tspan fill="{C["text"]}">{d["year_total"]:,}</tspan> contributions in the last year</text>'
              f'<text x="{M + PW - PAD - 30 - 5 * 15 - 8:.1f}" y="{ly:.1f}" class="m" text-anchor="end">less</text>{sw}'
              f'<text x="{M + PW - PAD:.1f}" y="{ly:.1f}" class="m" text-anchor="end">more</text>')
    h1 = ly + 18 - y0
    amp = 2.3 * pitch
    comet = f'''<g class="comet" style="animation-delay:{T0}s"><g transform="translate({cx0:.1f} {gy + 3.5 * pitch:.1f})"><g class="wob">
    <rect x="-110" y="-9" width="110" height="18" rx="9" fill="url(#tail)" opacity=".35"/>
    <rect x="-90" y="-2.5" width="90" height="5" rx="2.5" fill="url(#tail)"/>
    <circle r="11" fill="{C["cyan"]}" opacity=".35" filter="url(#blur)"/>
    <circle r="4.6" fill="#fff" filter="url(#glow)"/>
  </g></g></g>'''

    # ---- streak tiles
    ty, TW3, TH = y0 + h1 + G, (PW - 2 * G) / 3, 180
    xs = [M + i * (TW3 + G) for i in range(3)]

    # total + monthly bars
    mt = []
    for k in range(11, -1, -1):
        y_, m_ = today.year, today.month - k
        while m_ <= 0:
            y_, m_ = y_ - 1, m_ + 12
        mt.append(sum(v for key, v in days.items() if key.startswith(f"{y_}-{m_:02d}")))
    top = max(mt) or 1
    bx0, bb = xs[0] + TW3 - PAD - 12 * 9 + 3, ty + 146
    bars = "".join(
        f'<rect x="{bx0 + i * 9:.1f}" y="{bb - max(3, v / top * 62):.1f}" width="6" height="{max(3, v / top * 62):.1f}" rx="2" '
        f'fill="{"url(#barG)" if v else C["empty"]}" class="bar" style="animation-delay:{.9 + i * .05:.2f}s"/>' for i, v in enumerate(mt))
    since = esc(fdate(first, today)) + " — now" if first else "no contributions yet"
    t1 = f'''<g class="rise" style="animation-delay:.35s">{panel(xs[0], ty, TW3, TH, "02", "total contributions", C["purple"])}
  <text x="{xs[0] + PAD:.1f}" y="{ty + 106:.1f}" class="big">{total:,}</text>
  <text x="{xs[0] + PAD:.1f}" y="{ty + 136:.1f}" class="m">{since}</text>
  <text x="{xs[0] + PAD:.1f}" y="{ty + 156:.1f}" class="m" fill-opacity=".7">last 12 months &#8594;</text>
  {bars}</g>'''

    # current streak ring, filled as a share of the record
    rcx, rcy, rr = xs[1] + TW3 / 2, ty + 98, 37
    pct = min(cur / best, 1) * 100 if best else 0
    cur_txt = (esc(span(cs, ce, today)) if cur else "starts with today's commit") + (" · record" if cur and cur == best else "")
    t2 = f'''<g class="rise" style="animation-delay:.45s">{panel(xs[1], ty, TW3, TH, "03", "current streak", C["pink"])}
  <circle cx="{rcx:.1f}" cy="{rcy:.1f}" r="{rr}" fill="none" stroke="{C["empty"]}" stroke-width="7"/>
  <circle cx="{rcx:.1f}" cy="{rcy:.1f}" r="{rr}" fill="none" stroke="url(#ringG)" stroke-width="7" stroke-linecap="round" pathLength="100"
    stroke-dasharray="{max(pct - .01, 0):.2f} 100" transform="rotate(-90 {rcx:.1f} {rcy:.1f})" class="ring"/>
  <circle cx="{rcx:.1f}" cy="{rcy - rr:.1f}" r="12" fill="#120D3D"/>
  <g transform="translate({rcx:.1f} {rcy - rr - 1:.1f})"><g class="flame">
    <path d="M0-12C6-6 8.5-1.5 7.5 3.5C6.5 8.5 3.5 11 0 11S-6.5 8.5-7.5 3.5C-8.5-1.5-4-5-1.5-9.5C-.5-5 2-4.5 2-7.5Z" fill="{C["pink"]}"/>
    <path d="M0-3C3 0 4 2.5 3.5 5S1.5 8 0 8-3.5 7.5-3.5 5-1.5 1-1 -1C-.5 1 .8 1 0-3Z" fill="#FFC2DE"/>
  </g></g>
  <text x="{rcx:.1f}" y="{rcy + 11:.1f}" class="mid" text-anchor="middle">{cur}</text>
  <text x="{rcx:.1f}" y="{ty + 160:.1f}" class="m" text-anchor="middle">{cur_txt}</text>
</g>'''

    # longest streak + a week-style strip of its days
    lit = min(best, 21)
    dots = "".join(
        f'<rect x="{xs[2] + TW3 - PAD - 7 * 14 + 3 + (i % 7) * 14:.1f}" y="{ty + 90 + (i // 7) * 14:.1f}" width="10.5" height="10.5" rx="2.5" '
        + (f'fill="{C["cyan"]}" class="seq" style="animation-delay:{1 + i * .09:.2f}s"/>' if i < lit else f'fill="{C["empty"]}"/>')
        for i in range(21))
    more = f'<text x="{xs[2] + TW3 - PAD:.1f}" y="{ty + 148:.1f}" class="m" text-anchor="end">+{best - 21} more</text>' if best > 21 else ""
    best_txt = esc(span(bs, be, today)) if best else "—"
    t3 = f'''<g class="rise" style="animation-delay:.55s">{panel(xs[2], ty, TW3, TH, "04", "longest streak", C["cyan"])}
  <text x="{xs[2] + PAD:.1f}" y="{ty + 106:.1f}" class="big">{best}<tspan class="unit" dx="6">{"day" if best == 1 else "days"}</tspan></text>
  <text x="{xs[2] + PAD:.1f}" y="{ty + 136:.1f}" class="m">{best_txt}</text>
  {dots}{more}</g>'''

    H = round(ty + TH + M)
    stars = "".join(f'<circle cx="{sx}" cy="{sy * H / 100:.1f}" r="{r}" fill="{C["text"]}" class="tw" style="animation-delay:-{i * .8:.1f}s"/>'
                    for i, (sx, sy, r) in enumerate([(11, 8, .9), (989, 14, .8), (7, 60, .7), (993, 70, .9), (500, 1.6, .7), (300, 98.6, .8), (760, 98.8, .7)]))
    zap_kf = "0%{opacity:0;transform:scale(1)}1%{opacity:.8;transform:scale(1.3)}5%,100%{opacity:0;transform:scale(1)}"
    end = TRAVEL / CYCLE * 100

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ttl desc">
<title id="ttl">GitHub activity — {esc(login)}</title>
<desc id="desc">{d["year_total"]:,} contributions in the last year, {total:,} in total. Current streak {cur} days, longest streak {best} days.</desc>
<style>
{ASSETS["css"]}
.h{{font:12.5px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["text"]};letter-spacing:.3px}}
.m{{font:11px 'MonoW','JetBrains Mono',Consolas,monospace;fill:{C["dim"]}}}
.big{{font:600 40px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["text"]};font-variant-numeric:tabular-nums}}
.mid{{font:600 30px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["text"]}}}
.unit{{font:500 15px 'InterW','Inter','Segoe UI',system-ui,sans-serif;fill:{C["muted"]}}}
.rise{{animation:rise .8s cubic-bezier(.2,.7,.2,1) both}}
@keyframes rise{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
.cell{{transform-box:fill-box;transform-origin:50% 50%;animation:cin .5s cubic-bezier(.2,.8,.2,1.25) both}}
@keyframes cin{{from{{opacity:0;transform:scale(.3)}}to{{opacity:1;transform:none}}}}
.zap{{opacity:0;transform-box:fill-box;transform-origin:50% 50%;animation:zap {CYCLE}s ease-out infinite}}
@keyframes zap{{{zap_kf}}}
.comet{{opacity:0;animation:comet {CYCLE}s linear infinite}}
@keyframes comet{{0%{{transform:translateX(0);opacity:0}}3%{{opacity:1}}{end - 4:.1f}%{{opacity:1}}{end:.1f}%,100%{{transform:translateX({cx1 - cx0:.1f}px);opacity:0}}}}
.wob{{animation:wob 2.3s ease-in-out infinite alternate}}
@keyframes wob{{from{{transform:translateY(-{amp:.1f}px)}}to{{transform:translateY({amp:.1f}px)}}}}
.bar{{transform-box:fill-box;transform-origin:50% 100%;animation:grow .8s cubic-bezier(.2,.7,.2,1) both}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:none}}}}
.ring{{animation:ring 1.4s cubic-bezier(.3,.7,.2,1) .7s both}}
@keyframes ring{{from{{stroke-dasharray:0 100}}}}
.flame{{transform-box:fill-box;transform-origin:50% 100%;animation:flame 1.1s ease-in-out infinite alternate}}
@keyframes flame{{0%{{transform:scale(1,1) rotate(-3deg)}}50%{{transform:scale(.92,1.1) rotate(2deg)}}100%{{transform:scale(1.05,.95) rotate(-1deg)}}}}
.seq{{opacity:.3;animation:seq 4s ease-in-out infinite}}
@keyframes seq{{0%{{opacity:.3}}8%,60%{{opacity:1}}75%,100%{{opacity:.3}}}}
.tw{{animation:tw 3.6s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:.85}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.comet,.zap{{display:none}}.seq{{opacity:1}}}}
</style>
<defs>
  <linearGradient id="bgG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C["bg0"]}"/><stop offset="1" stop-color="{C["bg1"]}"/></linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}" stop-opacity=".55"/><stop offset=".5" stop-color="{C["purple"]}" stop-opacity=".15"/><stop offset="1" stop-color="{C["cyan"]}" stop-opacity=".55"/></linearGradient>
  <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#15104A" stop-opacity=".75"/><stop offset="1" stop-color="#0B0828" stop-opacity=".75"/></linearGradient>
  <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}" stop-opacity=".5"/><stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></linearGradient>
  <linearGradient id="barG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{C["cyan"]}"/><stop offset="1" stop-color="{C["purple"]}"/></linearGradient>
  <linearGradient id="ringG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C["cyan"]}"/><stop offset="1" stop-color="{C["purple"]}"/></linearGradient>
  <linearGradient id="tail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C["purple"]}" stop-opacity="0"/><stop offset=".6" stop-color="{C["purple"]}" stop-opacity=".55"/><stop offset="1" stop-color="{C["cyan"]}"/></linearGradient>
  <filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="blur" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="4"/></filter>
</defs>
<rect width="{W}" height="{H}" rx="20" fill="url(#bgG)"/>
{stars}
<g class="rise" style="animation-delay:.05s">{panel(M, y0, PW, h1, "01", "contributions", C["cyan"])}
  {"".join(months)}{days_lbl}
  {"".join(cells)}
  {"".join(zaps)}
  {comet}
  {legend}
</g>
{t1}
{t2}
{t3}
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.5" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>'''


def main():
    login = os.environ.get("GH_LOGIN", "zinmeir")
    today = datetime.now(ZoneInfo(TZ)).date()
    if "--sample" in sys.argv:
        data = sample(today)
    else:
        token = os.environ.get("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN is not set")
        data = fetch(login, token)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(data, login, today))
    (cur, _, _), (best, _, _), _ = streaks(data["days"], today)
    print(f"wrote {OUT}: {sum(data['days'].values())} contributions, streak {cur}, longest {best}")


if __name__ == "__main__":
    main()
