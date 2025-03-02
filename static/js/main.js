// 全局變數，用於存儲當前查詢的數據
let currentData = [];

// 頁面載入完成後執行
document.addEventListener('DOMContentLoaded', function() {
    // 移動端導航功能
    setupMobileNavigation();
    
    // 查詢表單提交
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            fetchCompanyData();
        });
    }

    // 清除表單按鈕
    const clearFormBtn = document.getElementById('clear-form');
    if (clearFormBtn) {
        clearFormBtn.addEventListener('click', function() {
            searchForm.reset();
        });
    }

    // 歷史記錄點擊事件，更新下拉選單的值
    const historyItems = document.querySelectorAll('.history-item');
    historyItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            // 設定公司代號
            document.getElementById('company-ids').value = this.dataset.companyIds;
            
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
        revenueChartBtn.addEventListener('click', function() {
            if (currentData.length > 0) {
                fetchRevenueChartData();
            }
        });
    }

    const growthRateChartBtn = document.getElementById('growth-rate-chart-btn');
    if (growthRateChartBtn) {
        growthRateChartBtn.addEventListener('click', function() {
            if (currentData.length > 0) {
                fetchGrowthRateChartData();
            }
        });
    }

    const yearlyComparisonBtn = document.getElementById('yearly-comparison-btn');
    if (yearlyComparisonBtn) {
        yearlyComparisonBtn.addEventListener('click', function() {
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
  
    // 設定切換表格顯示按鈕
    const toggleTableBtn = document.getElementById('toggle-table-btn');
    if (toggleTableBtn) {
        toggleTableBtn.addEventListener('click', function() {
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
    const companyIds = document.getElementById('company-ids').value;
    const startYear = document.getElementById('start-year').value;
    const endYear = document.getElementById('end-year').value;
    const startMonth = document.getElementById('start-month').value;
    const endMonth = document.getElementById('end-month').value;
    
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
                formatter: function() {
                    return Highcharts.numberFormat(this.value, 0, '.', ',');
                }
            }
        },
        tooltip: {
            formatter: function() {
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
            formatter: function() {
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
        
        item.addEventListener('click', function(e) {
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
                formatter: function() {
                    return Highcharts.numberFormat(this.value, 0, '.', ',');
                }
            }
        },
        tooltip: {
            formatter: function() {
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
        searchNav.addEventListener('click', function(e) {
            e.preventDefault();
            // 滾動到頁面頂部（搜尋表單區域）
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // 數據導航項目點擊
    const dataNav = document.getElementById('data-nav');
    if (dataNav) {
        dataNav.addEventListener('click', function(e) {
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
        chartNav.addEventListener('click', function(e) {
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