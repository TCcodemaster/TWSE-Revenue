/**
 * TWSE 系統保活 (Keep-Alive) 腳本
 * 用於防止雲端服務（如Render）在閒置時休眠應用程式
 */

// 設定保活間隔（毫秒，這裡設為每10分鐘）
const KEEP_ALIVE_INTERVAL = 10 * 60 * 1000;

// 設定是否啟用保活功能
const ENABLE_KEEP_ALIVE = true;

// 保活請求路徑
const KEEP_ALIVE_URL = '/api/keep-alive';

// 上次保活時間的儲存鍵
const LAST_PING_KEY = 'twse_last_keep_alive';

/**
 * 執行保活請求
 */
function pingServer() {
  console.log('[Keep-Alive] 發送保活請求...');
  
  fetch(KEEP_ALIVE_URL)
    .then(response => response.json())
    .then(data => {
      console.log(`[Keep-Alive] 保活成功: ${data.status}`);
      
      // 儲存最後保活時間
      localStorage.setItem(LAST_PING_KEY, Date.now().toString());
    })
    .catch(error => {
      console.error('[Keep-Alive] 保活請求失敗:', error);
    });
}

/**
 * 檢查並初始化保活系統
 */
function initKeepAlive() {
  if (!ENABLE_KEEP_ALIVE) {
    console.log('[Keep-Alive] 保活功能已禁用');
    return;
  }
  
  // 檢查上次保活時間
  const lastPing = localStorage.getItem(LAST_PING_KEY);
  const now = Date.now();
  
  if (lastPing) {
    const timeSinceLastPing = now - parseInt(lastPing);
    
    if (timeSinceLastPing >= KEEP_ALIVE_INTERVAL) {
      console.log('[Keep-Alive] 距離上次保活已超過間隔，立即執行保活');
      pingServer();
    } else {
      console.log(`[Keep-Alive] 距離上次保活: ${Math.floor(timeSinceLastPing / 1000)} 秒`);
    }
  } else {
    // 首次執行保活
    console.log('[Keep-Alive] 初始化保活系統');
    pingServer();
  }
  
  // 設定定期保活
  setInterval(pingServer, KEEP_ALIVE_INTERVAL);
  
  // 頁面可見性變化時檢查保活
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      const lastPing = localStorage.getItem(LAST_PING_KEY);
      if (lastPing) {
        const timeSinceLastPing = Date.now() - parseInt(lastPing);
        if (timeSinceLastPing >= KEEP_ALIVE_INTERVAL) {
          console.log('[Keep-Alive] 頁面重新可見且需要保活');
          pingServer();
        }
      }
    }
  });
}

// 當文檔加載完成時初始化保活系統
document.addEventListener('DOMContentLoaded', initKeepAlive);