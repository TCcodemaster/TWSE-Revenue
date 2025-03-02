// PWA 註冊 Service Worker
let deferredPrompt;
const installButton = document.getElementById('install-app');

// 註冊 Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(registration => {
                console.log('Service Worker 註冊成功，範圍:', registration.scope);
            })
            .catch(error => {
                console.log('Service Worker 註冊失敗:', error);
            });
    });
}

// 初始狀態隱藏安裝按鈕（因為現在它在導航欄中）
if (installButton) {
    installButton.classList.remove('available');
}

// 攔截安裝事件
window.addEventListener('beforeinstallprompt', (e) => {
    // 阻止 Chrome 67 及更早版本自動顯示安裝提示
    e.preventDefault();
    // 儲存事件，以便稍後觸發
    deferredPrompt = e;
    // 更新 UI 通知用戶可以安裝 PWA
    if (installButton) {
        // 不再需要顯示/隱藏，而是添加一個明顯的樣式類
        installButton.classList.add('available');
    }
});

// 安裝按鈕點擊事件
if (installButton) {
    installButton.addEventListener('click', (e) => {
        // 如果沒有安裝提示可用，則不執行任何操作
        if (!deferredPrompt) return;
        
        // 顯示安裝提示
        deferredPrompt.prompt();
        // 等待用戶回應提示
        deferredPrompt.userChoice
            .then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('用戶接受安裝');
                    // 安裝成功後移除高亮樣式
                    installButton.classList.remove('available');
                } else {
                    console.log('用戶拒絕安裝');
                }
                deferredPrompt = null;
            });
    });
}

// 檢測應用是否在獨立視窗中運行
window.addEventListener('DOMContentLoaded', () => {
    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
        // 應用以獨立模式運行
        console.log('應用正在以 PWA 模式運行');
        // 這裡可以添加專為 PWA 模式設計的 UI 調整
        document.body.classList.add('pwa-mode');
        
        // 如果是在 PWA 模式下，隱藏安裝按鈕
        if (installButton) {
            installButton.style.display = 'none';
        }
    }
});

// 設備離線提醒
window.addEventListener('online', () => {
    console.log('設備已恢復連接');
    document.body.classList.remove('offline-mode');
    
    // 顯示提示
    const toastContainer = document.getElementById('toast-container');
    if (toastContainer) {
        const toast = document.createElement('div');
        toast.className = 'toast show';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-success text-white">
                <strong class="me-auto">連接狀態</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="關閉"></button>
            </div>
            <div class="toast-body">
                網絡連接已恢復，您現在可以正常使用所有功能。
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // 5秒後自動關閉提示
        setTimeout(() => {
            const bsToast = new bootstrap.Toast(toast);
            bsToast.hide();
        }, 5000);
    }
});

window.addEventListener('offline', () => {
    console.log('設備已離線');
    document.body.classList.add('offline-mode');
    
    // 顯示提示
    const toastContainer = document.getElementById('toast-container');
    if (toastContainer) {
        const toast = document.createElement('div');
        toast.className = 'toast show';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-warning text-dark">
                <strong class="me-auto">連接狀態</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="關閉"></button>
            </div>
            <div class="toast-body">
                您的設備目前處於離線狀態。部分功能可能無法使用，但您仍可以訪問已快取的內容。
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // 保持提示直到恢復連接
    }
});