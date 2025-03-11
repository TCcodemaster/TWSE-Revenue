/**
 * API 服務模組
 * 封裝所有與後端 API 的通信功能
 */
export class ApiService {
  constructor() {
    this.baseUrl = ''; // 如果 API 在不同的域名，可以在這裡設置
  }

  /**
   * 發送 API 請求的通用方法
   * @param {string} endpoint - API 端點
   * @param {Object} data - 請求數據
   * @param {string} method - HTTP 方法 (GET, POST 等)
   * @returns {Promise<any>} - 解析後的響應數據
   */
  async sendRequest(endpoint, data = null, method = 'GET') {
    const url = `${this.baseUrl}${endpoint}`;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        throw new Error(`網路回應不正常: ${response.status}`);
      }
      
      const responseData = await response.json();
      
      if (responseData.error) {
        throw new Error(responseData.error);
      }
      
      return responseData;
    } catch (error) {
      console.error(`API 請求失敗 (${endpoint}):`, error);
      throw error;
    }
  }

  /**
   * 獲取公司數據
   * @param {string} companyIds - 逗號分隔的公司ID
   * @param {string} yearRange - 年份範圍 (例如: "111-112" 或 "112")
   * @param {string} monthRange - 月份範圍 (例如: "1-12" 或 "6")
   * @returns {Promise<Array>} - 公司數據陣列
   */
  async getCompanyData(companyIds, yearRange, monthRange) {
    const data = {
      company_ids: companyIds,
      year_range: yearRange,
      month_range: monthRange
    };

    const response = await this.sendRequest('/api/company-data', data, 'POST');
    return response.data;
  }

  /**
   * 獲取營收圖表數據
   * @param {Array} data - 原始公司數據
   * @returns {Promise<Object>} - 圖表數據
   */
  async getRevenueChartData(data) {
    const response = await this.sendRequest('/api/revenue-chart', { data }, 'POST');
    return response;
  }

  /**
   * 獲取增長率圖表數據
   * @param {Array} data - 原始公司數據
   * @returns {Promise<Object>} - 圖表數據
   */
  async getGrowthRateChartData(data) {
    const response = await this.sendRequest('/api/growth-rate-chart', { data }, 'POST');
    return response;
  }

  /**
   * 獲取年度比較圖表數據
   * @param {Array} data - 原始公司數據
   * @param {string} companyId - 公司ID
   * @returns {Promise<Object>} - 圖表數據
   */
  async getYearlyComparisonData(data, companyId) {
    const requestData = {
      data: data,
      company_id: companyId
    };
    
    const response = await this.sendRequest('/api/yearly-comparison-chart', requestData, 'POST');
    return response;
  }

  /**
   * 獲取爬蟲進度
   * @returns {Promise<Object>} - 進度資訊
   */
  async getScraperProgress() {
    const response = await this.sendRequest('/api/scraper-progress');
    return response;
  }
}