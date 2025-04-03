// main.js 頂部
import ProgressTracker from './utils/progress-tracker.js';
let currentData = [];


document.addEventListener('DOMContentLoaded', function () {
  // === 自動補全與標籤功能開始 ===
  if (!window.STOCK_LIST || !Array.isArray(window.STOCK_LIST)) {
    console.error("STOCK_LIST 未正確載入！");
    return;
  }

  // 獲取必要的 DOM 元素
  const inputField = document.getElementById("company-ids");
  const autocompleteList = document.getElementById("autocomplete-results");
  const selectedCompaniesContainer = document.getElementById("selected-companies");
  const hiddenInput = document.getElementById("company-ids-hidden");
  const industryFilter = document.getElementById('industry-filter');
  const marketFilter = document.getElementById('market-filter');

  let selectedCompanies = [];

  // 初始化篩選選項
  function populateStockFilters() {
    if (!industryFilter || !marketFilter) return;

    const industries = [...new Set(window.STOCK_LIST.map(stock => stock.industry))].sort();
    const markets = [...new Set(window.STOCK_LIST.map(stock => stock.market))].sort();
    
    industries.forEach(industry => {
      const option = document.createElement('option');
      option.value = industry;
      option.textContent = industry;
      industryFilter.appendChild(option);
    });
    
    markets.forEach(market => {
      const option = document.createElement('option');
      option.value = market;
      option.textContent = market;
      marketFilter.appendChild(option);
    });
  }

  // 自動補全和篩選函數
  function updateAutoCompleteResults() {
    const query = inputField.value.trim();
    const selectedIndustry = industryFilter.value;
    const selectedMarket = marketFilter.value;
    
    autocompleteList.innerHTML = "";
    
    // 如果沒有任何篩選條件，不顯示結果
    if (!query && !selectedIndustry && !selectedMarket) return;
    
    // 篩選邏輯
    const matches = window.STOCK_LIST.filter(company => {
      const matchesQuery = !query || 
                           company.code.includes(query) || 
                           company.name.includes(query);
      
      const matchesIndustry = !selectedIndustry || 
                              company.industry === selectedIndustry;
      
      const matchesMarket = !selectedMarket || 
                            company.market === selectedMarket;
      
      return matchesQuery && matchesIndustry && matchesMarket;
    });
    
    // 限制結果數量
    const displayMatches = matches.slice(0, 20);
    
    // 渲染結果
    displayMatches.forEach((company) => {
      const item = document.createElement("div");
      item.classList.add("autocomplete-item");
      item.innerHTML = `
        <span class="company-code">${company.code}</span> 
        <span class="company-name">${company.name}</span>
        <small class="company-industry">${company.industry}</small>
      `;
      
      item.dataset.code = company.code;
      
      item.addEventListener("click", () => {
        addCompanyTag(company);
        inputField.value = "";
        autocompleteList.innerHTML = "";
      });
      
      autocompleteList.appendChild(item);
    });
  }

  // 加入標籤函數
  function addCompanyTag(company) {
    if (selectedCompanies.includes(company.code)) return;
    selectedCompanies.push(company.code);

    // 創建標籤元素
    const tag = document.createElement("span");
    tag.classList.add("company-tag");

    // 創建標籤文字元素
    const tagText = document.createElement("span");
    tagText.textContent = `${company.code} ${company.name}`;

    // 創建移除按鈕
    const removeButton = document.createElement("span");
    removeButton.classList.add("remove-btn");
    removeButton.innerHTML = "×";

    // 點擊移除按鈕可移除標籤
    removeButton.addEventListener("click", (event) => {
      event.stopPropagation();
      selectedCompanies = selectedCompanies.filter(
        (code) => code !== company.code
      );
      tag.remove();
      updateHiddenInput();
    });

    // 將文字和移除按鈕加入標籤元素
    tag.appendChild(tagText);
    tag.appendChild(removeButton);
    tag.dataset.code = company.code;

    selectedCompaniesContainer.appendChild(tag);
    updateHiddenInput();
  }

  // 更新隱藏欄位的值
  function updateHiddenInput() {
    hiddenInput.value = selectedCompanies.join(",");
    console.log("已選公司:", hiddenInput.value);
  }

  // 事件綁定
  inputField.addEventListener("input", updateAutoCompleteResults);
  industryFilter.addEventListener('change', updateAutoCompleteResults);
  marketFilter.addEventListener('change', updateAutoCompleteResults);

  // 點擊外部時，清除自動補全選單
  document.addEventListener("click", (event) => {
    if (!inputField.contains(event.target) && !autocompleteList.contains(event.target)) {
      autocompleteList.innerHTML = "";
    }
  });

  // 初始化行業和市場篩選選項
  populateStockFilters();

  // 移動端導航功能
  setupMobileNavigation();

  // 查詢表單提交
  const searchForm = document.getElementById('search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', function (e) {
      e.preventDefault();
      fetchCompanyData();
    });
  }

  // 清除表單按鈕
  const clearFormBtn = document.getElementById('clear-form');
  if (clearFormBtn) {
    clearFormBtn.addEventListener('click', function () {
      searchForm.reset();
    });
  }

  // 歷史記錄點擊事件，更新下拉選單的值
  const historyItems = document.querySelectorAll('.history-item');
  historyItems.forEach(item => {
    item.addEventListener('click', function (e) {
      e.preventDefault();
      // 設定公司代號
      document.getElementById('company-ids').value = this.dataset.companyIds;
      document.getElementById('company-ids-hidden').value = this.dataset.companyIds;

      // 解析年份範圍 (例如 "111-112" 或 "112")
      const yearRange = this.dataset.yearRange;
      if (yearRange.includes('-')) {
        const years = yearRange.split('-');
        document.getElementById('start-year').value = years[0];
        document.getElementById('end-year').value = years[1];
      } else {
        document.getElementById('start-year').value = yearRange;
        document.getElementById('end-year').value = yearRange;
      }

      // 解析月份範圍 (例如 "1-3" 或 "6")
      const monthRange = this.dataset.monthRange;
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

  // 圖表按鈕點擊事件
  const revenueChartBtn = document.getElementById('revenue-chart-btn');
  if (revenueChartBtn) {
    revenueChartBtn.addEventListener('click', function () {
      if (currentData.length > 0) {
        fetchRevenueChartData();
      }
    });
  }

  const growthRateChartBtn = document.getElementById('growth-rate-chart-btn');
  if (growthRateChartBtn) {
    growthRateChartBtn.addEventListener('click', function () {
      if (currentData.length > 0) {
        fetchGrowthRateChartData();
      }
    });
  }

  const yearlyComparisonBtn = document.getElementById('yearly-comparison-btn');
  if (yearlyComparisonBtn) {
    yearlyComparisonBtn.addEventListener('click', function () {
      if (currentData.length > 0) {
        showCompanySelectModal();
      }
    });
  }

  // 填充下拉選單選項
  const today = new Date();
  const currentMinguo = today.getFullYear() - 1911;

  const startYearSelect = document.getElementById('start-year');
  const endYearSelect = document.getElementById('end-year');
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

  const startMonthSelect = document.getElementById('start-month');
  const endMonthSelect = document.getElementById('end-month');
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

  // 設定切換表格顯示按鈕
  const toggleTableBtn = document.getElementById('toggle-table-btn');
  if (toggleTableBtn) {
    toggleTableBtn.addEventListener('click', function () {
      const resultsSection = document.getElementById('results-section');
      if (resultsSection.style.display === 'none' || resultsSection.style.display === '') {
        resultsSection.style.display = 'block';
      } else {
        resultsSection.style.display = 'none';
      }
    });
  }
});

// 獲取公司數據
function fetchCompanyData() {
  const companyIds = document.getElementById('company-ids-hidden').value;
  const startYear = document.getElementById('start-year').value;
  const endYear = document.getElementById('end-year').value;
  const startMonth = document.getElementById('start-month').value;
  const endMonth = document.getElementById('end-month').value;
  const progressTracker = new ProgressTracker({
    // 自定義進度 API 的 URL
    progressUrl: '/api/scraper-progress',
    
    // 自定義輪詢間隔時間（毫秒）
    intervalTime: 1000,
    
    // 當進度完成時的回調函數
    onCompleted: function(data) {
      console.log('進度追蹤完成', data);
    },
    
    // 當發生錯誤時的回調函數
    onError: function(error) {
      console.error('進度追蹤出錯:', error);
      const errorElement = document.querySelector('.error-message');
      if (errorElement) {
        errorElement.textContent = `錯誤: ${error}`;
        errorElement.style.display = 'block';
      }
    }
  });

  const yearRange = `${startYear}-${endYear}`;
  const monthRange = `${startMonth}-${endMonth}`;

  // 顯示結果區域和加載訊息
  document.getElementById('results-section').style.display = 'block';
  document.querySelector('.loading-message').style.display = 'block';
  document.querySelector('.error-message').style.display = 'none';
  document.getElementById('chart-section').style.display = 'none';

  // 清空表格
  const tableBody = document.querySelector('#results-table tbody');
  tableBody.innerHTML = '';
  // 在發送請求前：
  progressTracker.enhanceLoadingMessage();  // 建立進度條的 DOM 結構
  progressTracker.startProgressPolling();     // 啟動進度輪詢

  // 發送 API 請求
  fetch('/api/company-data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      company_ids: companyIds,
      year_range: yearRange,
      month_range: monthRange
    }),
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('網路回應不正常');
      }
      return response.json();
    })
    .then(data => {
      // 隱藏加載訊息
      document.querySelector('.loading-message').style.display = 'none';
      // 請求完成或錯誤後：
      progressTracker.stopProgressPolling();

      if (data.error) {
        throw new Error(data.error);
      }

      // 儲存當前數據
      currentData = data.data;

      // 填充表格
      populateTable(currentData);
    })
    .catch(error => {
      // 隱藏加載訊息，顯示錯誤訊息
      document.querySelector('.loading-message').style.display = 'none';
      const errorElement = document.querySelector('.error-message');
      errorElement.textContent = `錯誤: ${error.message}`;
      errorElement.style.display = 'block';
    });
}

