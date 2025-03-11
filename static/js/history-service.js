/**
 * 歷史服務模組
 * 負責處理歷史記錄功能
 */
export class HistoryService {
  constructor() {
    this.historyItems = [];
  }

  /**
   * 初始化歷史記錄
   * @param {Function} updateCompanyTagsCallback - 更新公司標籤的回調函數
   */
  init(updateCompanyTagsCallback) {
    // 處理歷史記錄折疊
    this.setupHistoryCollapse();
    
    // 設置歷史記錄點擊事件
    this.setupHistoryItemEvents(updateCompanyTagsCallback);
  }

  /**
   * 設置歷史記錄折疊功能
   */
  setupHistoryCollapse() {
    const collapseElement = document.getElementById('collapseHistory');
    if (collapseElement) {
      // 監聽折疊狀態變化
      collapseElement.addEventListener('shown.bs.collapse', () => {
        const toggleButton = document.querySelector('[data-bs-toggle="collapse"]');
        if (toggleButton) {
          toggleButton.querySelector('.collapse-text').textContent = '收起記錄';
          toggleButton.querySelector('.collapse-icon').classList.remove('fa-chevron-down');
          toggleButton.querySelector('.collapse-icon').classList.add('fa-chevron-up');
        }
      });
  
      collapseElement.addEventListener('hidden.bs.collapse', () => {
        const toggleButton = document.querySelector('[data-bs-toggle="collapse"]');
        if (toggleButton) {
          const hiddenCount = document.querySelectorAll('.history-list-more .history-item').length;
          toggleButton.querySelector('.collapse-text').textContent = `更多記錄 (${hiddenCount})`;
          toggleButton.querySelector('.collapse-icon').classList.remove('fa-chevron-up');
          toggleButton.querySelector('.collapse-icon').classList.add('fa-chevron-down');
        }
      });
    }
  }

  /**
   * 設置歷史記錄項目點擊事件
   * @param {Function} updateCompanyTagsCallback - 更新公司標籤的回調函數
   */
  setupHistoryItemEvents(updateCompanyTagsCallback) {
    const allHistoryItems = document.querySelectorAll('.history-item');
    allHistoryItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        
        // 設定公司代號
        const companyIds = item.dataset.companyIds;
        document.getElementById('company-ids').value = companyIds;
        document.getElementById('company-ids-hidden').value = companyIds;
  
        // 處理公司標籤
        if (typeof updateCompanyTagsCallback === 'function') {
          updateCompanyTagsCallback(companyIds);
        }
  
        // 解析年份範圍 (例如 "111-112" 或 "112")
        const yearRange = item.dataset.yearRange;
        if (yearRange.includes('-')) {
          const years = yearRange.split('-');
          document.getElementById('start-year').value = years[0];
          document.getElementById('end-year').value = years[1];
        } else {
          document.getElementById('start-year').value = yearRange;
          document.getElementById('end-year').value = yearRange;
        }
  
        // 解析月份範圍 (例如 "1-3" 或 "6")
        const monthRange = item.dataset.monthRange;
        if (monthRange.includes('-')) {
          const months = monthRange.split('-');
          document.getElementById('start-month').value = months[0];
          document.getElementById('end-month').value = months[1];
        } else {
          document.getElementById('start-month').value = monthRange;
          document.getElementById('end-month').value = monthRange;
        }
      });
    });
  }

  /**
   * 添加新的歷史記錄
   * @param {Object} data - 歷史記錄數據
   */
  addHistoryItem(data) {
    // 這裡可以實現向服務器提交新的歷史記錄
    // 目前頁面似乎是從後端渲染歷史記錄，這個方法可以擴展為添加本地臨時記錄
    console.log('添加新的歷史記錄', data);
  }

  /**
   * 移除歷史記錄
   * @param {string} id - 歷史記錄 ID
   */
  removeHistoryItem(id) {
    // 這裡可以實現向服務器請求刪除歷史記錄
    console.log('移除歷史記錄', id);
  }

  /**
   * 更新歷史記錄顯示
   * 如果將來需要動態更新歷史記錄列表，可以使用此方法
   */
  updateHistoryDisplay() {
    // 這個方法可以用來刷新歷史記錄列表
    console.log('更新歷史記錄顯示');
  }
}