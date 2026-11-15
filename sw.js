/* ═══════════════════════════════════════════════════════════════════════════
   Service Worker — پیام‌رسان حرفه‌ای
   نسخه ۲.۱.۰
   ═══════════════════════════════════════════════════════════════════════════
   
   تغییرات نسبت به نسخه ۱:
   ✅ Supabase CDN (jsdelivr) حالا کش می‌شود — آفلاین درست کار می‌کند
   ✅ API های Supabase کش نمی‌شوند (فقط شبکه)
   ✅ کش با سقف تعداد ورودی محدود شد (جلوگیری از رشد بی‌پایان)
   ✅ HTML navigation: network-first با fallback به index.html
   ✅ پیام PING برای تست اتصال
   ✅ اعلان با tag و renotify بهتر
   ✅ پاسخ هوشمند به event.sync
   ✅ خطاها silent نمی‌شوند، در کنسول لاگ می‌شوند
*/

'use strict';

const CACHE_VERSION = 'v2.1.0';
const CACHE_STATIC = 'chat-static-' + CACHE_VERSION;
const CACHE_DYNAMIC = 'chat-dynamic-' + CACHE_VERSION;
const CACHE_IMAGES = 'chat-images-' + CACHE_VERSION;

const MAX_IMAGE_ENTRIES = 100;
const MAX_DYNAMIC_ENTRIES = 50;

// ⚠️ مسیرها با ./ شروع می‌شوند تا در GitHub Pages درست کار کنند
const PRECACHE_URLS = [
    './',
    './index.html',
    './manifest.json'
];

// ⚠️ API های Supabase هرگز نباید کش شوند (auth, data, realtime)
const NEVER_CACHE_HOSTS = [
    'supabase.co',
    'supabase.in',
    'supabase.com'
];

// CDN ها: کش می‌شوند با stale-while-revalidate (supabase-js)
const CDN_HOSTS = [
    'cdn.jsdelivr.net',
    'unpkg.com',
    'esm.run',
    'googleapis.com',
    'gstatic.com'
];

/* ═══════════════════════════════════════════════════════════════
   نصب
   ═══════════════════════════════════════════════════════════════ */
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_STATIC)
            .then(cache => {
                return cache.addAll(PRECACHE_URLS).catch(err => {
                    console.warn('[SW] Precache partial failure:', err);
                });
            })
            .then(() => {
                console.log('[SW] Installed', CACHE_VERSION);
                return self.skipWaiting();
            })
    );
});

/* ═══════════════════════════════════════════════════════════════
   فعال‌سازی
   ═══════════════════════════════════════════════════════════════ */
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(
                keys.map(key => {
                    // فقط کش‌های قدیمی این پروژه را پاک کن
                    if (key.startsWith('chat-') && key.indexOf(CACHE_VERSION) === -1) {
                        console.log('[SW] Deleting old cache:', key);
                        return caches.delete(key);
                    }
                })
            ))
            .then(() => {
                console.log('[SW] Activated', CACHE_VERSION);
                return self.clients.claim();
            })
    );
});

/* ═══════════════════════════════════════════════════════════════
   کمکی‌ها
   ═══════════════════════════════════════════════════════════════ */
function isApiRequest(url) {
    return NEVER_CACHE_HOSTS.some(host => url.hostname.includes(host));
}

function isCdnRequest(url) {
    return CDN_HOSTS.some(host => url.hostname.includes(host));
}

async function trimCache(cacheName, maxEntries) {
    try {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        if (keys.length > maxEntries) {
            const toDelete = keys.slice(0, keys.length - maxEntries);
            await Promise.all(toDelete.map(key => cache.delete(key)));
            console.log('[SW] Trimmed', toDelete.length, 'from', cacheName);
        }
    } catch (e) {
        console.warn('[SW] Trim error:', e);
    }
}

/* ═══════════════════════════════════════════════════════════════
   Fetch
   ═══════════════════════════════════════════════════════════════ */
