"""Downloads the archive photos (Wikimedia Commons) and makes two WebP widths of each.

python -I tools/photos.py   (from the project root; needs ffmpeg with libwebp)
Writes assets/img/arsiv/<id>-<w>.webp and tools/out/photos-local.json.
"""
import json, os, subprocess, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'research', 'photo-src')
OUT = os.path.join(ROOT, 'assets', 'img', 'arsiv')
os.makedirs(SRC, exist_ok=True); os.makedirs(OUT, exist_ok=True)
data = json.load(open(os.path.join(ROOT, 'research', 'photos.json'), encoding='utf-8'))
photos = data['photos'] if isinstance(data, dict) else data
BIG = {'p03'}          # the lead photo gets the larger source
WIDTHS = (1280, 640)

local = {}
for p in photos:
    url = p['url_1600'] if p['id'] in BIG else (p.get('url_1280') or p['url_1600'])
    ext = os.path.splitext(url.split('?')[0])[1].lower() or '.jpg'
    raw = os.path.join(SRC, p['id'] + ext)
    if not os.path.exists(raw):
        for attempt in range(6):                 # Commons rate-limits bursts: back off and retry
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'TakTek-prototype/1.0 (archive photos, credited)'})
                body = urllib.request.urlopen(req, timeout=90).read()
                open(raw, 'wb').write(body)
                break
            except urllib.error.HTTPError as ex:
                if ex.code != 429 or attempt == 5:
                    raise
                time.sleep(8 * (attempt + 1))
        time.sleep(2.5)
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', raw],
                           capture_output=True, text=True).stdout.strip().split(',')
    sw, sh = int(probe[0]), int(probe[1])
    made = []
    for w in WIDTHS:
        if w > sw and w != WIDTHS[-1]:
            continue
        tw = min(w, sw)
        th = round(sh * tw / sw / 2) * 2
        dst = os.path.join(OUT, f"{p['id']}-{tw}.webp")
        if not os.path.exists(dst):
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-vf', f'scale={tw}:{th}:flags=lanczos', '-c:v', 'libwebp', '-quality', '76', '-compression_level', '6', dst], check=True)
        made.append((tw, th, f"assets/img/arsiv/{p['id']}-{tw}.webp"))
    made.sort(reverse=True)
    w0, h0, src0 = made[0]
    local[p['id']] = {'src': src0, 'w': w0, 'h': h0, 'srcset': ', '.join(f'{s} {w}w' for w, h, s in made)}
    print(p['id'], sw, 'x', sh, '->', [m[0] for m in made])
json.dump(local, open(os.path.join(ROOT, 'tools', 'out', 'photos-local.json'), 'w', encoding='utf-8'), indent=1)
