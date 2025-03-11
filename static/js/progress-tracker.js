/**
 * 進度追蹤模組
 * 負責處理進度條和后台任務的狀態追蹤
 */
export class ProgressTracker {
    constructor() {
      // 不使用 ApiService 注入，改為直接使用 fetch
      this.progressInterval = null;
      this.completedFlag = false;
    }
  
    /**
     * 開始輪詢進度
     */
    startProgressPolling() {
      console.log("開始進度輪詢");
      
      // 重置完成標誌
      this.completedFlag = false;
      
      // 停止現有輪詢
      this.stopProgressPolling();
      
      // 開始輪詢 - 與原始代碼保持一致，直接使用 fetch 而不是通過 ApiService
      this.progressInterval = setInterval(() => {
        fetch('/api/scraper-progress')
          .then(response => {
            if (!response.ok) {
              throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
          })
          .then(data => {
            console.log("進度數據:", data);
            
            // 更新進度
            const status = this.updateProgress(data);
            
            // 檢查是否完成或出錯
            if (status === 'completed' || status === 'error') {
              if (status === 'error') {
                // 顯示錯誤信息
                const errorElement = document.querySelector('.error-message');
                if (errorElement && data.error) {
                  errorElement.textContent = `錯誤: ${data.error}`;
                  errorElement.style.display = 'block';
                }
              }
              
              // 延遲停止輪詢
              setTimeout(() => {
                this.stopProgressPolling();
              }, 1000);
            }
          })
          .catch(error => {
            console.error('輪詢進度時出錯:', error);
          });
      }, 1000);
    }
  
    /**
     * 停止輪詢進度
     */
    stopProgressPolling() {
      if (this.progressInterval) {
        clearInterval(this.progressInterval);
        this.progressInterval = null;
        console.log("停止進度輪詢");
      }
    }
  
    /**
     * 加強載入訊息，添加進度條
     * @returns {HTMLElement} 載入訊息元素
     */
    enhanceLoadingMessage() {
      const loadingMessage = document.querySelector('.loading-message');
      if (!loadingMessage) return null;
      
      // 如果已經有進度條，不需要重新創建
      if (loadingMessage.querySelector('.progress-container')) return loadingMessage;
      
      // 保留原始內容
      const originalContent = loadingMessage.innerHTML;
      
      // 更清晰的信息結構
      const messageContainer = document.createElement('div');
      messageContainer.style.textAlign = 'center';
      messageContainer.style.marginBottom = '10px';
      messageContainer.innerHTML = originalContent;
      
      // 創建進度條容器
      const progressContainer = document.createElement('div');
      progressContainer.className = 'progress-container mt-3';
      
      // 創建進度條 - 更明顯的設計
      progressContainer.innerHTML = `
        <div class="progress" style="height: 20px;">
          <div id="progress-bar" class="progress-bar progress-bar-striped progress-bar-animated" 
            role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
        </div>
        <div id="progress-info" class="small mt-2" style="font-size: 0.9em;">準備中...</div>
      `;
      
      // 清空原有內容並添加新的結構
      loadingMessage.innerHTML = '';
      loadingMessage.appendChild(messageContainer);
      loadingMessage.appendChild(progressContainer);
      
      return loadingMessage;
    }
  
    /**
     * 更新進度條
     * @param {Object} data - 進度數據
     * @returns {string} 狀態文本
     */
    updateProgress(data) {
      const progressBar = document.getElementById('progress-bar');
      const progressInfo = document.getElementById('progress-info');
      
      if (!progressBar || !progressInfo) {
        console.error('進度條元素未找到', { progressBar, progressInfo });
        return data.status;
      }
      
      // 更新進度條
      const percentage = data.percentage || 0;
      progressBar.style.width = `${percentage}%`;
      progressBar.textContent = `${percentage}%`;
      progressBar.setAttribute('aria-valuenow', percentage);
      
      // 根據狀態更新顏色
      if (data.status === 'error') {
        progressBar.classList.remove('bg-primary', 'bg-success', 'bg-warning');
        progressBar.classList.add('bg-danger');
      } else if (data.status === 'completed') {
        progressBar.classList.remove('bg-primary', 'bg-danger', 'bg-warning');
        progressBar.classList.add('bg-success');
      } else if (percentage > 95) {
        // 接近完成時使用黃色
        progressBar.classList.remove('bg-primary', 'bg-danger', 'bg-success');
        progressBar.classList.add('bg-warning');
      } else {
        progressBar.classList.remove('bg-success', 'bg-danger', 'bg-warning');
        progressBar.classList.add('bg-primary');
      }
      
      // 更新進度資訊
      let statusText = '';
      switch (data.status) {
        case 'idle': statusText = '準備中'; break;
        case 'running': statusText = '執行中'; break;
        case 'completed': statusText = '已完成'; break;
        case 'error': statusText = '發生錯誤'; break;
        default: statusText = data.status;
      }
      
      const timeSinceUpdate = data.time_since_update ? data.time_since_update : '';
      
      progressInfo.innerHTML = `
        ${statusText} - 完成: ${data.completed}/${data.total} 
        <br>公司: ${data.current_company || '無'} ${timeSinceUpdate}
      `;
      
      return data.status;
    }
  }