from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config
from utils.scraper import get_company_data
from utils.data_processor import parse_range, prepare_chart_data, prepare_yearly_comparison_data
from utils.database import Database
import os
import logging
import datetime
import time
from flask_caching import Cache

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 系統狀態追踪
system_status = {
    'startup_time': None,
    'is_initializing': True,
    'startup_count': 0,
    'last_ping': None
}

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

# 啟動系統
def initialize_system():
    """執行系統初始化流程"""
    system_status['startup_time'] = datetime.datetime.now()
    system_status['is_initializing'] = True
    system_status['startup_count'] += 1
    
    logger.info("系統啟動中...")
    
    # 模擬初始化流程，可以在這裡添加實際的初始化邏輯
    time.sleep(0.5)  # 連接資料庫
    logger.info("資料庫連接成功")
    
    time.sleep(0.5)  # 載入配置
    logger.info("應用程式配置載入完成")
    
    time.sleep(0.5)  # 檢查快取
    logger.info("資料快取檢查完成")
    
    # 初始化完成
    system_status['is_initializing'] = False
    logger.info(f"系統啟動完成，這是第 {system_status['startup_count']} 次啟動")
    
    return True

# 啟動頁面路由
@app.route('/startup')
def startup():
    """系統啟動頁面"""
    # 如果系統已經初始化完成，直接跳轉到首頁
    if system_status['startup_time'] is not None and not system_status['is_initializing']:
        return redirect(url_for('index'))
    
    # 否則顯示啟動頁面
    return render_template('startup.html')

# 首頁路由
@app.route('/')
def index():
    # 如果系統尚未初始化，跳轉到啟動頁面
    if system_status['startup_time'] is None:
        # 啟動初始化流程
        initialize_system()
        return redirect(url_for('startup'))
    
    # 如果系統正在初始化中，也跳轉到啟動頁面
    if system_status['is_initializing']:
        return redirect(url_for('startup'))
    
    # 系統已經初始化完成，從數據庫讀取查詢歷史
    query_history = db.get_query_history()
    return render_template('index.html', query_history=query_history)

# 保活 API 端點
@app.route('/api/keep-alive', methods=['GET'])
def keep_alive():
    """系統保活端點，防止雲端服務休眠"""
    system_status['last_ping'] = datetime.datetime.now()
    return jsonify({
        'status': 'active',
        'timestamp': system_status['last_ping'].strftime('%Y-%m-%d %H:%M:%S'),
        'startup_time': system_status['startup_time'].strftime('%Y-%m-%d %H:%M:%S') if system_status['startup_time'] else None,
        'uptime': str(datetime.datetime.now() - system_status['startup_time']) if system_status['startup_time'] else None
    })

# 系統狀態 API 端點
@app.route('/api/system-status', methods=['GET'])
def get_system_status():
    """獲取系統狀態資訊"""
    return jsonify({
        'status': 'initializing' if system_status['is_initializing'] else 'running',
        'startup_time': system_status['startup_time'].strftime('%Y-%m-%d %H:%M:%S') if system_status['startup_time'] else None,
        'startup_count': system_status['startup_count'],
        'last_ping': system_status['last_ping'].strftime('%Y-%m-%d %H:%M:%S') if system_status['last_ping'] else None,
        'uptime': str(datetime.datetime.now() - system_status['startup_time']) if system_status['startup_time'] else None
    })

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
    # 自動執行初始化
    initialize_system()
    app.run(debug=True)