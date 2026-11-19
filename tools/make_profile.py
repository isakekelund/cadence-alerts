"""Builds apps/*.mobileconfig: iPhone configuration profiles that put the Cadence apps on the Home Screen as
full-screen web clips, each with its own icon and name, opening its part of Cadence on claude.ai without Safari's bars.
(A page added with Share > Add to Home Screen can only use the icon of the site it is on; a web clip in a profile
carries its own icon.) A profile holds nothing but web clips: a name, an address and an icon each.
  apps/cadence-apps.mobileconfig   all ten apps
  apps/cadence-test.mobileconfig   Habits only, to try it first
The ids are stable, so installing a newer build replaces the old clips instead of adding doubles.
Usage: python3 tools/make_profile.py  (also rebuilds the launcher pages, which it shares its app list with)"""
import io, os, plistlib, uuid
from PIL import Image
from make_launchers import APPS, ICONS, OUT

NS = uuid.uuid5(uuid.NAMESPACE_URL, 'https://isakekelund.github.io/cadence-alerts/apps/')
BASE = 'io.github.isakekelund.cadence'


def icon(name):
    im = Image.open(os.path.join(ICONS, name + '.png')).convert('RGB').resize((180, 180), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True); return b.getvalue()


def clip(slug, name, icon_name, url):
    return {
        'PayloadType': 'com.apple.webClip.managed', 'PayloadVersion': 1,
        'PayloadIdentifier': f'{BASE}.clip.{slug}', 'PayloadUUID': str(uuid.uuid5(NS, 'clip:' + slug)).upper(),
        'PayloadDisplayName': name, 'Label': name, 'URL': url, 'Icon': icon(icon_name),
        'FullScreen': True, 'IgnoreManifestScope': True, 'Precomposed': True, 'IsRemovable': True,
    }


def profile(kind, title, desc, apps):
    return {
        'PayloadType': 'Configuration', 'PayloadVersion': 1,
        'PayloadIdentifier': f'{BASE}.{kind}', 'PayloadUUID': str(uuid.uuid5(NS, 'profile:' + kind)).upper(),
        'PayloadDisplayName': title, 'PayloadDescription': desc, 'PayloadOrganization': 'Cadence',
        'PayloadContent': [clip(*a) for a in apps],
    }


def write(file, p):
    with open(os.path.join(OUT, file), 'wb') as f: plistlib.dump(p, f)
    print(file, os.path.getsize(os.path.join(OUT, file)) // 1024, 'KB,', len(p['PayloadContent']), 'web clips')


write('cadence-apps.mobileconfig', profile('apps', 'Cadence apps',
      'Adds the Cadence apps to the Home Screen: ten web clips, each with its own icon. Nothing else.', APPS))
write('cadence-test.mobileconfig', profile('test', 'Cadence test (Habits)',
      'Adds one web clip, Habits, to the Home Screen. Nothing else.', [a for a in APPS if a[0] == 'habits']))
