# Builds two outputs from index.html:
#   dist/site/            - what GitHub Pages serves (index.html loads config.js -> Supabase; no config.js -> demo)
#   dist/preview.html     - claude.ai artifact preview (no config -> demo mode, simulated runners and GPS)
import re, os
s = open('index.html').read()
os.makedirs('dist/site', exist_ok=True)
open('dist/site/index.html', 'w').write(s)
head = re.search(r'<head>(.*?)</head>', s, re.S).group(1)
body = re.search(r'<body>(.*?)</body>', s, re.S).group(1)
head = re.sub(r'<meta[^>]*>\n?', '', head)
head = re.sub(r'<link rel="(manifest|apple-touch-icon)"[^>]*>\n?', '', head)
body = body.replace('<script src="config.js"></script>', '')
open('dist/preview.html', 'w').write(head.strip() + '\n' + body.strip() + '\n')
import shutil
for f in ['about.html', 'manifest.json', 'sw.js', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png']:
    shutil.copy(f, 'dist/site/' + f)
if os.path.exists('config.js'):
    shutil.copy('config.js', 'dist/site/config.js')
print('built', len(s))
