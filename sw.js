// Cadence Alerts service worker: shows pushed notifications and opens the right part of Cadence when one is tapped.
const VERSION = '6';
const APP_URL = 'https://claude.ai/artifact/JCcrHbJtuJMPXvsqPoTBSy';
// On the Mac mini a small helper (~/.cadence-alerts/opener.py) listens here and brings up the matching Dock app.
const MAC_OPENER = 'http://127.0.0.1:8799/open?url=';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil((async () => {
  // Leave the version where the page can read it, for the footer's diagnostic line.
  await (await caches.open('alerts')).put('sw-version', new Response(VERSION));
  await self.clients.claim();
})()));

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

// The page asks which version is running, to show it in its footer.
self.addEventListener('message', (e) => {
  if (e.data && e.data.ask === 'version' && e.source) e.source.postMessage({ version: VERSION });
});

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
    // iPhone: a Home Screen app cannot open another one, and iOS often just brings Alerts forward without
    // following an address. So leave the address where the page looks for it (it checks whenever it is shown),
    // tell any open page directly, and open Alerts.
    const cache = await caches.open('alerts');
    await cache.put('pending-open', new Response(JSON.stringify({ url, at: Date.now() })));
    await cache.put('last-tap', new Response(JSON.stringify({ url, at: Date.now(), v: VERSION })));
    const wins = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const w of wins) { try { w.postMessage({ open: url }); } catch (err) { /* ignore */ } }
    if (wins.length) { try { return await wins[0].focus(); } catch (err) { /* fall through */ } }
    return self.clients.openWindow('./?open=' + encodeURIComponent(url));
  })());
});
