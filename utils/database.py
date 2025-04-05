import sqlite3
import os
import json
import logging
import time
from utils.timer_decorator import timer_decorator

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()
        # 增加記憶體快取import sqlite3
import os
import json
import logging
import time

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()
        # 增加記憶體快取
        self._query_cache = {}
        self._cache_timeout = 600  # 10分鐘快取過期
    
    @timer_decorator(log_level='info')
    def init_db(self):
        """初始化數據庫表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 建立查詢歷史表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_ids TEXT NOT NULL,
                    year_range TEXT NOT NULL,
                    month_range TEXT NOT NULL,
                    user_id INTEGER DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # 建立數據快取表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS revenue_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, year, month)
                )
                ''')
                
                # 為數據快取表添加索引以提高查詢效率
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_revenue_data_lookup 
                ON revenue_data(company_id, year, month)
                ''')
                
                # 建立用戶表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    google_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
                ''')
                
                # 建立用戶偏好設定表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    theme TEXT DEFAULT 'light',
                    language TEXT DEFAULT 'zh-TW',
                    display_mode TEXT DEFAULT 'table',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                ''')
                
                # 檢查是否需要添加user_id列
                try:
                    cursor.execute('SELECT user_id FROM query_history LIMIT 1')
                except sqlite3.OperationalError:
                    # 如果列不存在，則添加它
                    cursor.execute('ALTER TABLE query_history ADD COLUMN user_id INTEGER DEFAULT NULL')
                
                conn.commit()
            logger.info("數據庫初始化完成")
        except sqlite3.Error as e:
            logger.error(f"初始化數據庫時出錯: {e}")
    
    @timer_decorator(log_level='debug')
    def add_query_history(self, company_ids, year_range, month_range, user_id=None):
        """添加查詢歷史記錄，可選關聯用戶ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查是否已存在相同查詢
                if user_id:
                    cursor.execute('''
                    SELECT id FROM query_history 
                    WHERE company_ids = ? AND year_range = ? AND month_range = ? AND user_id = ?
                    ''', (company_ids, year_range, month_range, user_id))
                else:
                    cursor.execute('''
                    SELECT id FROM query_history 
                    WHERE company_ids = ? AND year_range = ? AND month_range = ? AND user_id IS NULL
                    ''', (company_ids, year_range, month_range))
                
                existing = cursor.fetchone()
                if existing:
                    # 如果存在，更新時間戳
                    cursor.execute('''
                    UPDATE query_history 
                    SET created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''', (existing[0],))
                else:
                    # 如果不存在，添加新記錄
                    if user_id:
                        cursor.execute('''
                        INSERT INTO query_history (company_ids, year_range, month_range, user_id)
                        VALUES (?, ?, ?, ?)
                        ''', (company_ids, year_range, month_range, user_id))
                    else:
                        cursor.execute('''
                        INSERT INTO query_history (company_ids, year_range, month_range)
                        VALUES (?, ?, ?)
                        ''', (company_ids, year_range, month_range))
                    
                conn.commit()
                
                # 重要改進：清除查詢歷史的快取，確保下次獲取時能拿到最新數據
                for key in list(self._query_cache.keys()):
                    if 'query_history' in key:
                        del self._query_cache[key]
                    
        except sqlite3.Error as e:
            logger.error(f"添加查詢歷史時出錯: {e}")

    @timer_decorator(log_level='debug')
    def get_query_history(self, user_id=None, force_refresh=False):
        """獲取查詢歷史記錄，可選按用戶ID過濾
        
        Args:
            user_id (int, optional): 用戶ID。如果提供，只返回該用戶的歷史。
            force_refresh (bool, optional): 是否強制刷新快取。默認為False。
        """
        # 生成快取鍵
        cache_key = f'query_history_{user_id}' if user_id else 'query_history'
        
        # 檢查記憶體快取（如果不是強制刷新）
        if not force_refresh and cache_key in self._query_cache:
            cache_time, cache_data = self._query_cache[cache_key]
            if time.time() - cache_time < self._cache_timeout:
                return cache_data
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 使用字典游標，使結果更易於處理
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 根據是否提供user_id來構建查詢
                if user_id:
                    cursor.execute('''
                    SELECT company_ids, year_range, month_range 
                    FROM query_history 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    ''', (user_id,))
                else:
                    cursor.execute('''
                    SELECT company_ids, year_range, month_range 
                    FROM query_history 
                    ORDER BY created_at DESC
                    ''')
                
                results = cursor.fetchall()
                history = []
                
                for row in results:
                    # 轉換為字典，確保資料結構一致
                    history.append({
                        'company_ids': row['company_ids'],
                        'year_range': row['year_range'],
                        'month_range': row['month_range']
                    })
                
                # 更新記憶體快取
                self._query_cache[cache_key] = (time.time(), history)
                return history
        except sqlite3.Error as e:
            logger.error(f"獲取查詢歷史時出錯: {e}")
            return []
    
    # 新增用戶相關方法
    def get_user_by_id(self, user_id):
        """根據ID獲取用戶資料"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, username, email, google_id, created_at, last_login, is_active
                FROM users WHERE id = ?
                ''', (user_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"獲取用戶資料時出錯: {e}")
            return None
    
    def get_user_by_email(self, email):
        """根據電子郵件獲取用戶"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"根據郵件獲取用戶時出錯: {e}")
            return None
    
    def get_user_by_google_id(self, google_id):
        """根據Google ID獲取用戶"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE google_id = ?', (google_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"根據Google ID獲取用戶時出錯: {e}")
            return None
    
    def create_user(self, username, email, password_hash=None, google_id=None):
        """創建新用戶
        
        Args:
            username (str): 用戶名
            email (str): 電子郵件
            password_hash (str, optional): 密碼哈希。如果使用Google登入可為None
            google_id (str, optional): Google ID。如果使用常規註冊可為None
            
        Returns:
            tuple: (成功與否, 用戶ID或錯誤消息)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 檢查電子郵件是否已存在
                cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
                if cursor.fetchone():
                    return False, "此電子郵件已被註冊"
                
                # 創建用戶
                cursor.execute('''
                INSERT INTO users (username, email, password_hash, google_id, last_login)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (username, email, password_hash, google_id))
                
                user_id = cursor.lastrowid
                
                # 創建用戶偏好設定
                cursor.execute('''
                INSERT INTO user_preferences (user_id)
                VALUES (?)
                ''', (user_id,))
                
                conn.commit()
                return True, user_id
        except sqlite3.Error as e:
            logger.error(f"創建用戶時出錯: {e}")
            return False, str(e)
    
    def update_user_login(self, user_id):
        """更新用戶最後登入時間"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (user_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"更新用戶登入時間時出錯: {e}")
            return False
    
    def get_user_preferences(self, user_id):
        """獲取用戶偏好設定"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"獲取用戶偏好設定時出錯: {e}")
            return None
    
    def update_user_preferences(self, user_id, theme=None, language=None, display_mode=None):
        """更新用戶偏好設定"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 構建更新語句
                update_fields = []
                params = []
                
                if theme is not None:
                    update_fields.append("theme = ?")
                    params.append(theme)
                
                if language is not None:
                    update_fields.append("language = ?")
                    params.append(language)
                
                if display_mode is not None:
                    update_fields.append("display_mode = ?")
                    params.append(display_mode)
                
                if update_fields:
                    query = f"UPDATE user_preferences SET {', '.join(update_fields)} WHERE user_id = ?"
                    params.append(user_id)
                    cursor.execute(query, params)
                    conn.commit()
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"更新用戶偏好設定時出錯: {e}")
            return False
    
    @timer_decorator(log_level='debug', log_args=True)
    def insert_revenue_data(self, company_id, year, month, data):
        """緩存公司數據"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO revenue_data (company_id, year, month, data)
                VALUES (?, ?, ?, ?)
                ''', (company_id, year, month, json.dumps(data, ensure_ascii=False)))
                conn.commit()
                
                # 更新記憶體快取
                cache_key = f'{company_id}_{year}_{month}'
                self._query_cache[cache_key] = (time.time(), data)
        except sqlite3.Error as e:
            logger.error(f"緩存數據時出錯: {e}")
    
    @timer_decorator(log_level='debug', log_args=True)
    def get_revenue_data(self, company_id, year, month, max_age_days=30):
        """獲取緩存的公司數據，延長數據有效期至30天"""
        # 生成快取鍵
        cache_key = f'{company_id}_{year}_{month}'
        
        # 檢查記憶體快取
        if cache_key in self._query_cache:
            cache_time, cache_data = self._query_cache[cache_key]
            if time.time() - cache_time < self._cache_timeout:
                return cache_data
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT data FROM revenue_data 
                WHERE company_id = ? AND year = ? AND month = ? 
                AND (julianday('now') - julianday(created_at)) <= ?
                ''', (company_id, year, month, max_age_days))
                
                result = cursor.fetchone()
                if result:
                    data = json.loads(result[0])
                    # 更新記憶體快取
                    self._query_cache[cache_key] = (time.time(), data)
                    return data
                return None
        except sqlite3.Error as e:
            logger.error(f"獲取緩存數據時出錯: {e}")
            return None
    
    @timer_decorator(log_level='info')        
    def clear_memory_cache(self):
        """清除記憶體快取"""
        self._query_cache.clear()
        logger.info("記憶體快取已清除")
        self._query_cache = {}
        self._cache_timeout = 600  # 10分鐘快取過期
    

        """清除記憶體快取"""
        self._query_cache.clear()
        logger.info("記憶體快取已清除")
        
    