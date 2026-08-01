const CACHE_NAME = 'mealplanner-v1';
const urlsToCache = [
    '/',
    '/static/main.css',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            );
        })
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