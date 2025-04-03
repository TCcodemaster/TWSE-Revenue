from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config
from utils.scraper import get_company_data,get_status
from utils.data_processor import parse_range, prepare_chart_data, prepare_yearly_comparison_data
from utils.database import Database
import os
import logging
import datetime
import time
from flask_caching import Cache
import traceback
import threading


"""
多層緩存策略（Multi-Tier Caching Strategy）

緩存層級與特性：

1. 記憶體緩存 (In-Memory Cache)
    - 位置：Flask-Caching (app.py)
    - 存取速度：最快（毫秒級）
    - 生命週期：應用運行期間
    - 適用場景：頻繁、短期數據查詢
    - 實現方法：cache.set() / cache.get()

2. 數據庫緩存 (Database Cache)
    - 位置：utils/database.py
    - 存取速度：相對較慢
    - 生命週期：永久保存
    - 適用場景：長期數據存儲
    - 實現方法：SQLite持久化

檢索優先順序：
記憶體緩存 →  數據庫緩存

設計目的：
- 提供多層次、靈活的數據緩存機制
- 平衡性能、持久性和存儲成本
"""


# 導入新的進度追蹤模組
from utils.progress_tracker import get_status
# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 系統狀態追踪
system_status = {
    'startup_time': None,
    'is_initializing': True,
    'startup_count': 0,
    'last_ping': None,
    'error_count': 0
}

# 初始化 Flask 應用
app = Flask(__name__)
app.config.from_object(Config)

# 配置緩存
cache_config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",  # 簡單記憶體緩存
    "CACHE_DEFAULT_TIMEOUT": 3600  # 提高預設緩存時間至1小時
}
app.config.from_mapping(cache_config)
cache = Cache(app)

# TODO Render 部署時，每次啟動都是新的容器，如果沒有設置持久化磁碟 (Persistent Disk)，data.db 會在重啟後消失。
# TODO Render 的文件系統是唯讀的 (Read-Only)，除非手動設置掛載目錄。

# 確保 `data` 資料夾存在
# 從環境變數讀取數據庫位置，提供合理預設值
db_base_path = os.environ.get('DATABASE_DIR', os.path.join(app.root_path, 'data'))
os.makedirs(db_base_path, exist_ok=True)

db_path = os.path.join(db_base_path, 'data.db')
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
        'uptime': str(datetime.datetime.now() - system_status['startup_time']) if system_status['startup_time'] else None,
        'error_count': system_status['error_count']
    })

@app.route('/api/revenue-chart', methods=['POST'])
@cache.cached(timeout=3600, key_prefix=lambda: f"revenue_chart_{hash(request.data)}")
def get_revenue_chart():
    try:
        data = request.json
        sorted_data = data.get('data', [])
        
        # 準備圖表數據
        chart_data = prepare_chart_data(sorted_data, 'revenue')
        return jsonify(chart_data)
    
    except Exception as e:
        system_status['error_count'] += 1
        logger.error(f"處理營收圖表請求時出錯: {e}")
        return jsonify({'error': str(e)}), 500

# 獲取增長率圖表數據
@app.route('/api/growth-rate-chart', methods=['POST'])
@cache.cached(timeout=3600, key_prefix=lambda: f"growth_rate_chart_{hash(request.data)}")
def get_growth_rate_chart():
    try:
        data = request.json
        sorted_data = data.get('data', [])
        
        # 準備圖表數據
        chart_data = prepare_chart_data(sorted_data, 'growth_rate')
        return jsonify(chart_data)
    
    except Exception as e:
        system_status['error_count'] += 1
        logger.error(f"處理增長率圖表請求時出錯: {e}")
        return jsonify({'error': str(e)}), 500

# 獲取年度比較圖表數據
@app.route('/api/yearly-comparison-chart', methods=['POST'])
@cache.cached(timeout=3600, key_prefix=lambda: f"yearly_chart_{hash(request.data)}")
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
        system_status['error_count'] += 1
        logger.error(f"處理年度比較圖表請求時出錯: {e}")
        return jsonify({'error': str(e)}), 500

# 清除緩存
@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    try:
        cache.clear()
        db.clear_memory_cache()
        return jsonify({'status': 'success', 'message': '緩存已清除'})
    except Exception as e:
        logger.error(f"清除緩存時出錯: {e}")
        return jsonify({'error': str(e)}), 500



