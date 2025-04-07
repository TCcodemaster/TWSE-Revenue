import os
import logging
import datetime
import time
import traceback
import threading

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_caching import Cache, logger
from config import Config
from utils.scraper import get_company_data, get_status
from utils.data_processor import parse_range, prepare_chart_data, prepare_yearly_comparison_data
from utils.database import Database
from utils.auth import login_user, register_user

# 引入 Flask-Dance Google OAuth 模組
from flask_dance.contrib.google import make_google_blueprint, google

# 建立 Flask 應用，並從 Config 載入設定（config.py 中已使用 dotenv 載入環境變數）
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']  # SECRET_KEY 用於 session 加密

# 配置記憶體快取
cache_config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 3600  # 一小時快取時間
}
app.config.from_mapping(cache_config)
cache = Cache(app)

# 建立 Google OAuth Blueprint
# 注意：此處使用 .env 中的 GOOGLE_CLIENT_ID 與 GOOGLE_CLIENT_SECRET
google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    # 設定的 redirect_url 必須與 Google Cloud Console 中已授權的重導向 URI 完全一致，
    # 例如：http://localhost:5000/google_login_callback
    redirect_url="/google_login_callback",
    reprompt_consent=True,  # 新增這個參數
)
# 註冊 Blueprint，預設授權路徑會變成 /login/google/authorized
app.register_blueprint(google_bp, url_prefix="/login")

# 初始化資料庫：如果環境變數中有 DATABASE_DIR 則使用之，否則預設於應用內的 data 資料夾
db_base_path = os.environ.get('DATABASE_DIR', os.path.join(app.root_path, 'data'))
os.makedirs(db_base_path, exist_ok=True)
db_path = os.path.join(db_base_path, 'data.db')
db = Database(db_path)

# 系統狀態與初始化資訊
system_status = {
    'startup_time': None,
    'is_initializing': True,
    'startup_count': 0,
    'last_ping': None,
    'error_count': 0
}

def initialize_system():
    """執行系統初始化流程"""
    system_status['startup_time'] = datetime.datetime.now()
    system_status['is_initializing'] = True
    system_status['startup_count'] += 1
    logging.info("系統啟動中...")
    time.sleep(0.5)  # 模擬連接資料庫
    logging.info("資料庫連接成功")
    time.sleep(0.5)  # 模擬載入配置
    logging.info("應用程式配置載入完成")
    time.sleep(0.5)  # 模擬檢查快取
    logging.info("資料快取檢查完成")
    system_status['is_initializing'] = False
    logging.info(f"系統啟動完成，這是第 {system_status['startup_count']} 次啟動")
    return True

