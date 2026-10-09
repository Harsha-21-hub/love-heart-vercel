"""Browser-friendly web version of the Love Heart animation.

The composition, heart geometry, phrase placement, color selection, and animation
schedule are generated in Python. FastAPI serves the page; SVG animations are
rendered natively by the browser, including on Android.
"""
from __future__ import annotations

import html
import math
import random
import unicodedata
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

# Keep the original design settings and language list.
SC = 21
OY = 20
DURATION = 10.0
ANIM = 42
LIFT = 34
GAP = 7
SIZES = (9, 10, 11, 12)
BG = "#060208"
FLASH = (1.0, 0.78, 0.78)
WINE = (0.58, 0.0, 0.09)
CRIMSON = (0.90, 0.05, 0.14)
BLOOD = (0.98, 0.10, 0.16)

PHRASES = [
    "I love you", "Seni seviyorum", "Te amo", "Je t'aime",
    "Ich liebe dich", "Ti amo", "Eu te amo", "Я тебя люблю",
    "사랑해", "愛してる", "我爱你", "मैं तुमसे प्यार करता हूँ",
    "Σ' αγαπώ", "Ik hou van jou", "Jag älskar dig", "Kocham cię",
    "ฉันรักเธอ", "Anh yêu em", "Aku cinta kamu", "Я тебе кохаю",
]

app = FastAPI(title="Love Heart", version="1.0.0")


def heart(a: float) -> tuple[float, float]:
    x = 16 * (math.sin(a) ** 3)
    y = (
        13 * math.cos(a)
        - 5 * math.cos(2 * a)
        - 2 * math.cos(3 * a)
        - math.cos(4 * a)
    )
    return x * SC, y * SC + OY


def hx(c: tuple[float, float, float]) -> str:
    return "#%02x%02x%02x" % tuple(
        int(max(0, min(1, v)) * 255) for v in c
    )


def mix(a: tuple[float, ...], b: tuple[float, ...], k: float) -> tuple[float, ...]:
    k = max(0.0, min(1.0, k))
    return tuple(p + (q - p) * k for p, q in zip(a, b))


def estimate_text_width(text: str, size: int) -> float:
    """Estimate bold font width in SVG user units without OS-specific Tk fonts."""
    total = 0.0
    for ch in text:
        cat = unicodedata.category(ch)
        if cat in {"Mn", "Me", "Cf"}:  # combining marks / formatting chars
            factor = 0.0
        elif ch.isspace():
            factor = 0.34
        elif unicodedata.east_asian_width(ch) in {"W", "F"}:
            factor = 1.0
        elif cat.startswith("P"):
            factor = 0.34 if ch in "'’`.,:;!|" else 0.48
        elif ch.isupper():
            factor = 0.69
        elif ch.isdigit():
            factor = 0.59
        elif "DEVANAGARI" in unicodedata.name(ch, "") or "THAI" in unicodedata.name(ch, ""):
            factor = 0.66
        else:
            factor = 0.56
        total += factor * size
    return total


POLY = [heart(2 * math.pi * i / 720) for i in range(720)]
EDGES = list(zip(POLY, POLY[1:] + POLY[:1]))
YMAX = max(p[1] for p in POLY)
YMIN = min(p[1] for p in POLY)
CY = (YMAX + YMIN) / 2


def spans(y: float) -> list[tuple[float, float]]:
    xs: list[float] = []
    for (x1, y1), (x2, y2) in EDGES:
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2]))


