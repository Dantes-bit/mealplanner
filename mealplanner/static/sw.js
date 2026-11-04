const CACHE_NAME = 'mealplanner-v4';
const OFFLINE_URL = '/offline';

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.add(OFFLINE_URL))
    );
    self.skipWaiting();
});

self.addEventListener('fetch', event => {
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(OFFLINE_URL))
        );
        return;
    }

    if (event.request.destination === 'style' || event.request.destination === 'script') {
        event.respondWith(fetch(event.request));
        return;
    }

    event.respondWith(
        caches.match(event.request).then(response => response || fetch(event.request))
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        Promise.all([
            caches.keys().then(names =>
                Promise.all(names.filter(name => name !== CACHE_NAME).map(name => caches.delete(name)))
            ),
            self.clients.claim()
        ])
    );
});

self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'MealPlanner';
    const options = {
        body: data.body || 'You have a new notification',
        icon: '/static/icons/icon-192.png',
        badge: '/static/icons/icon-192.png'
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
    event.notification.close();
    event.waitUntil(clients.openWindow('/'));
});