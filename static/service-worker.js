// 服務工作者的快取名稱
const CACHE_NAME = 'twse-revenue-app-v1';

// 需要快取的資源
const CACHE_URLS = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js',
  'https://code.jquery.com/jquery-3.6.0.min.js',
  'https://code.highcharts.com/highcharts.js',
  'https://code.highcharts.com/modules/exporting.js',
  'https://code.highcharts.com/modules/export-data.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',
  '/static/icons/icon-72x72.png',
  '/static/icons/icon-96x96.png',
  '/static/icons/icon-128x128.png',
  '/static/icons/icon-144x144.png',
  '/static/icons/icon-152x152.png',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-384x384.png',
  '/static/icons/icon-512x512.png'
];

// 安裝事件 - 當服務工作者被安裝時執行
self.addEventListener('install', event => {
  // 等待直到所有資源都被快取
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('快取打開成功');
        return cache.addAll(CACHE_URLS);
      })
      .then(() => {
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('快取資源時出錯:', error);
      })
  );
});

// 啟動事件 - 當服務工作者被啟用時執行
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          // 刪除舊的快取
          if (cacheName !== CACHE_NAME) {
            console.log('刪除舊快取:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // 聲明控制權
      return self.clients.claim();
    })
  );
});

// 攔截請求事件
self.addEventListener('fetch', event => {
  // 跳過非 GET 請求和 API 請求
  if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // 如果在快取中找到了匹配的響應，則返回它
        if (response) {
          return response;
        }

        // 複製請求，因為請求是一次性的
        const fetchRequest = event.request.clone();

        // 發送網路請求
        return fetch(fetchRequest)
          .then(response => {
            // 檢查是否收到了有效響應
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // 複製響應，因為響應體只能使用一次
            const responseToCache = response.clone();

            // 將新資源添加到快取
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return response;
          });
      })
      .catch(error => {
        console.error('獲取資源時出錯:', error);
        // 如果是導航請求（請求 HTML 頁面），則返回離線頁面
        if (event.request.mode === 'navigate') {
          return caches.match('/offline.html');
        }
      })
  );
});

// 推送通知事件
self.addEventListener('push', event => {
  const title = '營收查詢系統通知';
  const options = {
    body: event.data ? event.data.text() : '有新的資訊',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-96x96.png'
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// 點擊通知事件
self.addEventListener('notificationclick', event => {
  event.notification.close();

  event.waitUntil(
    clients.openWindow('/')
  );
});