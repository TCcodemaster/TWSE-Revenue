/**
 * UI 工具模組
 * 提供各種 UI 操作和元素管理的工具函數
 */
export class UiUtils {
  constructor() {}

  /**
   * 初始化下拉選單
   */
  initDropdowns() {
    // 填充年份下拉選單
    this.populateYearDropdowns();
    
    // 填充月份下拉選單
    this.populateMonthDropdowns();
    
    // 設置表格顯示切換按鈕
    this.setupTableToggle();
  }

  /**
   * 填充年份下拉選單
   */
  populateYearDropdowns() {
    const today = new Date();
    const currentMinguo = today.getFullYear() - 1911;

    const startYearSelect = document.getElementById('start-year');
    const endYearSelect = document.getElementById('end-year');
    
    if (!startYearSelect || !endYearSelect) return;
    
    // 清空現有選項
    startYearSelect.innerHTML = '';
    endYearSelect.innerHTML = '';
    
    // 添加年份選項
    for (let y = currentMinguo; y >= currentMinguo - 30; y--) {
      const option1 = document.createElement('option');
      option1.value = y;
      option1.textContent = y;
      startYearSelect.appendChild(option1);

      const option2 = document.createElement('option');
      option2.value = y;
      option2.textContent = y;
      endYearSelect.appendChild(option2);
    }
  }

  /**
   * 填充月份下拉選單
   */
  populateMonthDropdowns() {
    const startMonthSelect = document.getElementById('start-month');
    const endMonthSelect = document.getElementById('end-month');
    
    if (!startMonthSelect || !endMonthSelect) return;
    
    // 清空現有選項
    startMonthSelect.innerHTML = '';
    endMonthSelect.innerHTML = '';
    
    // 添加月份選項
    for (let m = 1; m <= 12; m++) {
      const option1 = document.createElement('option');
      option1.value = m;
      option1.textContent = m;
      startMonthSelect.appendChild(option1);

      const option2 = document.createElement('option');
      option2.value = m;
      option2.textContent = m;
      endMonthSelect.appendChild(option2);
    }

    // 設定月份預設值：起始為1，結束為12
    startMonthSelect.value = 1;
    endMonthSelect.value = 12;
  }

  /**
   * 設置表格顯示切換按鈕
   */
  setupTableToggle() {
    const toggleTableBtn = document.getElementById('toggle-table-btn');
    if (toggleTableBtn) {
      toggleTableBtn.addEventListener('click', () => {
        const resultsSection = document.getElementById('results-section');
        if (resultsSection.style.display === 'none' || resultsSection.style.display === '') {
          resultsSection.style.display = 'block';
        } else {
          resultsSection.style.display = 'none';
        }
      });
    }
  }

  /**
   * 清空表格
   * @param {string} selector - 表格 tbody 選擇器
   */
  clearTable(selector) {
    const tableBody = document.querySelector(selector);
    if (tableBody) {
      tableBody.innerHTML = '';
    }
  }

  /**
   * 填充表格資料
   * @param {string} selector - 表格 tbody 選擇器
   * @param {Array} data - 要填充的數據
   */
  populateTable(selector, data) {
    const tableBody = document.querySelector(selector);
    if (!tableBody) return;
    
    tableBody.innerHTML = '';

    // 按公司代號和月份排序
    const sortedData = [...data].sort((a, b) => {
      if (a['公司代號'] === b['公司代號']) {
        return a['月份'].localeCompare(b['月份']);
      }
      return a['公司代號'].localeCompare(b['公司代號']);
    });

    // 填充表格
    sortedData.forEach(item => {
      const row = document.createElement('tr');

      // 創建每個單元格
      const columns = ['公司代號', '公司名稱', '當月營收', '上月營收', '去年當月營收', '上月比較增減(%)', '去年同月增減(%)', '月份'];
      columns.forEach(key => {
        const cell = document.createElement('td');
        cell.textContent = item[key] || '';
        row.appendChild(cell);
      });

      tableBody.appendChild(row);
    });
  }

  /**
   * 設置移動端導航功能
   * @param {Function} fetchDataCallback - 獲取數據的回調函數
   * @param {Object} chartService - 圖表服務實例
   */
  setupMobileNavigation(fetchDataCallback, chartService) {
    // 搜尋導航項目點擊
    const searchNav = document.getElementById('search-nav');
    if (searchNav) {
      searchNav.addEventListener('click', (e) => {
        e.preventDefault();
        // 滾動到頁面頂部（搜尋表單區域）
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    // 數據導航項目點擊
    const dataNav = document.getElementById('data-nav');
    if (dataNav) {
      dataNav.addEventListener('click', (e) => {
        e.preventDefault();
        // 如果結果部分已顯示，則滾動到結果表格
        const resultsSection = document.getElementById('results-section');
        if (resultsSection && resultsSection.style.display !== 'none') {
          resultsSection.scrollIntoView({ behavior: 'smooth' });
        } else {
          // 如果結果部分未顯示，先執行搜尋
          fetchDataCallback();
        }
      });
    }

    // 圖表導航項目點擊
    const chartNav = document.getElementById('chart-nav');
    if (chartNav) {
      chartNav.addEventListener('click', (e) => {
        e.preventDefault();
        
        // 如果圖表部分已顯示，則滾動到圖表區域
        const chartSection = document.getElementById('chart-section');
        if (chartSection && chartSection.style.display !== 'none') {
          chartSection.scrollIntoView({ behavior: 'smooth' });
        } else {
          // 如果圖表部分未顯示，且已有數據，則顯示營收圖表
          const currentData = window.app?.currentData || [];
          if (currentData.length > 0) {
            chartService.fetchRevenueChartData(currentData);
            // 短暫延遲後滾動到圖表區域（等待圖表加載）
            setTimeout(() => {
              const chartSection = document.getElementById('chart-section');
              if (chartSection) {
                chartSection.scrollIntoView({ behavior: 'smooth' });
              }
            }, 300);
          } else {
            // 如果沒有數據，提示用戶先進行搜尋
            alert('請先搜尋公司數據，再查看圖表。');
          }
        }
      });
    }
  }
}