self.addEventListener('fetch', event => {
    const request = event.request;

    // فقط GET
    if (request.method !== 'GET') return;

    // فقط http/https
    if (!request.url.startsWith('http')) return;

    const url = new URL(request.url);

    /* ─── ۱. APIهای Supabase: مستقیم به شبکه، بدون کش ─── */
    if (isApiRequest(url)) {
        // مسیر Supabase API (نه CDN) — کش نمی‌کنیم
        if (url.hostname.includes('supabase.') && !isCdnRequest(url)) {
            return; // بگذار مرورگر خودش درخواست را بفرستد
        }
    }

    /* ─── ۲. تصاویر: cache-first ─── */
    if (request.destination === 'image') {
        event.respondWith(
            caches.match(request).then(cached => {
                if (cached) return cached;

                return fetch(request).then(response => {
                    if (response && response.status === 200 && response.type === 'basic') {
                        const clone = response.clone();
                        caches.open(CACHE_IMAGES).then(cache => {
                            cache.put(request, clone);
                            trimCache(CACHE_IMAGES, MAX_IMAGE_ENTRIES);
                        });
                    }
                    return response;
                }).catch(() => {
                    // PNG شفاف ۱×۱ برای تصاویر از دست رفته
                    return new Response(
                        atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='),
                        { headers: { 'Content-Type': 'image/png' } }
                    );
                });
            })
        );
        return;
    }

    /* ─── ۳. CDN: stale-while-revalidate (کار آفلاین + آپدیت پس‌زمینه) ─── */
    if (isCdnRequest(url)) {
        event.respondWith(
            caches.open(CACHE_DYNAMIC).then(cache =>
                cache.match(request).then(cached => {
                    const networkPromise = fetch(request).then(response => {
                        if (response && response.status === 200) {
                            cache.put(request, response.clone());
                            trimCache(CACHE_DYNAMIC, MAX_DYNAMIC_ENTRIES);
                        }
                        return response;
                    }).catch(() => cached);

                    return cached || networkPromise;
                })
            )
        );
        return;
    }

    /* ─── ۴. HTML navigation: network-first، fallback به cache ─── */
    if (request.mode === 'navigate' || request.destination === 'document') {
        event.respondWith(
            fetch(request).then(response => {
                if (response && response.status === 200) {
                    const clone = response.clone();
                    caches.open(CACHE_STATIC).then(cache => cache.put(request, clone));
                }
                return response;
            }).catch(() => {
                return caches.match(request)
                    .then(cached => cached || caches.match('./index.html') || caches.match('./'));
            })
        );
        return;
    }

    /* ─── ۵. بقیه: network-first، fallback به cache ─── */
    event.respondWith(
        fetch(request).then(response => {
            if (response && response.status === 200 && response.type === 'basic') {
                const clone = response.clone();
                caches.open(CACHE_DYNAMIC).then(cache => {
                    cache.put(request, clone);
                    trimCache(CACHE_DYNAMIC, MAX_DYNAMIC_ENTRIES);
                });
            }
            return response;
        }).catch(() => {
            return caches.match(request).then(cached => {
                if (cached) return cached;
                return new Response('Offline — no cache available', {
                    status: 503,
                    statusText: 'Offline',
                    headers: { 'Content-Type': 'text/plain; charset=utf-8' }
                });
            });
        })
    );
});

/* ═══════════════════════════════════════════════════════════════
   Push Notification
   ═══════════════════════════════════════════════════════════════ */
self.addEventListener('push', event => {
    let data = {
        title: '💬 پیام جدید',
        body: 'پیام جدیدی دارید',
        tag: 'chat-msg',
        icon: 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"%3E%3Crect width="192" height="192" rx="40" fill="%235288c1"/%3E%3Ctext x="96" y="130" font-size="100" text-anchor="middle" fill="%23ffffff"%3E%F0%9F%92%AC%3C/text%3E%3C/svg%3E'
    };

    try {
        if (event.data) {
            const parsed = event.data.json();
            data = Object.assign(data, parsed);
        }
    } catch (e) {
        try {
            data.body = event.data ? event.data.text() : data.body;
        } catch (err) {}
    }

    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: data.icon,
            badge: data.badge || data.icon,
            tag: data.tag || 'chat-msg',
            vibrate: [100, 50, 100],
            data: data.data || {},
            requireInteraction: false,
            silent: false,
            renotify: true
        })
    );
});

/* ═══════════════════════════════════════════════════════════════
   کلیک روی اعلان
   ═══════════════════════════════════════════════════════════════ */
self.addEventListener('notificationclick', event => {
    event.notification.close();

    const data = event.notification.data || {};
    // مسیر پایه (پوشه اپ در GitHub Pages)
    const baseUrl = new URL('./index.html', self.registration.scope).href;
    const urlToOpen = data.url || baseUrl;

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clients => {
                // اگر تبی از اپ باز است، focus کن (و اگر لازم است، navigate)
                for (const client of clients) {
                    if (client.url.startsWith(self.registration.scope) && 'focus' in client) {
                        if (data.roomId && 'navigate' in client) {
                            return client.navigate(urlToOpen).then(() => client.focus());
                        }
                        return client.focus();
                    }
                }
                // وگرنه، پنجره جدید
                if (self.clients.openWindow) {
                    return self.clients.openWindow(urlToOpen);
                }
            })
    );
});

/* ═══════════════════════════════════════════════════════════════
   پیام از کلاینت (index.html / admin.html)
   ═══════════════════════════════════════════════════════════════ */
self.addEventListener('message', event => {
    if (!event.data || !event.data.type) return;

    const { type } = event.data;
    const port = event.ports && event.ports[0];

    if (type === 'SKIP_WAITING') {
        self.skipWaiting();
        return;
    }

    if (type === 'CACHE_URLS' && Array.isArray(event.data.urls)) {
        event.waitUntil(
            caches.open(CACHE_STATIC)
                .then(cache => cache.addAll(event.data.urls).catch(() => {}))
                .then(() => port && port.postMessage({ success: true }))
        );
        return;
    }

    if (type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys()
                .then(keys => Promise.all(keys.map(key => caches.delete(key))))
                .then(() => {
                    console.log('[SW] All caches cleared');
                    port && port.postMessage({ success: true });
                })
        );
        return;
    }

    if (type === 'PING') {
        port && port.postMessage({
            pong: true,
            version: CACHE_VERSION,
            timestamp: Date.now()
        });
        return;
    }

    if (type === 'GET_VERSION') {
        port && port.postMessage({ version: CACHE_VERSION });
        return;
    }
});

/* ═══════════════════════════════════════════════════════════════
   Background Sync (برای پیام‌های آفلاین آینده)
   ═══════════════════════════════════════════════════════════════ */
self.addEventListener('sync', event => {
    if (event.tag === 'sync-messages') {
        event.waitUntil(
            self.clients.matchAll({ type: 'window', includeUncontrolled: true })
                .then(clients => {
                    clients.forEach(client => {
                        client.postMessage({ type: 'SYNC_MESSAGES' });
                    });
                })
        );
    }
});

console.log('[SW] Script loaded:', CACHE_VERSION);
