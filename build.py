#!/usr/bin/env python3
"""Builds the neofetch-style profile card.

    python3 build.py [running|wave|bragg|playing|progress]

Writes dark.svg + light.svg with the chosen bottom section. Dates are recomputed
on every run; .github/workflows/update.yml runs this daily so Uptime and the
bottom section stay current. If preview.template.html sits next to this file
(local only, not committed) it also writes variants/*.svg and preview.html.
"""
import html, math, sys
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path

HERE = Path(__file__).parent
TODAY = datetime.now(ZoneInfo("America/New_York")).date()   # the day rolls over at midnight Eastern
BORN = date(2005, 10, 29)            # day from LinkedIn; year assumed from the email handle
DEGREE = (date(2024, 8, 19), date(2028, 5, 13))   # first day of class -> expected May 2028 (approx.)

FS, CW, LH = 16, 9.632, 20           # font size, widest common monospace advance, line height
PADX, TOP, ROWS = 18, 34, 26
ART_COLS, N = 44, 60                 # portrait columns, info-panel columns
PX = PADX + (ART_COLS + 2) * CW      # info panel x
W = round(PX + N * CW + PADX)
H = TOP + (ROWS - 1) * LH + 24
FONT = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
THEMES = {
    "dark":  dict(bg="#161b22", t="#c9d1d9", k="#ffa657", v="#a5d6ff", d="#616e7f", g="#3fb950"),
    "light": dict(bg="#f6f8fa", t="#24292f", k="#953800", v="#0a3069", d="#b6c2cf", g="#1a7f37"),
}
VARIANTS = ["running", "wave", "bragg", "playing", "progress"]

y = lambda row: TOP + row * LH
esc = lambda s: html.escape(s, quote=False)
span = lambda cls, s: f'<tspan class="{cls}">{esc(s)}</tspan>' if s else ""
line = lambda row, inner, x=PX: f'<text x="{x:.1f}" y="{y(row)}" xml:space="preserve">{inner}</text>'


def kv(row, key, value, extra=()):
    """. key: ......... value   (value right-aligned, dots fill the gap)"""
    tail = value + "".join(t for _, t in extra)
    ndots = N - 2 - len(key) - 2 - 1 - len(tail)
    assert ndots >= 2, f"line too long: {key}"
    return line(row, span("d", ". ") + span("k", key) + span("t", ":") + span("d", " " + "." * ndots + " ")
                + span("v", value) + "".join(span(c, t) for c, t in extra))


def header(row, label, after=0.0):
    x0 = PX + (len(label) + 1) * CW + after
    x1 = PX + N * CW
    yy = y(row) - 5.5
    segs = [(x0, x1 - 36), (x1 - 32, x1 - 27), (x1 - 23, x1 - 9), (x1 - 5, x1)]
    rule = "".join(f'<rect class="t" x="{a:.1f}" y="{yy}" width="{b - a:.1f}" height="1.3"/>' for a, b in segs)
    return line(row, span("t", label)) + rule


def blank(row):
    return line(row, span("d", "."))


def ymd(a, b):
    yrs, mos, days = b.year - a.year, b.month - a.month, b.day - a.day
    if days < 0:
        mos -= 1
        prev = date(b.year, b.month, 1).toordinal() - 1
        days += date.fromordinal(prev).day
    if mos < 0:
        yrs -= 1; mos += 12
    return yrs, mos, days


def up(start):
    m = (TODAY.year - start.year) * 12 + TODAY.month - start.month
    return (f"{m // 12}y " if m >= 12 else "") + (f"{m % 12}mo" if m % 12 or m < 12 else "")


# ── bottom sections ─────────────────────────────────────────────────────────
def running(r, uid):
    rows = [("heelcode", "agent harness for CS classrooms", date(2026, 9, 1)),
            ("wavemaker", "13,500 gal wave tank, 30 pistons", date(2025, 11, 1)),
            ("nscc", "President & Founder", date(2025, 10, 1)),
            ("ai-safety", "Fellow, Carolina AI Alignment", date(2026, 8, 1))]
    out = [header(r, "- Running")]
    for i, (k, v, s) in enumerate(rows):
        out.append(kv(r + 1 + i, k, v, [("t", " | "), ("g", "up " + up(s).strip())]))
    return out


