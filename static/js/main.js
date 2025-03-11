/**
 * 主程式入口點
 * 負責初始化和協調各模組
 */

// 載入所有模組
import { AutocompleteService } from './autocomplete.js';
import { ApiService } from './api-service.js';
import { ChartService } from './chart-service.js';
import { ProgressTracker } from './progress-tracker.js';
import { UiUtils } from './ui-utils.js';
import { HistoryService } from './history-service.js';

// 全局變數，用於存儲當前查詢的數據
let currentData = [];

// 主應用程式類別
class App {
  constructor() {
    this.autocompleteService = new AutocompleteService();
    this.apiService = new ApiService();
    this.chartService = new ChartService();
    this.progressTracker = new ProgressTracker();
     
    this.uiUtils = new UiUtils();
    this.historyService = new HistoryService();
    
    // 存放當前查詢數據
    this.currentData = [];
  }

  /**
   * 初始化應用程式
   */
  init() {
    document.addEventListener('DOMContentLoaded', () => {
      // 初始化自動補全功能
      this.autocompleteService.init();

      // 初始化 UI 元素
      this.uiUtils.initDropdowns();
      this.uiUtils.setupMobileNavigation(this.fetchCompanyData.bind(this), this.chartService);

      // 設置搜尋表單提交事件
      const searchForm = document.getElementById('search-form');
      if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
          e.preventDefault();
          this.fetchCompanyData();
        });
      }

      // 設置清除表單按鈕
      const clearFormBtn = document.getElementById('clear-form');
      if (clearFormBtn) {
        clearFormBtn.addEventListener('click', () => {
          searchForm.reset();
          this.autocompleteService.clearTags();
        });
      }

      // 設置圖表按鈕點擊事件
      this.setupChartButtons();
      
      // 初始化歷史記錄功能
      this.historyService.init(this.autocompleteService.updateCompanyTags.bind(this.autocompleteService));
    });
  }

  /**
   * 設置圖表按鈕事件
   */
  setupChartButtons() {
    const revenueChartBtn = document.getElementById('revenue-chart-btn');
    if (revenueChartBtn) {
      revenueChartBtn.addEventListener('click', () => {
        if (this.currentData.length > 0) {
          this.chartService.fetchRevenueChartData(this.currentData);
        }
      });
    }

    const growthRateChartBtn = document.getElementById('growth-rate-chart-btn');
    if (growthRateChartBtn) {
      growthRateChartBtn.addEventListener('click', () => {
        if (this.currentData.length > 0) {
          this.chartService.fetchGrowthRateChartData(this.currentData);
        }
      });
    }

    const yearlyComparisonBtn = document.getElementById('yearly-comparison-btn');
    if (yearlyComparisonBtn) {
      yearlyComparisonBtn.addEventListener('click', () => {
        if (this.currentData.length > 0) {
          this.chartService.showCompanySelectModal(this.currentData);
        }
      });
    }
  }

  /**
   * 獲取公司數據
   */
/**
 * 獲取公司數據
 */
/**
 * 獲取公司數據
 */
fetchCompanyData() {
  // 獲取表單數據
  const companyIds = document.getElementById('company-ids-hidden').value;
  const startYear = document.getElementById('start-year').value;
  const endYear = document.getElementById('end-year').value;
  const startMonth = document.getElementById('start-month').value;
  const endMonth = document.getElementById('end-month').value;

  // 表單驗證
  if (!companyIds) {
    alert('請選擇公司');
    return;
  }

  // 格式化範圍值
  const yearRange = startYear === endYear ? startYear : `${startYear}-${endYear}`;
  const monthRange = startMonth === endMonth ? startMonth : `${startMonth}-${endMonth}`;

  // 顯示結果區域
  document.getElementById('results-section').style.display = 'block';

  // 準備載入訊息 - 重要：這個必須在發送API請求前調用
  this.progressTracker.enhanceLoadingMessage();
  document.querySelector('.loading-message').style.display = 'block';
  
  // 隱藏錯誤訊息和圖表區域
  document.querySelector('.error-message').style.display = 'none';
  document.getElementById('chart-section').style.display = 'none';

  // 清空表格
  this.uiUtils.clearTable('#results-table tbody');
  
  // 重要：在發送請求前啟動進度輪詢
  this.progressTracker.startProgressPolling();

  // 發送 API 請求
  this.apiService.getCompanyData(companyIds, yearRange, monthRange)
    .then(data => {
      // 儲存當前數據
      this.currentData = data;
      
      // 填充表格
      this.uiUtils.populateTable('#results-table tbody', data);
      
      // 隱藏載入訊息
      document.querySelector('.loading-message').style.display = 'none';
      
      // 請求完成後停止輪詢 - 移除這行，讓輪詢機制自行決定何時停止
      // this.progressTracker.stopProgressPolling();
    })
    .catch(error => {
      // 顯示錯誤訊息
      document.querySelector('.loading-message').style.display = 'none';
      const errorElement = document.querySelector('.error-message');
      errorElement.textContent = `錯誤: ${error.message}`;
      errorElement.style.display = 'block';
      
      // 請求出錯時停止輪詢 - 移除這行，讓輪詢機制自行決定何時停止
      // this.progressTracker.stopProgressPolling();
    });
}
}

// 創建應用實例並初始化
const app = new App();
app.init();

// 導出應用實例，以便在控制台中訪問
window.app = app;