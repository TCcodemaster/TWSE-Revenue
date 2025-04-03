/**
 * ProgressTracker 類
 * 用於追蹤和顯示長時間運行任務的進度
 */
class ProgressTracker {
  /**
   * 建立一個進度追蹤器實例
   * @param {Object} options - 設定選項
   * @param {number} options.intervalTime - 輪詢間隔（毫秒）
   * @param {string} options.progressUrl - 進度 API 的 URL
   * @param {Function} options.onCompleted - 完成時的回調函數
   * @param {Function} options.onError - 發生錯誤時的回調函數
   */
  constructor(options = {}) {
    this.progressInterval = null;
    this.completedFlag = false;
    this.intervalTime = options.intervalTime || 1000; // 輪詢間隔（毫秒）
    this.progressUrl = options.progressUrl || '/api/scraper-progress';
    this.onCompleted = options.onCompleted || null;
    this.onError = options.onError || null;
  }

  /**
   * 開始進度輪詢，定時請求進度 API 並更新進度條
   */
  startProgressPolling() {
    console.log("開始進度輪詢");
    this.completedFlag = false;
    // 先確保停止之前的輪詢
    this.stopProgressPolling();

    this.progressInterval = setInterval(() => {
      fetch(this.progressUrl)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log("進度數據:", data);
          const status = this.updateProgress(data);
          // 當狀態完成或出錯時，延遲後停止輪詢
          if (status === 'completed' || status === 'error') {
            if (status === 'error') {
              const errorElement = document.querySelector('.error-message');
              if (errorElement && data.error) {
                errorElement.textContent = `錯誤: ${data.error}`;
                errorElement.style.display = 'block';
              }
              
              // 調用錯誤回調函數（如果有）
              if (this.onError && typeof this.onError === 'function') {
                this.onError(data.error);
              }
            } else if (status === 'completed') {
              // 調用完成回調函數（如果有）
              if (this.onCompleted && typeof this.onCompleted === 'function') {
                this.onCompleted(data);
              }
            }
            
            setTimeout(() => {
              this.stopProgressPolling();
            }, 1000);
          }
        })
        .catch(error => {
          console.error('輪詢進度時出錯:', error);
          if (this.onError && typeof this.onError === 'function') {
            this.onError(error.message);
          }
        });
    }, this.intervalTime);
  }

  /**
   * 停止進度輪詢
   */
  stopProgressPolling() {
    if (this.progressInterval) {
      clearInterval(this.progressInterval);
      this.progressInterval = null;
      console.log("停止進度輪詢");
    }
  }

  /**
   * 加強載入訊息，建立進度條結構
   * @returns {HTMLElement|null} 返回 loading 訊息元素，若找不到則返回 null
   */
  enhanceLoadingMessage() {
    const loadingMessage = document.querySelector('.loading-message');
    if (!loadingMessage) return null;

    // 若已存在進度條則直接返回
    if (loadingMessage.querySelector('.progress-container')) return loadingMessage;

    // 保留原始內容
    const originalContent = loadingMessage.innerHTML;
    const messageContainer = document.createElement('div');
    messageContainer.style.textAlign = 'center';
    messageContainer.style.marginBottom = '10px';
    messageContainer.innerHTML = originalContent;

    // 建立進度條容器
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container mt-3';
    progressContainer.innerHTML = `
      <div class="progress" style="height: 20px;">
        <div id="progress-bar" class="progress-bar progress-bar-striped progress-bar-animated" 
             role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
          0%
        </div>
      </div>
      <div id="progress-info" class="small mt-2" style="font-size: 0.9em;">準備中...</div>
    `;

    // 清空原內容並加入新的結構
    loadingMessage.innerHTML = '';
    loadingMessage.appendChild(messageContainer);
    loadingMessage.appendChild(progressContainer);

    return loadingMessage;
  }

  /**
   * 根據 API 返回的資料更新進度條與進度資訊
   * @param {Object} data - 進度數據
   * @returns {string} 返回目前的狀態文本（例如：idle、running、completed、error）
   */
  updateProgress(data) {
    const progressBar = document.getElementById('progress-bar');
    const progressInfo = document.getElementById('progress-info');

    if (!progressBar || !progressInfo) {
      console.error('進度條元素未找到', { progressBar, progressInfo });
      return data.status;
    }

    const percentage = data.percentage || 0;
    progressBar.style.width = `${percentage}%`;
    progressBar.textContent = `${percentage}%`;
    progressBar.setAttribute('aria-valuenow', percentage);

    // 根據不同狀態設置不同的顏色
    if (data.status === 'error') {
      progressBar.classList.remove('bg-primary', 'bg-success', 'bg-warning');
      progressBar.classList.add('bg-danger');
    } else if (data.status === 'completed') {
      progressBar.classList.remove('bg-primary', 'bg-danger', 'bg-warning');
      progressBar.classList.add('bg-success');
    } else if (percentage > 95) {
      progressBar.classList.remove('bg-primary', 'bg-danger', 'bg-success');
      progressBar.classList.add('bg-warning');
    } else {
      progressBar.classList.remove('bg-success', 'bg-danger', 'bg-warning');
      progressBar.classList.add('bg-primary');
    }

    let statusText = '';
    switch (data.status) {
      case 'idle': statusText = '準備中'; break;
      case 'running': statusText = '執行中'; break;
      case 'completed': statusText = '已完成'; break;
      case 'error': statusText = '發生錯誤'; break;
      default: statusText = data.status;
    }

    const timeSinceUpdate = data.time_since_update || '';
    progressInfo.innerHTML = `
      ${statusText} - 完成: ${data.completed}/${data.total}
      <br>公司: ${data.current_company || '無'} ${timeSinceUpdate}
    `;

    return data.status;
  }
}

// 導出 ProgressTracker 類，使其他模組可以使用
export default ProgressTracker;