// 填充表格
function populateTable(data) {
  const tableBody = document.querySelector('#results-table tbody');
  tableBody.innerHTML = '';

  // 按公司代號和月份排序
  data.sort((a, b) => {
    if (a['公司代號'] === b['公司代號']) {
      return a['月份'].localeCompare(b['月份']);
    }
    return a['公司代號'].localeCompare(b['公司代號']);
  });

  // 填充表格
  data.forEach(item => {
    const row = document.createElement('tr');

    // 創建每個單元格
    ['公司代號', '公司名稱', '當月營收', '上月營收', '去年當月營收', '上月比較增減(%)', '去年同月增減(%)', '月份'].forEach(key => {
      const cell = document.createElement('td');
      cell.textContent = item[key] || '';
      row.appendChild(cell);
    });

    tableBody.appendChild(row);
  });
}

// 獲取營收圖表數據
function fetchRevenueChartData() {
  // 顯示圖表區域和加載訊息
  document.getElementById('chart-section').style.display = 'block';
  document.getElementById('chart-title').textContent = '公司營收比較圖';

  // 發送 API 請求
  fetch('/api/revenue-chart', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      data: currentData
    }),
  })
    .then(response => response.json())
    .then(data => {
      // 繪製圖表
      drawRevenueChart(data);
    })
    .catch(error => {
      console.error('獲取圖表數據時出錯:', error);
      alert('獲取圖表數據時出錯: ' + error.message);
    });
}

