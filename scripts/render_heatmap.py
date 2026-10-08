"""Render data/contributions.json as assets/contributions.svg: the 53-week calendar drawn the way GitHub draws it
(no frame, in the README's purple), with each box popping in on a diagonal sweep once, then holding.

CSS keyframes inside the SVG (GitHub plays them in an <img>; it never runs scripts). Standard library only.
STATIC=1 writes the finished frame for previews.
"""
import json
import os
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
STATIC = os.environ.get('STATIC') == '1'

PITCH, CELL = 16, 13
LEFT, TOP = 34, 24
LEVELS = ['#161b22', '#2d2a55', '#4b3f96', '#7a68d8', '#a78bfa']  # the README's purple
SANS = '-apple-system,Segoe UI,Helvetica,Arial,sans-serif'


def main():
    data = json.loads((ROOT / 'data' / 'contributions.json').read_text(encoding='utf-8'))
    days = data['days']
    weeks = max(d['week'] for d in days) + 1
    W = LEFT + weeks * PITCH + 14  # room for a month label over the last column
    grid_bottom = TOP + 7 * PITCH
    H = grid_bottom + 34
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{SANS}" '
        f'role="img" aria-label="{data["total"]} GitHub contributions in the last year">',
        '<style>',
        'text.l{fill:#7d8590;font-size:13px;font-weight:600}',
        'text.t{fill:#e6edf3;font-size:15px;font-weight:700}',
        '.c{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .55s ease-out both}',
        '.g{animation:pop .55s ease-out both,flash .7s ease-out both}',
        '@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}',
        '@keyframes flash{0%,45%{filter:brightness(2.2)}100%{filter:brightness(1)}}',
        '@media (prefers-reduced-motion:reduce){.c{opacity:1!important;animation:none!important}}',
        '</style>',
    ]
    seen = set()
    for d in sorted(days, key=lambda d: (d['week'], d['weekday'])):
        y, m, dd = (int(x) for x in d['date'].split('-'))
        if dd <= 7 and d['weekday'] == 0 and (y, m) not in seen:
            seen.add((y, m))
            out.append(f'<text class="l" x="{LEFT + d["week"] * PITCH}" y="16">{date(y, m, 1).strftime("%b")}</text>')
    for i, name in ((1, 'Mon'), (3, 'Wed'), (5, 'Fri')):
        out.append(f'<text class="l" x="2" y="{TOP + i * PITCH + 11}">{name}</text>')
    for d in days:
        level = min(d['level'], 4)
        cls = '' if STATIC else (' class="c g"' if level else ' class="c"')
        delay = '' if STATIC else f' style="animation-delay:{(d["week"] + d["weekday"]) * 0.028:.3f}s"'
        tip = f"{d['count']} contribution{'s' if d['count'] != 1 else ''} on {d['date']}"
        out.append(f'<rect{cls}{delay} x="{LEFT + d["week"] * PITCH}" y="{TOP + d["weekday"] * PITCH}" width="{CELL}" '
                   f'height="{CELL}" rx="2.5" fill="{LEVELS[level]}"><title>{escape(tip)}</title></rect>')
    out.append(f'<text class="t" x="{LEFT}" y="{grid_bottom + 22}">{data["total"]:,} contributions in the last year</text>')
    lx = W - 5 * PITCH - 38
    out.append(f'<text class="l" x="{lx - 8}" y="{grid_bottom + 21}" text-anchor="end">Less</text>')
    for i, c in enumerate(LEVELS):
        out.append(f'<rect x="{lx + i * PITCH}" y="{grid_bottom + 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    out.append(f'<text class="l" x="{lx + 5 * PITCH + 4}" y="{grid_bottom + 21}">More</text>')
    out.append('</svg>')
    name = 'contributions-static.svg' if STATIC else 'contributions.svg'
    (ROOT / 'assets').mkdir(exist_ok=True)
    (ROOT / 'assets' / name).write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'wrote assets/{name}: {W} x {H}, {weeks} weeks')


if __name__ == '__main__':
    main()
