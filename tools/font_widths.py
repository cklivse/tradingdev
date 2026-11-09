"""Write per-character advance widths (in em) for the characters of a deck.
Usage: python font_widths.py slides.md out.json"""
import json, subprocess, sys
from PIL import ImageFont

def path(pattern):
    return subprocess.check_output(["fc-match", "-f", "%{file}", pattern], text=True)

def index(pattern):
    return int(subprocess.check_output(["fc-match", "-f", "%{index}", pattern], text=True) or 0)

text = open(sys.argv[1], encoding="utf-8").read()
chars = sorted(set(text) - {"\n", "\r"})
SIZE = 1000
out = {}
for key, pattern in {"sans": "Noto Sans CJK TC:regular", "bold": "Noto Sans CJK TC:bold", "mono": "Liberation Mono"}.items():
    font = ImageFont.truetype(path(pattern), SIZE, index=index(pattern))
    out[key] = {ch: round(font.getlength(ch) / SIZE, 4) for ch in chars}
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
print(len(chars), "chars;", {k: out[k].get("A") for k in out}, {k: out[k].get("中") for k in out})