// 繪製營收圖表
function drawRevenueChart(data) {
  Highcharts.chart('chart-container', {
    chart: {
      type: 'line'
    },
    title: {
      text: '公司營收比較'
    },
    xAxis: {
      categories: data.categories,
      title: {
        text: '年月'
      }
    },
    yAxis: {
      title: {
        text: '營收'
      },
      labels: {
        formatter: function () {
          return Highcharts.numberFormat(this.value, 0, '.', ',');
        }
      }
    },
    tooltip: {
      formatter: function () {
        return '<b>' + this.series.name + '</b><br/>' +
          this.x + ': ' + Highcharts.numberFormat(this.y, 0, '.', ',');
      }
    },
    plotOptions: {
      line: {
        marker: {
          enabled: true
        }
      }
    },
    series: data.series
  });
}

// 獲取增長率圖表數據
function fetchGrowthRateChartData() {
  // 顯示圖表區域和加載訊息
  document.getElementById('chart-section').style.display = 'block';
  document.getElementById('chart-title').textContent = '公司營收增減率比較圖';

  // 發送 API 請求
  fetch('/api/growth-rate-chart', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      data: currentData
    }),
  })
    .then(response => response.json())
    .then(data => {
      // 繪製圖表
      drawGrowthRateChart(data);
    })
    .catch(error => {
      console.error('獲取圖表數據時出錯:', error);
      alert('獲取圖表數據時出錯: ' + error.message);
    });
}