def intersect(a_spans: list[tuple[float, float]], b_spans: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out = []
    for a in a_spans:
        for b in b_spans:
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi - lo > 14:
                out.append((lo, hi))
    return out


def phrase_cycle(rng: random.Random):
    while True:
        order = PHRASES[:]
        rng.shuffle(order)
        yield from order


def math_dist(x: float, y: float) -> float:
    return math.hypot(x / (16 * SC), (y - CY) / (14.5 * SC))


def build_layout() -> list[dict[str, Any]]:
    rng = random.Random(11)
    cycle = phrase_cycle(rng)
    # Tk's platform-dependent font metrics are replaced by a close SVG-friendly estimate.
    row_h = max(max(SIZES) * 1.42, 17) + 4
    half = row_h / 2
    placed: list[dict[str, Any]] = []
    y = YMAX - half
    while y > YMIN + half:
        row = intersect(spans(y + half), spans(y - half))
        for lo, hi in row:
            lo += 4
            hi -= 4
            cur = lo + rng.uniform(0, 8)
            line: list[list[Any]] = []
            while True:
                fit = None
                for _ in range(10):
                    text = next(cycle)
                    size = rng.choice(SIZES)
                    width = estimate_text_width(text, size)
                    if cur + width <= hi:
                        fit = (text, size, width)
                        break
                if not fit:
                    break
                phrase, size, width = fit
                line.append([cur + width / 2, phrase, size, width])
                cur += width + GAP
            if not line:
                continue
            if len(line) > 1:
                left = hi - (line[-1][0] + line[-1][3] / 2)
                for i, item in enumerate(line):
                    item[0] += left * i / (len(line) - 1)
            else:
                line[0][0] = (lo + hi) / 2
            for i, (x, phrase, size, _width) in enumerate(line):
                placed.append({"x": x, "y": y, "text": phrase, "size": size,
                               "edge": i == 0 or i == len(line) - 1})
        y -= row_h

    for p in placed:
        rad = min(1.0, math_dist(p["x"], p["y"]))
        base = mix(WINE, CRIMSON, 0.25 + 0.75 * rad)
        base = mix(base, BLOOD, rng.uniform(0, 0.35) + (0.3 if p["edge"] else 0))
        p["color"] = hx(tuple(min(1, v) for v in base))
        p["rad"] = rad
        p["dx"] = rng.uniform(-10, 10)

    edges = [p for p in placed if p["edge"]]
    inner = [p for p in placed if not p["edge"]]
    edges.sort(key=lambda p: math.atan2(p["x"], p["y"] - CY) % (2 * math.pi))
    inner.sort(key=lambda p: -p["rad"] + rng.uniform(0, 0.08))
    return edges + inner


def build_svg() -> tuple[str, int]:
    items = build_layout()
    count = len(items)
    if not count:
        return '<svg viewBox="0 0 800 800" role="img" aria-label="Love heart"></svg>', 0

    parts = [
        '<svg class="heart-art" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" '
        'role="img" aria-label="A heart formed from love phrases in many languages">',
        f'<rect width="800" height="800" fill="{BG}"/>',
        '<g font-family="Arial, Helvetica, sans-serif" font-weight="700" text-anchor="middle" '
        'dominant-baseline="middle" paint-order="stroke fill">',
    ]
    for i, p in enumerate(items):
        x = 400 + p["x"]
        final_y = 400 - p["y"]
        # Small random horizontal drift and vertical lift echo the original Turtle animation.
        delay = (i / max(1, count - 1)) * DURATION
        start_y = final_y + LIFT
        color = p["color"]
        phrase = html.escape(p["text"], quote=False)
        size = p["size"]
        shimmer_delay = 12.3 + (i % 31) * 0.13
        dx = p["dx"]
        parts.append(
            f'<text x="{x:.2f}" y="{start_y:.2f}" fill="{BG}" opacity="0" '
            f'font-size="{size}" stroke="{BG}" stroke-width="0.25" '
            f'style="filter:drop-shadow(1.5px 2px 0px {BG})">{phrase}'
            f'<animate attributeName="x" from="{x + dx:.2f}" to="{x:.2f}" '
            f'dur="0.72s" begin="{delay:.3f}s" fill="freeze" calcMode="spline" '
            f'keyTimes="0;1" keySplines="0.2 0.8 0.2 1" />'
            f'<animate attributeName="y" from="{start_y:.2f}" to="{final_y:.2f}" '
            f'dur="0.72s" begin="{delay:.3f}s" fill="freeze" calcMode="spline" '
            f'keyTimes="0;1" keySplines="0.2 0.8 0.2 1" />'
            f'<animate attributeName="opacity" from="0" to="1" dur="0.58s" '
            f'begin="{delay:.3f}s" fill="freeze" />'
            f'<animate attributeName="fill" from="{BG}" to="{color}" dur="0.9s" '
            f'begin="{delay:.3f}s" fill="freeze" />'
            f'<animate attributeName="fill" values="{color};#ffc3cf;{color}" '
            f'dur="2.9s" begin="{shimmer_delay:.2f}s" repeatCount="indefinite" />'
            '</text>'
        )
    parts.extend(['</g>', '</svg>'])
    return "\n".join(parts), count


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    svg, count = build_svg()
    page = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="{BG}">
  <meta name="description" content="A glowing heart formed from I love you in languages around the world.">
  <title>Love Heart ❤️</title>
  <style>
    :root {{ color-scheme: dark; --bg: {BG}; }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; min-height: 100%; background: var(--bg); }}
    body {{ min-height: 100svh; display: flex; justify-content: center; align-items: center;
           overflow-x: hidden; color: #f8eaf0;
           font-family: Arial, Helvetica, sans-serif; }}
    main {{ width: min(100%, 900px); min-height: 100svh; padding: max(14px, env(safe-area-inset-top)) 12px max(18px, env(safe-area-inset-bottom));
            display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; }}
    h1 {{ margin: 0; font-size: clamp(13px, 2.3vw, 17px); font-weight: 700; letter-spacing: .26em;
          text-align: center; color: #f8c5d0; opacity: .88; }}
    .subtitle {{ margin: 0; color: #bda5b3; font-size: 12px; text-align: center; letter-spacing: .04em; }}
    .heart-art {{ display: block; width: min(100%, 800px, 88svh); height: auto; max-height: 82svh; overflow: visible; }}
    .controls {{ display: flex; justify-content: center; padding-top: 2px; }}
    button {{ border: 1px solid #7f344c; background: #1b0913; color: #f9d6df; border-radius: 999px;
              font: inherit; font-size: 13px; padding: 10px 18px; min-height: 42px; cursor: pointer;
              -webkit-tap-highlight-color: transparent; }}
    button:focus-visible {{ outline: 2px solid #ff9eb8; outline-offset: 3px; }}
    button:active {{ transform: scale(.98); }}
    @media (max-width: 480px) {{ main {{ gap: 7px; }} .heart-art {{ width: min(100%, 90svh); max-height: 78svh; }} }}
    @media (prefers-reduced-motion: reduce) {{ button {{ transition: none; }} }}
  </style>
</head>
<body>
  <main>
    <h1>LOVE, IN EVERY LANGUAGE</h1>
    <p class="subtitle">One heart. So many ways to say it.</p>
    {svg}
    <div class="controls"><button type="button" onclick="window.location.reload()">Replay animation ↻</button></div>
  </main>
</body>
</html>'''
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


@app.get("/healthz", response_class=JSONResponse)
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/info", response_class=JSONResponse)
def info() -> dict[str, Any]:
    """Small optional endpoint for verifying the Python service is live."""
    _svg, count = build_svg()
    return {"app": "Love Heart", "status": "ok", "phrases": len(PHRASES), "placed_texts": count}