def wave(r, uid):
    base, maxh, period = y(r + 3) + 4, 3 * LH - 8, 30
    bars = []
    for i in range(-period, N):
        ph = 2 * math.pi * i / period
        h = 0.14 + 0.80 * math.cos(ph / 2) ** 6 + 0.05 * math.sin(3 * ph + 1.0)   # soliton pulse + ripple
        hp = max(2.5, round(h * maxh / 2.5) * 2.5)
        bars.append(f'<rect x="{PX + i * CW + 1:.1f}" y="{base - hp:.1f}" width="{CW - 2:.1f}" height="{hp:.1f}"/>')
    return [header(r, "- Wave Tank"),
            f'<clipPath id="{uid}c"><rect x="{PX:.1f}" y="{base - maxh - 2:.1f}" width="{N * CW:.1f}" height="{maxh + 4:.1f}"/></clipPath>',
            f'<g clip-path="url(#{uid}c)"><g class="v" opacity=".85">{"".join(bars)}'
            f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{period * CW:.2f} 0" dur="5s" repeatCount="indefinite"/></g></g>',
            kv(r + 4, "Wave.Maker", "EEL @ UNC, 30 pistons, 13,500 gal")]


def bragg_curve(zmax=18.0, R=15.77, sigma=0.19):
    """Depth-dose of 150 MeV protons in water: Bragg-Kleeman stopping with range straggling."""
    M = 1800; dz = zmax / M
    raw = [(1 - 0.012 * z) * (R - z) ** -0.435 if z < R - dz / 2 else 0.0 for z in (dz * (i + 0.5) for i in range(M))]
    k = int(4 * sigma / dz)
    ker = [math.exp(-0.5 * (j * dz / sigma) ** 2) for j in range(-k, k + 1)]
    ks = sum(ker)
    sm = [sum(raw[i + j - k] * ker[j] for j in range(2 * k + 1) if 0 <= i + j - k < M) / ks for i in range(M)]
    per = M // N
    cells = [sum(sm[c * per:(c + 1) * per]) / per for c in range(N)]
    top = max(cells)
    return [c / top for c in cells]


def bragg(r, uid):
    base, maxh = y(r + 3) + 4, 3 * LH - 8
    cells = bragg_curve()
    peak = cells.index(max(cells))
    bars = []
    for i, c in enumerate(cells):
        hp = round(c * maxh / 2.5) * 2.5
        if hp <= 0:
            continue
        bars.append(f'<rect class="{"k" if i == peak else "v"}" x="{PX + i * CW + 1:.1f}" y="{base - hp:.1f}" width="{CW - 2:.1f}" height="{hp:.1f}"/>')
    axis = f'<rect class="d" x="{PX:.1f}" y="{base + 1.5:.1f}" width="{N * CW:.1f}" height="1"/>'
    return [header(r, "- Bragg Peak"), "".join(bars), axis,
            kv(r + 4, "Proton.Beam", "150 MeV in water, stops at 15.8 cm")]


def playing(r, uid):
    x0 = PX + 14 * CW
    eq = ""
    for i, (vals, dur) in enumerate([("5;13;7;11;5", 1.1), ("12;4;10;6;12", 0.9), ("7;11;3;13;7", 1.3), ("10;6;13;4;10", 1.0)]):
        hs = vals.split(";")
        ys = ";".join(f"{y(r) - float(h):.1f}" for h in hs)
        eq += (f'<rect class="k" x="{x0 + i * 6:.1f}" y="{y(r) - float(hs[0]):.1f}" width="4" height="{hs[0]}">'
               f'<animate attributeName="height" values="{vals}" dur="{dur}s" repeatCount="indefinite"/>'
               f'<animate attributeName="y" values="{ys}" dur="{dur}s" repeatCount="indefinite"/></rect>')
    return [header(r, "- Now Playing", after=5 * 6 + 8), eq,
            kv(r + 1, "On.Loop", "Her Abiding Memory, Pitcher56"),
            kv(r + 2, "Rotation", "Lamp, Ichiko Aoba, Ryo Fukui, Feng"),
            kv(r + 3, "Also", "LCD Soundsystem, Grimes, Aphex Twin"),
            kv(r + 4, "Full.Shelf", "keffer.cafe/stuff/media")]


def progress(r, uid):
    BAR0, BARN = 21, 16
    a, b = DEGREE
    bday = date(TODAY.year, BORN.month, BORN.day)
    last = bday if bday <= TODAY else date(TODAY.year - 1, BORN.month, BORN.day)
    nxt = date(last.year + 1, BORN.month, BORN.day)
    y0, y1 = date(TODAY.year, 1, 1), date(TODAY.year + 1, 1, 1)
    rows = [("B.S. CS + Math", (TODAY - a).days / (b - a).days, f"{(b - TODAY).days}d to May '28"),
            (f"Orbit.{last.year - BORN.year + 1}", (TODAY - last).days / (nxt - last).days, f"{(nxt - TODAY).days}d to Oct 29"),
            (f"Year.{TODAY.year}", (TODAY - y0).days / (y1 - y0).days, f"{(y1 - TODAY).days}d left")]
    out = [header(r, "- Progress")]
    for i, (k, f, tail) in enumerate(rows):
        row = r + 1 + i
        f = min(1, max(0, f))
        nd = BAR0 - (2 + len(k) + 1) - 2
        inner = (span("d", ". ") + span("k", k) + span("t", ":") + span("d", " " + "." * nd + " ")
                 + f'<tspan class="v" x="{PX + (BAR0 + BARN) * CW:.1f}">{esc(f"{round(f * 100):>4d}%")}</tspan>'
                 + span("t", " | ") + span("g", tail))
        out.append(line(row, inner))
        fill = round(f * BARN)
        for c in range(BARN):
            cls = 'class="v"' if c < fill else 'class="d" opacity=".45"'
            out.append(f'<rect {cls} x="{PX + (BAR0 + c) * CW + 1:.1f}" y="{y(row) - 11.5}" width="{CW - 2:.1f}" height="12"/>')
    return out


