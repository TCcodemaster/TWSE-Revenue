/**
 * 圖表服務模組
 * 負責處理所有與圖表相關的功能
 */
import { ApiService } from './api-service.js';

export class ChartService {
  constructor() {
    this.apiService = new ApiService();
  }

  /**
   * 獲取並顯示營收圖表
   * @param {Array} data - 原始公司數據
   */
  async fetchRevenueChartData(data) {
    try {
      // 顯示圖表區域和標題
      document.getElementById('chart-section').style.display = 'block';
      document.getElementById('chart-title').textContent = '公司營收比較圖';

      // 發送 API 請求
      const chartData = await this.apiService.getRevenueChartData(data);
      
      // 繪製圖表
      this.drawRevenueChart(chartData);
    } catch (error) {
      console.error('獲取圖表數據時出錯:', error);
      alert('獲取圖表數據時出錯: ' + error.message);
    }
  }

  /**
   * 繪製營收圖表
   * @param {Object} data - 圖表數據
   */
  drawRevenueChart(data) {
    if (!window.Highcharts) {
      console.error('Highcharts 庫未載入');
      return;
    }

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

  /**
   * 獲取並顯示增長率圖表
   * @param {Array} data - 原始公司數據
   */
  async fetchGrowthRateChartData(data) {
    try {
      // 顯示圖表區域和標題
      document.getElementById('chart-section').style.display = 'block';
      document.getElementById('chart-title').textContent = '公司營收增減率比較圖';
      
      // 發送 API 請求
      const chartData = await this.apiService.getGrowthRateChartData(data);
      
      // 繪製圖表
      this.drawGrowthRateChart(chartData);
    } catch (error) {
      console.error('獲取圖表數據時出錯:', error);
      alert('獲取圖表數據時出錯: ' + error.message);
    }
  }

  /**
   * 繪製增長率圖表
   * @param {Object} data - 圖表數據
   */
  drawGrowthRateChart(data) {
    if (!window.Highcharts) {
      console.error('Highcharts 庫未載入');
      return;
    }

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

  /**
   * 顯示公司選擇對話框
   * @param {Array} data - 原始公司數據
   */
  showCompanySelectModal(data) {
    if (!window.bootstrap) {
      console.error('Bootstrap 庫未載入');
      return;
    }

    // 獲取不重複的公司列表
    const companies = [];
    const companyIds = new Set();

    data.forEach(item => {
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
    if (!companySelectList) {
      console.error('找不到公司選擇列表元素');
      return;
    }

    companySelectList.innerHTML = '';

    companies.forEach(company => {
      const item = document.createElement('a');
      item.href = '#';
      item.className = 'list-group-item list-group-item-action';
      item.textContent = `${company.id} ${company.name}`;
      item.dataset.companyId = company.id;

      item.addEventListener('click', (e) => {
        e.preventDefault();
        const companyId = e.currentTarget.dataset.companyId;
        this.fetchYearlyComparisonData(data, companyId);

        // 關閉對話框
        const modal = bootstrap.Modal.getInstance(document.getElementById('company-select-modal'));
        modal.hide();
      });

      companySelectList.appendChild(item);
    });

    // 顯示對話框
    const modalElement = document.getElementById('company-select-modal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
  }

  /**
   * 獲取並顯示年度比較圖表
   * @param {Array} data - 原始公司數據
   * @param {string} companyId - 公司ID
   */
  async fetchYearlyComparisonData(data, companyId) {
    try {
      // 顯示圖表區域和標題
      document.getElementById('chart-section').style.display = 'block';
      document.getElementById('chart-title').textContent = `${companyId} 歷年營收比較圖`;

      // 發送 API 請求
      const chartData = await this.apiService.getYearlyComparisonData(data, companyId);
      
      // 繪製圖表
      this.drawYearlyComparisonChart(chartData, companyId, data);
    } catch (error) {
      console.error('獲取圖表數據時出錯:', error);
      alert('獲取圖表數據時出錯: ' + error.message);
    }
  }

  /**
   * 繪製年度比較圖表
   * @param {Object} data - 圖表數據
   * @param {string} companyId - 公司ID
   * @param {Array} originalData - 原始公司數據
   */
  drawYearlyComparisonChart(data, companyId, originalData) {
    if (!window.Highcharts) {
      console.error('Highcharts 庫未載入');
      return;
    }

    // 從原始數據中找到公司名稱
    let companyName = '';
    for (const item of originalData) {
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
    });}}