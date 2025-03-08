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



# 確保 `data` 資料夾存在
data_dir = os.path.join(app.root_path, 'data')
os.makedirs(data_dir, exist_ok=True)

# 設定數據庫路徑
db_path = os.path.join(data_dir, 'data.db')
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


# 進度查詢 API 端點


# 用于存储爬虫进度的全局变量
scraper_progress = {
    'percentage': 0,
    'completed': 0,
    'total': 0,
    'current_company': '',
    'status': 'idle',  # idle, running, completed, error
    'last_update': time.time()
}

@app.route('/api/scraper-progress', methods=['GET'])
def get_scraper_progress():
    """获取爬虫进度信息"""
    try:
        global scraper_progress
        
        # 检查进度是否已经很久没有更新（可能意味着后端在处理复杂请求）
        current_time = time.time()
        time_since_update = current_time - scraper_progress.get('last_update', current_time)
        
        # 如果状态是running但超过10秒没有更新，仍然返回运行中状态
        if scraper_progress['status'] == 'running' and time_since_update > 10:
            logger.info(f"进度长时间未更新: {time_since_update:.1f}秒")
        
        # 深拷贝进度数据，避免并发问题
        progress_data = dict(scraper_progress)
        
        # 添加额外信息帮助调试
        progress_data['time_since_update'] = f"{time_since_update:.1f}秒"
        
        return jsonify(progress_data)
    except Exception as e:
        logger.error(f"获取爬虫进度时出错: {e}")
        return jsonify({
            'error': str(e),
            'percentage': 0,
            'completed': 0,
            'total': 0,
            'current_company': '',
            'status': 'error',
            'last_update': time.time()
        }), 500

# 修改API调用函数，确保正确跟踪进度
@app.route('/api/company-data', methods=['POST'])
def get_company_data_api():
    try:
        global scraper_progress
        
        # 重置进度
        scraper_progress = {
            'percentage': 0,
            'completed': 0,
            'total': 0,
            'current_company': '',
            'status': 'idle',
            'last_update': time.time()
        }
        
        # 检查请求格式
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
        
        # 记录接收到的数据
        logger.info(f"接收到的请求数据类型: {request.content_type}")
        logger.info(f"接收到的请求数据: {data}")
        
        # 验证必要参数
        if not data or not data.get('company_ids'):
            return jsonify({'error': '请提供公司代号'}), 400
        
        # 分割公司代号
        company_ids = [company_id.strip() for company_id in data.get('company_ids', '').split(',')]
        year_range_input = data.get('year_range', '')
        month_range_input = data.get('month_range', '')

        # 建立请求的唯一缓存键
        cache_key = f"company_data_{','.join(company_ids)}_{year_range_input}_{month_range_input}"
        
        # 尝试从缓存获取数据
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"从缓存获取数据: {cache_key}")
            
            # 即使是缓存数据，也模擬過程
            scraper_progress.update({
                'percentage': 100,
                'completed': 1,
                'total': 1,
                'current_company': '從缓存加载',
                'status': 'completed',
                'last_update': time.time()
            })
            
            return jsonify(cached_result)
        
        # 解析年份和月份范围
        year_range = parse_range([year_range_input])
        month_range = parse_range([month_range_input])

        # 验证解析后的数据
        if not company_ids or not year_range or not month_range:
            return jsonify({'error': '缺少必要参数或参数格式不正确'}), 400

        # 更新进度状态为开始运行
        total_tasks = len(company_ids) * len(year_range) * len(month_range)
        scraper_progress.update({
            'percentage': 0,
            'completed': 0,
            'total': total_tasks,
            'current_company': company_ids[0],
            'status': 'running',
            'last_update': time.time()
        })
        
        # 获取公司数据
        company_data = get_company_data(company_ids, year_range, month_range)
        
        # 完成后更新进度状态
        scraper_progress.update({
            'percentage': 100,
            'completed': total_tasks,
            'total': total_tasks,
            'status': 'completed',
            'last_update': time.time()
        })

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
        # 发生错误时更新进度状态
        scraper_progress.update({
            'status': 'error',
            'last_update': time.time()
        })
        
        system_status['error_count'] += 1
        error_detail = traceback.format_exc()
        logger.error(f"处理 API 请求时出错: {e}\n{error_detail}")
        return jsonify({'error': str(e)}), 500
# 修改 get_company_data 函数的调用方式，添加进度更新
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