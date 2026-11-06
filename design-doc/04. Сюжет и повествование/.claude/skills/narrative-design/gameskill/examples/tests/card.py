#!/usr/bin/env python3
"""Render the check output as a PNG (the page screenshot). Needs Pillow.
Usage: python3 tests/card.py <title> <out.png> -- <command...>"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont

title, out = sys.argv[1], sys.argv[2]
cmd = sys.argv[sys.argv.index("--") + 1:]
res = subprocess.run(cmd, capture_output=True, text=True)
lines = [l for l in res.stdout.splitlines() if l.startswith(("PASS", "FAIL", "INFO", "RESULT"))]
font = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", s)
W, lh = 1200, 22
H = 90 + lh * len(lines) + 30
img = Image.new("RGB", (W, H), (22, 24, 30))
d = ImageDraw.Draw(img)
d.text((30, 24), title, fill=(240, 240, 240), font=font(26))
y = 80
for l in lines:
    col = {"PASS": (110, 210, 130), "FAIL": (240, 100, 100), "INFO": (150, 170, 220), "RESULT": (250, 210, 90)}[l.split()[0]]
    if len(l) > 98:
        l = l[:95] + "..."
    d.text((30, y), l, fill=col, font=font(16))
    y += lh
img.save(out)
print("SCREENSHOT", out)
