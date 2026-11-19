"""Builds apps/: one small launcher page per Cadence app, so each can sit on the iPhone Home Screen with its own icon and name.
A launcher opens its part of Cadence on claude.ai at once. Opened with #add, it stays put and shows how to add it instead.
Icons come from the Cadence repo (../Cadence/icons, the same art as the Mac Dock apps).
Usage: python3 tools/make_launchers.py"""
import html, json, os
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), '..')
ICONS = os.path.join(ROOT, '..', 'Cadence', 'icons')
OUT = os.path.join(ROOT, 'apps')
CADENCE = 'https://claude.ai/artifact/JCcrHbJtuJMPXvsqPoTBSy'
APPS = [  # slug, name, icon file, where it opens
    ('cadence', 'Cadence', 'cadence', CADENCE),
    ('calendar', 'Calendar', 'cadence-calendar', CADENCE + '#calendar-app'),
    ('mail', 'Mail', 'cadence-mail', CADENCE + '#mail-app'),
    ('reminders', 'Reminders', 'cadence-reminders', CADENCE + '#reminders-app'),
    ('pulse', 'Pulse', 'cadence-progress', CADENCE + '#progress-app'),
    ('habits', 'Habits', 'cadence-habits', CADENCE + '#habits-app'),
    ('finance', 'Finance', 'cadence-money', CADENCE + '#money-app'),
    ('news', 'News', 'cadence-news', CADENCE + '#news-app'),
    ('cosmos', 'Cosmos', 'cadence-cosmos', CADENCE + '#cosmos-app'),
    ('halsotranaren', 'Hälsotränaren', 'halsotranaren', 'https://claude.ai/artifact/4nv5dE8WseyHNCYh7heAhT'),
]

STYLE = """:root{--paper:#F4F5F1;--ink:#1C2629;--soft:#5d6a6d;--sun:#E59A2F;--card:#fff}
@media (prefers-color-scheme:dark){:root{--paper:#101618;--ink:#E6ECEA;--soft:#9aa8a6;--card:#172022}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.5 -apple-system,system-ui,sans-serif;padding:max(24px,env(safe-area-inset-top)) 16px 32px}
main{max-width:460px;margin:0 auto}h1{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:28px;margin:8px 0 4px}
p,li{color:var(--soft)}a{color:inherit}.card{background:var(--card);border-radius:18px;padding:16px 18px;margin:16px 0}
.app{display:flex;align-items:center;gap:14px;padding:10px 0;text-decoration:none;color:var(--ink)}
.app img{width:52px;height:52px;border-radius:12px}.app span{flex:1;font-weight:600}.app em{font-style:normal;color:var(--sun);font-size:15px}
.big{width:96px;height:96px;border-radius:22px;display:block;margin:8px 0 12px}b{color:var(--ink)}"""

STEPS = """<ol><li>Tap the Share button in Safari.</li><li>Choose <b>Add to Home Screen</b>.</li>
<li>If you see <b>Open as Web App</b>, turn it off. Then Cadence opens in Safari, where you are already signed in to Claude.</li>
<li>Tap <b>Add</b>.</li></ol>"""


def page(slug, name, icon, url):
    n = html.escape(name)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{n}</title>
<meta name="apple-mobile-web-app-title" content="{n}">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#101618">
<script>
  // Launched from the Home Screen: go straight to Cadence. Opened with #add: stay and explain, and drop #add
  // so the Home Screen saves the plain address.
  if (location.hash !== '#add') location.replace({json.dumps(url)});
  else history.replaceState(null, '', location.pathname);
</script>
<style>{STYLE}</style></head>
<body><main>
<img class="big" src="icon-180.png" alt="">
<h1>{n}</h1>
<p>Add {n} to your Home Screen. It opens this part of Cadence.</p>
<div class="card">{STEPS}</div>
<p><a href="{html.escape(url)}">Open {n} now</a> · <a href="../">All Cadence apps</a></p>
</main></body></html>
"""


def index():
    rows = ''.join(f'<a class="app" href="{s}/#add"><img src="{s}/icon-180.png" alt=""><span>{html.escape(n)}</span><em>Add</em></a>'
                   for s, n, _, _ in APPS)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Cadence apps</title>
<link rel="icon" href="cadence/icon-192.png">
<meta name="theme-color" content="#101618">
<style>{STYLE}</style></head>
<body><main>
<h1>Cadence apps</h1>
<p>Put each part of Cadence on your Home Screen with its own icon, like the apps in the Mac Dock. Open this page in Safari on your iPhone, tap an app, then add it.</p>
<div class="card">{rows}</div>
<p>They open Cadence on claude.ai, so whatever Claude changes there shows up at once.</p>
<h1 style="font-size:22px;margin-top:28px">Full screen, without Safari's bars</h1>
<p>A profile adds the apps as full-screen web clips with the same icons. It holds only the ten names, addresses and icons.</p>
<div class="card"><ol><li>Tap a link below and choose <b>Allow</b>.</li><li>Open <b>Settings</b>, tap <b>Profile Downloaded</b>, then <b>Install</b>. iPhone says the profile is not signed; that is expected for one you made yourself.</li><li>The first time you open each app, sign in to Claude in it.</li></ol>
<p><a href="https://bttliinpthrngngohbcv.supabase.co/functions/v1/push?action=profile&amp;name=test">Try one first: Habits</a><br><a href="https://bttliinpthrngngohbcv.supabase.co/functions/v1/push?action=profile&amp;name=apps">All ten apps</a></p></div>
<p>To remove them: Settings, General, VPN &amp; Device Management, the profile, Remove Profile.</p>
</main></body></html>
"""


os.makedirs(OUT, exist_ok=True)
for slug, name, icon, url in APPS:
    d = os.path.join(OUT, slug); os.makedirs(d, exist_ok=True)
    im = Image.open(os.path.join(ICONS, icon + '.png')).convert('RGB')
    for s in (180, 192, 512):
        im.resize((s, s), Image.LANCZOS).save(os.path.join(d, f'icon-{s}.png'), optimize=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f: f.write(page(slug, name, icon, url))
    man = {'name': name, 'short_name': name, 'start_url': './', 'scope': './', 'display': 'browser',
           'background_color': '#101618', 'theme_color': '#101618',
           'icons': [{'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                     {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]}
    with open(os.path.join(d, 'manifest.webmanifest'), 'w', encoding='utf-8') as f: json.dump(man, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f: f.write(index())
print('built', len(APPS), 'launchers in', os.path.abspath(OUT))
