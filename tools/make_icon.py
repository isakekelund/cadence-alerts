"""Draws the Cadence Alerts icon in the Cadence icon theme (same ground, line weight and sun dot as Cadence/tools/make_icons.py): a bell whose clapper is the sun.
Usage: python3 tools/make_icon.py  -> icons/icon-512.png, icon-192.png, apple-touch-icon.png"""
from PIL import Image, ImageDraw
import os
S = 4; N = 1024 * S
PAPER, SUN, W = (244, 245, 241, 255), (240, 174, 74, 255), 54
TOP, BOT = (40, 55, 60), (17, 24, 26)
OUT = os.path.join(os.path.dirname(__file__), '..', 'icons')

def ground():
    px = Image.linear_gradient('L').resize((N, N))
    im = Image.composite(Image.new('RGBA', (N, N), BOT + (255,)), Image.new('RGBA', (N, N), TOP + (255,)), px)
    hill = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(hill).ellipse([-300 * S, 800 * S, 1324 * S, 1700 * S], fill=(244, 245, 241, 14))
    return Image.alpha_composite(im, hill)
def line(d, pts, w=W, fill=PAPER):
    pts = [(x * S, y * S) for x, y in pts]
    d.line(pts, fill=fill, width=w * S, joint='curve')
    for x, y in pts: d.ellipse([x - w * S / 2, y - w * S / 2, x + w * S / 2, y + w * S / 2], fill=fill)
def dot(d, x, y, r, fill=SUN): d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=fill)

im = ground(); d = ImageDraw.Draw(im)
d.arc([332 * S, 272 * S, 692 * S, 632 * S], 180, 360, fill=PAPER, width=W * S)   # dome
line(d, [(359, 452), (359, 602), (292, 672)])                                       # left side and flare
line(d, [(665, 452), (665, 602), (732, 672)])                                       # right side and flare
line(d, [(292, 672), (732, 672)])                                                   # rim
line(d, [(512, 212), (512, 262)])                                                   # handle
dot(d, 512, 772, 70)                                                                # the sun as clapper
im = im.resize((1024, 1024), Image.LANCZOS).convert('RGB')
os.makedirs(OUT, exist_ok=True)
for n, s in [('icon-512', 512), ('icon-192', 192), ('apple-touch-icon', 180)]:
    im.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, n + '.png'))
