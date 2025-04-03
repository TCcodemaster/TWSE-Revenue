/**
 * 圖表管理模組 - 負責處理所有與圖表相關的功能
 */
class ChartManager {
  /**
   * 建立圖表管理器實例
   * @param {Object} options - 配置選項
   */
  constructor(options = {}) {
    // 保存對 currentData 的參考
    this.currentDataGetter = options.currentDataGetter || (() => []);
    this.chartContainer = options.chartContainer || 'chart-container';
    this.chartSection = options.chartSection || 'chart-section';
    this.chartTitle = options.chartTitle || 'chart-title';
  }

  /**
   * 獲取營收圖表數據
   */
  fetchRevenueChartData() {
    // 獲取當前數據
    const currentData = this.currentDataGetter();
    
    // 顯示圖表區域和加載訊息
    document.getElementById(this.chartSection).style.display = 'block';
    document.getElementById(this.chartTitle).textContent = '公司營收比較圖';

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
        this.drawRevenueChart(data);
      })
      .catch(error => {
        console.error('獲取圖表數據時出錯:', error);
        alert('獲取圖表數據時出錯: ' + error.message);
      });
  }

  /**
   * 繪製營收圖表
   */
  drawRevenueChart(data) {
    Highcharts.chart(this.chartContainer, {
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

  /**
   * 獲取增長率圖表數據
   */
  fetchGrowthRateChartData() {
    const currentData = this.currentDataGetter();
    
    // 顯示圖表區域和加載訊息
    document.getElementById(this.chartSection).style.display = 'block';
    document.getElementById(this.chartTitle).textContent = '公司營收增減率比較圖';

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
        this.drawGrowthRateChart(data);
      })
      .catch(error => {
        console.error('獲取圖表數據時出錯:', error);
        alert('獲取圖表數據時出錯: ' + error.message);
      });
  }

  /**
   * 繪製增長率圖表
   */
  drawGrowthRateChart(data) {
    Highcharts.chart(this.chartContainer, {
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

  /**
   * 顯示公司選擇對話框
   */
  showCompanySelectModal() {
    const currentData = this.currentDataGetter();
    
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

    // 保存 this 的參考，以便在事件處理器中使用
    const self = this;
    
    companies.forEach(company => {
      const item = document.createElement('a');
      item.href = '#';
      item.className = 'list-group-item list-group-item-action';
      item.textContent = `${company.id} ${company.name}`;
      item.dataset.companyId = company.id;

      item.addEventListener('click', function (e) {
        e.preventDefault();
        const companyId = this.dataset.companyId;
        self.fetchYearlyComparisonData(companyId);

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

  /**
   * 獲取年度比較圖表數據
   */
  fetchYearlyComparisonData(companyId) {
    const currentData = this.currentDataGetter();
    
    // 顯示圖表區域和加載訊息
    document.getElementById(this.chartSection).style.display = 'block';
    document.getElementById(this.chartTitle).textContent = `${companyId} 歷年營收比較圖`;

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
        this.drawYearlyComparisonChart(data, companyId);
      })
      .catch(error => {
        console.error('獲取圖表數據時出錯:', error);
        alert('獲取圖表數據時出錯: ' + error.message);
      });
  }

  /**
   * 繪製年度比較圖表
   */
  drawYearlyComparisonChart(data, companyId) {
    const currentData = this.currentDataGetter();
    
    // 從當前數據中找到公司名稱
    let companyName = '';
    for (const item of currentData) {
      if (item['公司代號'] === companyId) {
        companyName = item['公司名稱'];
        break;
      }
    }

    Highcharts.chart(this.chartContainer, {
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
}

// 導出模組
export default ChartManager;
