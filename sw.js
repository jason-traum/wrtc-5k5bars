/* 5K 5 Bars service worker.
   The page itself: network first, so a new version shows up on the next open; the saved copy only when there's no signal.
   Pinned libraries and fonts: cache first (their URLs carry exact versions).
   Map tiles, map fonts and the tile index: cache first in their own cache, capped, so streets you've looked at
   still draw with no signal.
   Supabase (the race data): never cached here. Taps made offline wait in the page's own queue. */
const VERSION = 'race-2026-10-01a';
const TILES = 'map-tiles-v1', TILE_CAP = 600;
const SHELL = ['./', './index.html', './about.html', './config.js', './manifest.json', './apple-touch-icon.png', './icon-192.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION && k !== TILES).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.hostname.endsWith('.supabase.co')) return;

  if (url.hostname === 'tiles.openfreemap.org') {
    e.respondWith(caches.open(TILES).then(c => c.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok) { c.put(req, res.clone()); c.keys().then(k => { if (k.length > TILE_CAP) k.slice(0, k.length - TILE_CAP).forEach(x => c.delete(x)); }); }
      return res;
    }))));
    return;
  }
  const pinned = url.hostname === 'cdn.jsdelivr.net' || url.hostname === 'cdnjs.cloudflare.com' || url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com';
  if (pinned) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok || res.type === 'opaque') { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
      return res;
    })));
    return;
  }

  if (url.origin === self.location.origin) {
    e.respondWith(fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req).then(hit => hit || (req.mode === 'navigate' ? caches.match('./index.html') : Response.error()))));
  }
});