// 繪製增長率圖表
function drawGrowthRateChart(data) {
  Highcharts.chart('chart-container', {
    chart: {
      type: 'line'
    },
    title: {
      text: '公司營收增減率比較'
    },
    xAxis: {
      categories: data.categories,
      title: {
        text: '年月'
      }
    },
    yAxis: {
      title: {
        text: '增減率 (%)'
      },
      labels: {
        format: '{value}%'
      }
    },
    tooltip: {
      formatter: function () {
        return '<b>' + this.series.name + '</b><br/>' +
          this.x + ': ' + this.y + '%';
      }
    },
    plotOptions: {
      line: {
        marker: {
          enabled: true
        }
      }
    },
    series: data.series
  });
}

// 顯示公司選擇對話框
function showCompanySelectModal() {
  // 獲取不重複的公司列表
  const companies = [];
  const companyIds = new Set();

  currentData.forEach(item => {
    if (!companyIds.has(item['公司代號'])) {
      companyIds.add(item['公司代號']);
      companies.push({
        id: item['公司代號'],
        name: item['公司名稱']
      });
    }
  });

  // 填充公司選擇列表
  const companySelectList = document.getElementById('company-select-list');
  companySelectList.innerHTML = '';

  companies.forEach(company => {
    const item = document.createElement('a');
    item.href = '#';
    item.className = 'list-group-item list-group-item-action';
    item.textContent = `${company.id} ${company.name}`;
    item.dataset.companyId = company.id;

    item.addEventListener('click', function (e) {
      e.preventDefault();
      const companyId = this.dataset.companyId;
      fetchYearlyComparisonData(companyId);

      // 關閉對話框
      const modal = bootstrap.Modal.getInstance(document.getElementById('company-select-modal'));
      modal.hide();
    });

    companySelectList.appendChild(item);
  });

  // 顯示對話框
  const modal = new bootstrap.Modal(document.getElementById('company-select-modal'));
  modal.show();
}

// 獲取年度比較圖表數據
function fetchYearlyComparisonData(companyId) {
  // 顯示圖表區域和加載訊息
  document.getElementById('chart-section').style.display = 'block';
  document.getElementById('chart-title').textContent = `${companyId} 歷年營收比較圖`;

  // 發送 API 請求
  fetch('/api/yearly-comparison-chart', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      data: currentData,
      company_id: companyId
    }),
  })
    .then(response => response.json())
    .then(data => {
      // 繪製圖表
      drawYearlyComparisonChart(data, companyId);
    })
    .catch(error => {
      console.error('獲取圖表數據時出錯:', error);
      alert('獲取圖表數據時出錯: ' + error.message);
    });
}

// 繪製年度比較圖表
function drawYearlyComparisonChart(data, companyId) {
  // 從當前數據中找到公司名稱
  let companyName = '';
  for (const item of currentData) {
    if (item['公司代號'] === companyId) {
      companyName = item['公司名稱'];
      break;
    }
  }

  Highcharts.chart('chart-container', {
    chart: {
      type: 'line'
    },
    title: {
      text: `${companyId} ${companyName} 歷年營收比較`
    },
    xAxis: {
      categories: data.categories,
      title: {
        text: '月份'
      }
    },
    yAxis: {
      title: {
        text: '營收'
      },
      labels: {
        formatter: function () {
          return Highcharts.numberFormat(this.value, 0, '.', ',');
        }
      }
    },
    tooltip: {
      formatter: function () {
        return '<b>' + this.series.name + '</b><br/>' +
          this.x + '月: ' + Highcharts.numberFormat(this.y, 0, '.', ',');
      }
    },
    plotOptions: {
      line: {
        marker: {
          enabled: true
        }
      }
    },
    series: data.series
  });
}

