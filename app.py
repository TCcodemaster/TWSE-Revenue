from flask import Flask, render_template, request, jsonify
from config import Config
from utils.scraper import get_company_data
from utils.data_processor import parse_range, prepare_chart_data, prepare_yearly_comparison_data
from utils.database import Database
import os
import logging
from flask_caching import Cache

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 Flask 應用
app = Flask(__name__)
app.config.from_object(Config)

# 配置緩存
cache_config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",  # 簡單記憶體緩存
    "CACHE_DEFAULT_TIMEOUT": 300  # 預設緩存時間（秒）
}
app.config.from_mapping(cache_config)
cache = Cache(app)

# 初始化數據庫
db_path = os.path.join(app.root_path, 'data.db')
db = Database(db_path)

# 首頁路由
@app.route('/')
def index():
    # 從數據庫讀取查詢歷史
    query_history = db.get_query_history()
    return render_template('index.html', query_history=query_history)

# 處理公司數據請求的 API
@app.route('/api/company-data', methods=['POST'])
def get_company_data_api():
    try:
        data = request.json
        company_ids = [company_id.strip() for company_id in data.get('company_ids', '').split(',')]
        year_range_input = data.get('year_range', '')
        month_range_input = data.get('month_range', '')

        # 建立請求的唯一緩存鍵
        cache_key = f"company_data_{','.join(company_ids)}_{year_range_input}_{month_range_input}"
        
        # 嘗試從緩存獲取數據
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"從緩存獲取數據: {cache_key}")
            return jsonify(cached_result)
        
        # 解析年份和月份範圍
        year_range = parse_range([year_range_input])
        month_range = parse_range([month_range_input])

        # 驗證輸入
        if not company_ids or not year_range or not month_range:
            return jsonify({'error': '缺少必要參數'}), 400

        # 獲取公司數據
        company_data = get_company_data(company_ids, year_range, month_range)

        # 如果成功，添加到查詢歷史
        if company_data:
            db.add_query_history(
                data.get('company_ids', ''),
                data.get('year_range', ''),
                data.get('month_range', '')
            )

        # 排序並返回數據
        sorted_data = sorted(company_data, key=lambda x: (x['公司代號'], x['月份']))
        result = {'data': sorted_data}
        
        # 存入緩存
        cache.set(cache_key, result)
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"處理 API 請求時出錯: {e}")
        return jsonify({'error': str(e)}), 500

# 獲取營收圖表數據
@app.route('/api/revenue-chart', methods=['POST'])
@cache.cached(timeout=300, key_prefix=lambda: f"revenue_chart_{hash(request.data)}")
def get_revenue_chart():
    try:
        data = request.json
        sorted_data = data.get('data', [])
        
        # 準備圖表數據
        chart_data = prepare_chart_data(sorted_data, 'revenue')
        return jsonify(chart_data)
    
    except Exception as e:
        logger.error(f"處理營收圖表請求時出錯: {e}")
        return jsonify({'error': str(e)}), 500

# 獲取增長率圖表數據
@app.route('/api/growth-rate-chart', methods=['POST'])
@cache.cached(timeout=300, key_prefix=lambda: f"growth_rate_chart_{hash(request.data)}")
def get_growth_rate_chart():
    try:
        data = request.json
        sorted_data = data.get('data', [])
        
        # 準備圖表數據
        chart_data = prepare_chart_data(sorted_data, 'growth_rate')
        return jsonify(chart_data)
    
    except Exception as e:
        logger.error(f"處理增長率圖表請求時出錯: {e}")
        return jsonify({'error': str(e)}), 500

# 獲取年度比較圖表數據
@app.route('/api/yearly-comparison-chart', methods=['POST'])
@cache.cached(timeout=300, key_prefix=lambda: f"yearly_chart_{hash(request.data)}")
def get_yearly_comparison_chart():
    try:
        data = request.json
        sorted_data = data.get('data', [])
        company_id = data.get('company_id', '')
        
        if not company_id:
            return jsonify({'error': '缺少公司代號'}), 400
        
        # 準備圖表數據
        chart_data = prepare_yearly_comparison_data(sorted_data, company_id)
        
        if chart_data is None:
            return jsonify({'error': f'未找到公司代號為 {company_id} 的數據'}), 404
            
        return jsonify(chart_data)
    
    except Exception as e:
        logger.error(f"處理年度比較圖表請求時出錯: {e}")
        return jsonify({'error': str(e)}), 500

# 離線頁面
@app.route('/offline.html')
def offline():
    return render_template('offline.html')

# 錯誤處理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)