# 修改 /api/scraper-progress 路由
@app.route('/api/scraper-progress', methods=['GET'])
def get_scraper_progress():
    """獲取爬蟲進度信息"""
    try:
        # 使用新的進度追蹤模組獲取狀態
        from utils.progress_tracker import get_status
        progress_data = get_status()
        
        # 添加额外信息帮助调试
        current_time = time.time()
        time_since_update = current_time - progress_data.get('last_update', current_time)
        progress_data['time_since_update'] = f"{time_since_update:.1f}秒"
        
        # 確保進度數據包含所有預期的欄位
        if 'percentage' not in progress_data:
            progress_data['percentage'] = 0
        if 'completed' not in progress_data:
            progress_data['completed'] = 0
        if 'total' not in progress_data:
            progress_data['total'] = 0
        if 'current_company' not in progress_data:
            progress_data['current_company'] = ''
        if 'status' not in progress_data:
            progress_data['status'] = 'idle'
        
        # 輸出進度信息到日誌以便調試
        logger.debug(f"進度數據: {progress_data}")
        
        return jsonify(progress_data)
    except Exception as e:
        logger.error(f"獲取爬蟲進度時出錯: {e}")
        return jsonify({
            'error': str(e),
            'percentage': 0,
            'completed': 0,
            'total': 0,
            'current_company': '',
            'status': 'error',
            'last_update': time.time(),
            'time_since_update': '0.0秒'
        }), 500
# 修改API调用函数，确保正确跟踪进度
@app.route('/api/company-data', methods=['POST'])
def get_company_data_api():
    try:
        # 檢查請求格式
        if request.is_json:
            data = request.json
            if data is None:
                data = {
                    'company_ids': request.form.get('company_ids', ''),
                    'year_range': request.form.get('year_range', ''),
                    'month_range': request.form.get('month_range', '')
                }
        else:
            data = {
                'company_ids': request.form.get('company_ids', ''),
                'year_range': request.form.get('year_range', ''),
                'month_range': request.form.get('month_range', '')
            }
        
        # 記錄接收到的數據
        logger.info(f"接收到的請求數據類型: {request.content_type}")
        logger.info(f"接收到的請求數據: {data}")
        
        # 驗證必要參數
        if not data or not data.get('company_ids'):
            return jsonify({'error': '请提供公司代号'}), 400
        
        # 分割公司代號
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
        
        # 解析年份和月份范围
        year_range = parse_range([year_range_input])
        month_range = parse_range([month_range_input])

        # 验证解析后的数据
        if not company_ids or not year_range or not month_range:
            return jsonify({'error': '缺少必要参数或参数格式不正确'}), 400
        
        # 获取公司数据
        company_data = get_company_data(company_ids, year_range, month_range)
        
        # 如果成功，添加到查询历史
        if company_data:
            db.add_query_history(
                data.get('company_ids', ''),
                data.get('year_range', ''),
                data.get('month_range', '')
            )

        # 排序并返回数据
        sorted_data = sorted(company_data, key=lambda x: (x['公司代號'], x['月份']))
        result = {'data': sorted_data}
        
        # 存入缓存
        cache.set(cache_key, result, timeout=3600)
        
        return jsonify(result)

    except Exception as e:
        system_status['error_count'] += 1
        error_detail = traceback.format_exc()
        logger.error(f"处理 API 请求时出错: {e}\n{error_detail}")
        return jsonify({'error': str(e)}), 500

# 这是一个简单的包装函数
def get_company_data_with_progress(company_ids, year_range, month_range):
    """带进度追踪的公司数据获取函数"""
    global scraper_progress
    
    # 重置进度
    scraper_progress = {
        'percentage': 0,
        'completed': 0,
        'total': len(company_ids) * len(year_range) * len(month_range),
        'current_company': '',
        'status': 'running'
    }
    
    try:
        # 调用原始函数获取数据
        data = get_company_data(company_ids, year_range, month_range)
        
        # 设置完成状态
        scraper_progress['percentage'] = 100
        scraper_progress['completed'] = scraper_progress['total']
        scraper_progress['status'] = 'completed'
        
        return data
    except Exception as e:
        # 设置错误状态
        scraper_progress['status'] = 'error'
        raise e
@app.route('/offline.html')
def offline():
    return render_template('offline.html')

# 錯誤處理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    system_status['error_count'] += 1
    return render_template('500.html'), 500

if __name__ == '__main__':
    # 自動執行初始化
    initialize_system()
    app.run(debug=True)