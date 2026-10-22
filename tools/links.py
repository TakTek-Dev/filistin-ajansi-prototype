"""Checks every internal link, image and anchor in the generated pages.

python -I tools/links.py   (from the project root, after tools/pages.py)
Resolves relative paths per page, maps the absolute /filistin-ajansi-prototype/ paths of 404.html to the root,
and checks that #fragments exist in their target page. Exits 1 when anything is broken.
"""
import glob, os, re, sys
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = '/filistin-ajansi-prototype/'
pages = sorted(glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, 'haber', '*.html')))
ids_cache = {}

def ids(path):
    if path not in ids_cache:
        ids_cache[path] = set(re.findall(r'\sid="([^"]+)"', open(path, encoding='utf-8').read()))
    return ids_cache[path]

broken, checked = [], 0
for page in pages:
    html = open(page, encoding='utf-8').read()
    refs = re.findall(r'\s(?:href|src)="([^"]+)"', html)
    for ss in re.findall(r'\ssrcset="([^"]+)"', html):
        refs += [part.strip().split(' ')[0] for part in ss.split(',')]
    for ref in refs:
        if re.match(r'^(https?:|mailto:|tel:|data:|javascript:)', ref):
            continue
        checked += 1
        u = urlsplit(ref)
        if u.path.startswith(SITE):
            target = os.path.join(ROOT, *unquote(u.path[len(SITE):]).split('/'))
        elif u.path:
            target = os.path.normpath(os.path.join(os.path.dirname(page), unquote(u.path)))
        else:
            target = page
        if os.path.isdir(target):
            target = os.path.join(target, 'index.html')
        rel = os.path.relpath(page, ROOT)
        if not os.path.exists(target):
            broken.append(f'{rel}: missing {ref}')
            continue
        if u.fragment and target.endswith('.html') and u.fragment not in ids(target):
            broken.append(f'{rel}: no #{u.fragment} in {os.path.relpath(target, ROOT)}')

print(f'{len(pages)} pages, {checked} internal references, {len(broken)} broken')
for x in broken[:60]:
    print('  ' + x)
sys.exit(1 if broken else 0)
