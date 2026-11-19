// Cadence Alerts service worker: shows pushed notifications and opens Cadence when one is tapped.
const APP_URL = 'https://claude.ai/artifact/JCcrHbJtuJMPXvsqPoTBSy';

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

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || APP_URL;
  e.waitUntil((async () => {
    const wins = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const w of wins) {
      if (w.url === url && 'focus' in w) return w.focus();
    }
    return self.clients.openWindow(url);
  })());
});