// 設置移動端導航功能
function setupMobileNavigation() {
  // 搜尋導航項目點擊
  const searchNav = document.getElementById('search-nav');
  if (searchNav) {
    searchNav.addEventListener('click', function (e) {
      e.preventDefault();
      // 滾動到頁面頂部（搜尋表單區域）
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // 數據導航項目點擊
  const dataNav = document.getElementById('data-nav');
  if (dataNav) {
    dataNav.addEventListener('click', function (e) {
      e.preventDefault();
      // 如果結果部分已顯示，則滾動到結果表格
      const resultsSection = document.getElementById('results-section');
      if (resultsSection && resultsSection.style.display !== 'none') {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
      } else {
        // 如果結果部分未顯示，先執行搜尋
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
          searchForm.dispatchEvent(new Event('submit'));
        }
      }
    });
  }

  // 圖表導航項目點擊
  const chartNav = document.getElementById('chart-nav');
  if (chartNav) {
    chartNav.addEventListener('click', function (e) {
      e.preventDefault();
      // 如果圖表部分已顯示，則滾動到圖表區域
      const chartSection = document.getElementById('chart-section');
      if (chartSection && chartSection.style.display !== 'none') {
        chartSection.scrollIntoView({ behavior: 'smooth' });
      } else {
        // 如果圖表部分未顯示，且已有數據，則顯示營收圖表
        if (currentData.length > 0) {
          fetchRevenueChartData();
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



// 将此代码添加到 main.js 文件的底部，或替换现有的进度轮询代码



// 修正 fetchCompanyData 函数，确保在发送请求前启动进度轮询
function fetchCompanyData() {
  const companyIds = document.getElementById('company-ids-hidden').value;
  const startYear = document.getElementById('start-year').value;
  const endYear = document.getElementById('end-year').value;
  const startMonth = document.getElementById('start-month').value;
  const endMonth = document.getElementById('end-month').value;
  // 建立一個新的進度追蹤器實例（或使用全域/共享實例）
  const progressTracker = new ProgressTracker();

  const yearRange = `${startYear}-${endYear}`;
  const monthRange = `${startMonth}-${endMonth}`;

  // 顯示結果區域和加載訊息
  document.getElementById('results-section').style.display = 'block';
  document.querySelector('.loading-message').style.display = 'block';
  document.querySelector('.error-message').style.display = 'none';
  document.getElementById('chart-section').style.display = 'none';

  // 清空表格
  const tableBody = document.querySelector('#results-table tbody');
  tableBody.innerHTML = '';

  // 在發送請求前：呼叫進度追蹤器的方法
  progressTracker.enhanceLoadingMessage();  // 建立進度條的 DOM 結構
  progressTracker.startProgressPolling();     // 啟動進度輪詢

  // 發送 API 請求
  fetch('/api/company-data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      company_ids: companyIds,
      year_range: yearRange,
      month_range: monthRange
    }),
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('網路回應不正常');
      }
      return response.json();
    })
    .then(data => {
      // 請求完成後停止輪詢
      progressTracker.stopProgressPolling();
      // 隱藏 loading 訊息
      document.querySelector('.loading-message').style.display = 'none';

      if (data.error) {
        throw new Error(data.error);
      }

      // 儲存當前數據
      currentData = data.data;
      // 填充表格
      populateTable(currentData);
    })
    .catch(error => {
      // 錯誤時停止輪詢
      progressTracker.stopProgressPolling();
      document.querySelector('.loading-message').style.display = 'none';
      const errorElement = document.querySelector('.error-message');
      errorElement.textContent = `錯誤: ${error.message}`;
      errorElement.style.display = 'block';
    });
}


// 确保在页面加载完成后绑定事件
document.addEventListener('DOMContentLoaded', function () {
  // 这里可能需要重新绑定表单提交事件，以使用修改后的 fetchCompanyData 函数
  const searchForm = document.getElementById('search-form');
  if (searchForm) {
    // 移除现有的事件监听器 (如果可能的话)
    searchForm.removeEventListener('submit', fetchCompanyData);

    // 添加新的事件监听器
    searchForm.addEventListener('submit', function (e) {
      e.preventDefault();
      fetchCompanyData();
    });
  }
});

// 添加到 main.js 檔案中
document.addEventListener('DOMContentLoaded', function () {
  // 處理歷史記錄折疊
  const collapseElement = document.getElementById('collapseHistory');
  if (collapseElement) {
    // 監聽折疊狀態變化
    collapseElement.addEventListener('shown.bs.collapse', function () {
      const toggleButton = document.querySelector('[data-bs-toggle="collapse"]');
      if (toggleButton) {
        toggleButton.querySelector('.collapse-text').textContent = '收起記錄';
        toggleButton.querySelector('.collapse-icon').classList.remove('fa-chevron-down');
        toggleButton.querySelector('.collapse-icon').classList.add('fa-chevron-up');
      }
    });

    collapseElement.addEventListener('hidden.bs.collapse', function () {
      const toggleButton = document.querySelector('[data-bs-toggle="collapse"]');
      if (toggleButton) {
        const hiddenCount = document.querySelectorAll('.history-list-more .history-item').length;
        toggleButton.querySelector('.collapse-text').textContent = `更多記錄 (${hiddenCount})`;
        toggleButton.querySelector('.collapse-icon').classList.remove('fa-chevron-up');
        toggleButton.querySelector('.collapse-icon').classList.add('fa-chevron-down');
      }
    });
  }

  // 確保所有歷史項目的事件處理（包括折疊區域內的）
  const allHistoryItems = document.querySelectorAll('.history-item');
  allHistoryItems.forEach(item => {
    item.addEventListener('click', function (e) {
      e.preventDefault();

      // 設定公司代號
      const companyIds = this.dataset.companyIds;
      document.getElementById('company-ids').value = companyIds;
      document.getElementById('company-ids-hidden').value = companyIds;

      // 處理公司標籤（如果您使用標籤顯示選擇的公司）
      updateCompanyTags(companyIds);

      // 解析年份範圍 (例如 "111-112" 或 "112")
      const yearRange = this.dataset.yearRange;
      if (yearRange.includes('-')) {
        const years = yearRange.split('-');
        document.getElementById('start-year').value = years[0];
        document.getElementById('end-year').value = years[1];
      } else {
        document.getElementById('start-year').value = yearRange;
        document.getElementById('end-year').value = yearRange;
      }

      // 解析月份範圍 (例如 "1-3" 或 "6")
      const monthRange = this.dataset.monthRange;
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
});

// 更新公司標籤的輔助函數（如果您使用標籤顯示選擇的公司）
function updateCompanyTags(companyIdsStr) {
  // 如果不需要處理標籤，可以移除此函數
  if (!window.STOCK_LIST || !Array.isArray(window.STOCK_LIST)) {
    return;
  }

  // 清空現有標籤
  const selectedCompaniesContainer = document.getElementById('selected-companies');
  if (selectedCompaniesContainer) {
    selectedCompaniesContainer.innerHTML = '';
  }

  // 解析公司代號
  const companyIds = companyIdsStr.split(',');

  // 重新建立標籤
  const selectedCompanies = [];

  companyIds.forEach(companyId => {
    const trimmedId = companyId.trim();
    if (trimmedId) {
      selectedCompanies.push(trimmedId);

      // 找到對應的公司資訊
      const companyInfo = window.STOCK_LIST.find(company => company.code === trimmedId);

      if (companyInfo && selectedCompaniesContainer) {
        // 創建新標籤
        const tag = document.createElement('span');
        tag.classList.add('company-tag');

        const tagText = document.createElement('span');
        tagText.textContent = `${companyInfo.code} ${companyInfo.name}`;

        const removeButton = document.createElement('span');
        removeButton.classList.add('remove-btn');
        removeButton.innerHTML = '×';

        removeButton.addEventListener('click', function (event) {
          event.stopPropagation();
          selectedCompanies.splice(selectedCompanies.indexOf(trimmedId), 1);
          tag.remove();
          document.getElementById('company-ids-hidden').value = selectedCompanies.join(',');
        });

        tag.appendChild(tagText);
        tag.appendChild(removeButton);
        tag.dataset.code = trimmedId;

        selectedCompaniesContainer.appendChild(tag);
      }
    }
  });
}

