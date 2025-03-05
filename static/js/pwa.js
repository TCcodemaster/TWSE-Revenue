// 這個文件應該放在 static/js/pwa.js

// PWA相關功能
const PWA = {
  // 初始化
  init: function() {
      console.log('PWA功能已初始化');
      
      // 如果支援 Service Worker
      if ('serviceWorker' in navigator) {
          this.registerServiceWorker();
      }
  },
  
  // 註冊 Service Worker
  registerServiceWorker: function() {
      navigator.serviceWorker
          .register('/static/service-worker.js')
          .then((registration) => {
              console.log('Service Worker 註冊成功:', registration);
          })
          .catch((error) => {
              console.error('Service Worker 註冊失敗:', error);
          });
  }
};

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
  PWA.init();
});

// 暴露到全局
window.PWA = PWA;