BOTTOM = dict(running=running, wave=wave, bragg=bragg, playing=playing, progress=progress)


# ── the card ────────────────────────────────────────────────────────────────
def card(variant, theme=None):
    """theme=None -> classes only (colours come from the host page's CSS)."""
    uid = f"nf-{variant}"
    art = (HERE / "portrait.txt").read_text().split("\n")
    yrs, mos, days = ymd(BORN, TODAY)
    body = [f'<text class="t" xml:space="preserve">' + "".join(
        f'<tspan x="{PADX}" y="{y(i)}">{esc(l)}</tspan>' for i, l in enumerate(art) if l.strip()) + "</text>"]
    r = 0
    body.append(header(r, "william@keffer")); r += 1
    for k, v in [("OS", "macOS 26, Arch Linux, iOS"),
                 ("Uptime", f"{yrs} years, {mos} months, {days} days"),
                 ("Host", "UNC Chapel Hill"),
                 ("Kernel", "B.S. Computer Science + Mathematics '28"),
                 ("IDE", "VS Code, Codex")]:
        body.append(kv(r, k, v)); r += 1
    body.append(blank(r)); r += 1
    for k, v in [("Languages.Programming", "Python, TypeScript, Rust, SQL"),
                 ("Languages.Computer", "HTML, CSS, GLSL, Bash, LaTeX"),
                 ("Languages.Real", "English, Deutsch (WIP)")]:
        body.append(kv(r, k, v)); r += 1
    body.append(blank(r)); r += 1
    for k, v in [("Hobbies.Software", "Deep Rock Galactic, Fortnite"),
                 ("Hobbies.Hardware", "Espresso, Nintendo handhelds"),
                 ("Hobbies.Archive", "Stüssy (stussy.ink)")]:
        body.append(kv(r, k, v)); r += 1
    r += 1
    body.append(header(r, "- Contact")); r += 1
    for k, v in [("Email", "williamkeffer2005@gmail.com"),
                 ("Website", "keffer.cafe"),
                 ("LinkedIn", "williamkeffer"),
                 ("GitHub", "WillieTheWhale")]:
        body.append(kv(r, k, v)); r += 1
    r += 1
    body += BOTTOM[variant](r, uid)
    style = ""
    bg = f'<rect class="nf-bg" width="{W}" height="{H}" rx="14"/>'
    if theme:
        c = THEMES[theme]
        style = (f"<style>text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}"
                 f".nf-bg{{fill:{c['bg']}}}.t{{fill:{c['t']}}}.k{{fill:{c['k']}}}.v{{fill:{c['v']}}}.d{{fill:{c['d']}}}.g{{fill:{c['g']}}}</style>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="nf" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="William Keffer, neofetch-style profile card">{style}{bg}{"".join(body)}</svg>\n')


def main():
    pick = sys.argv[1] if len(sys.argv) > 1 else "running"
    assert pick in VARIANTS, f"choose one of {VARIANTS}"
    for th in THEMES:
        (HERE / f"{th}.svg").write_text(card(pick, th))
    print(f"built {pick}: {W}x{H}, uptime {ymd(BORN, TODAY)}")
    tpl_path = HERE / "preview.template.html"
    if not tpl_path.exists():
        return
    (HERE / "variants").mkdir(exist_ok=True)
    for v in VARIANTS:
        for th in THEMES:
            (HERE / "variants" / f"{v}-{th}.svg").write_text(card(v, th))
    tpl = tpl_path.read_text()
    cards = "".join(f'<div class="variant" data-v="{v}"{"" if v == pick else " hidden"}>{card(v)}</div>' for v in VARIANTS)
    (HERE / "preview.html").write_text(tpl.replace("<!--CARDS-->", cards).replace("__FONT__", FONT).replace("__MINW__", str(round(W * 0.74))))


if __name__ == "__main__":
    main()
