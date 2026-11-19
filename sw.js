// Cadence Alerts service worker: shows pushed notifications and opens the right part of Cadence when one is tapped.
const APP_URL = 'https://claude.ai/artifact/JCcrHbJtuJMPXvsqPoTBSy';
// On the Mac mini a small helper (~/.cadence-alerts/opener.py) listens here and brings up the matching Dock app.
const MAC_OPENER = 'http://127.0.0.1:8799/open?url=';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

self.addEventListener('push', (e) => {
  let m = {};
  try { m = e.data ? e.data.json() : {}; } catch { m = { body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(m.title || 'Cadence', {
    body: m.body || '',
    tag: m.tag || undefined,
    icon: 'icons/icon-192.png',
    badge: 'icons/icon-192.png',
    data: { url: m.url || APP_URL },
  }));
});

const isMac = /Macintosh/.test(self.navigator.userAgent) && !(self.navigator.maxTouchPoints > 1);

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || APP_URL;
  e.waitUntil((async () => {
    if (isMac && url.startsWith('https://claude.ai/artifact/')) {
      // Ask the helper to open the Dock app; if it is not running, fall back to a browser tab.
      try {
        const r = await fetch(MAC_OPENER + encodeURIComponent(url), { mode: 'no-cors', cache: 'no-store', targetAddressSpace: 'loopback' });
        if (r) return;
      } catch (err) { /* helper not running */ }
      return self.clients.openWindow(url);
    }
    // iPhone: a Home Screen app cannot open another one, and it ignores addresses outside Alerts.
    // So open Alerts itself with ?open=, and let the page go on to that part of Cadence.
    const target = './?open=' + encodeURIComponent(url);
    const wins = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const w of wins) {
      if ('navigate' in w) { try { await w.navigate(target); return w.focus(); } catch (err) { /* try the next */ } }
    }
    return self.clients.openWindow(target);
  })());
});