# 傳統帳號密碼登入路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    處理用戶登入請求。
    
    支援兩種提交方式:
    1. 傳統表單提交: 返回重定向或HTML頁面
    2. AJAX請求: 返回JSON格式響應
    
    Returns:
        - 成功時: 重定向到首頁(傳統)或返回JSON成功訊息(AJAX)
        - 失敗時: 返回登入頁面(傳統)或返回JSON錯誤訊息(AJAX)
    """
    if request.method == 'POST':
        # 判斷請求類型以決定如何獲取數據
        is_ajax_request = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            request.accept_mimetypes.get('application/json', 0) >= 
            request.accept_mimetypes.get('text/html', 0)
        )
        
        # 調試記錄 - 幫助排查問題
        app.logger.debug(f"Content-Type: {request.content_type}")
        app.logger.debug(f"Is AJAX: {is_ajax_request}")
        
        # 處理JSON或表單數據
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        # 驗證用戶
        success, result = login_user(username, password)
        
        if success:
            flash("登入成功！", 'success')
            # 設置用戶session
            # 假設login_user返回的result中包含user_id和username
            if isinstance(result, dict):
                session['user_id'] = result.get('user_id')
                session['username'] = result.get('username')
            
            if is_ajax_request:
                return jsonify({
                    'success': True, 
                    'message': "登入成功", 
                    'url': url_for('index')
                })
            return redirect(url_for('index'))
        else:
            flash(result, 'error')
            if is_ajax_request:
                return jsonify({
                    'success': False, 
                    'message': result
                })
            return render_template('login.html', error=result)
    
    # GET請求返回登入頁面
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    處理用戶註冊請求。
    
    支援兩種提交方式:
    1. 傳統表單提交: 返回重定向或HTML頁面
    2. AJAX請求: 返回JSON格式響應
    
    處理流程:
    1. 驗證密碼是否匹配
    2. 調用register_user函數嘗試註冊用戶
    3. 根據註冊結果返回相應響應
    
    Returns:
        - 成功時: 重定向到登入頁(傳統)或返回JSON成功訊息(AJAX)
        - 失敗時: 返回註冊頁面(傳統)或返回JSON錯誤訊息(AJAX)
    """
    if request.method == 'POST':
        # 判斷請求類型以決定如何獲取數據
        is_ajax_request = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            request.accept_mimetypes.get('application/json', 0) >= 
            request.accept_mimetypes.get('text/html', 0)
        )
        
        # 處理JSON或表單數據
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
        
        # 驗證密碼
        if password != confirm_password:
            error_msg = "兩次輸入的密碼不一致"
            flash(error_msg, "error")
            
            if is_ajax_request:
                return jsonify({
                    'success': False, 
                    'message': error_msg
                })
            return render_template('login.html', error=error_msg)
        
        # 註冊用戶
        success, result = register_user(username, email, password)
        
        if success:
            success_msg = "註冊成功，請登入"
            flash(success_msg, "success")
            
            if is_ajax_request:
                return jsonify({
                    'success': True, 
                    'message': success_msg,
                    'url': url_for('login')
                })
            return redirect(url_for('login'))
        else:
            flash(result, "error")
            
            if is_ajax_request:
                return jsonify({
                    'success': False, 
                    'message': result
                })
            return render_template('login.html', error=result)
    
    # GET請求返回註冊頁面(通常與登入頁面相同)
    return render_template('login.html')
# Google OAuth 回呼路由
@app.route('/google_login_callback')
def google_login_callback():
    # 若尚未授權，轉到 Google 登入流程
    if not google.authorized:
        return redirect(url_for("google.login"))
    # 從 Google 取得使用者資訊
    resp = google.get("/oauth2/v1/userinfo")
    if not resp.ok:
        flash("無法從 Google 取得使用者資訊，請稍後再試。", "error")
        return redirect(url_for("login"))
    info = resp.json()
    google_id = info.get("id")
    email = info.get("email")
    username = info.get("name") or email.split("@")[0]
    # 根據 google_id 或 email 檢查資料庫是否已有此用戶
    user_obj = db.get_user_by_google_id(google_id)
    if not user_obj:
        user_obj = db.get_user_by_email(email)
    if not user_obj:
        # 自動註冊：Google OAuth 用戶不需提供本地密碼
        success, user_id_or_msg = db.create_user(
            username=username,
            email=email,
            password_hash=None,
            google_id=google_id
        )
        if not success:
            flash(f"自動註冊失敗: {user_id_or_msg}", "error")
            return redirect(url_for("login"))
        user_obj = db.get_user_by_id(user_id_or_msg)
    # 寫入 session，完成登入
    session['user_id'] = user_obj['id']
    session['username'] = user_obj['username']
    flash("使用 Google 登入成功", "success")
    return redirect(url_for("index"))

# 首頁路由
@app.route('/')
def index():
    if system_status['startup_time'] is None:
        initialize_system()
        return redirect(url_for('startup'))
    if system_status['is_initializing']:
        return redirect(url_for('startup'))
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # 取得該用戶的查詢歷史（假設 db.get_query_history 依據 user_id 返回資料）
    query_history = db.get_query_history(user_id=session.get('user_id'))
    return render_template('index.html', query_history=query_history)
@app.route('/startup')
def startup():
    if system_status['startup_time'] is not None and not system_status['is_initializing']:
        return redirect(url_for('index'))
    return render_template('startup.html')
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
                data.get('month_range', ''),
                user_id=session.get('user_id')  # 添加用戶 ID
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