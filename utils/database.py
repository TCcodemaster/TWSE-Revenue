import sqlite3
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # 建立數據快取表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_cache (
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
                CREATE INDEX IF NOT EXISTS idx_data_cache_lookup 
                ON data_cache(company_id, year, month)
                ''')
                
                conn.commit()
            logger.info("數據庫初始化完成")
        except sqlite3.Error as e:
            logger.error(f"初始化數據庫時出錯: {e}")
    
    def add_query_history(self, company_ids, year_range, month_range):
        """添加查詢歷史記錄"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查是否已存在相同查詢
                cursor.execute('''
                SELECT id FROM query_history 
                WHERE company_ids = ? AND year_range = ? AND month_range = ?
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
                    cursor.execute('''
                    INSERT INTO query_history (company_ids, year_range, month_range)
                    VALUES (?, ?, ?)
                    ''', (company_ids, year_range, month_range))
                    
                conn.commit()
                
                # 重要改進：清除查詢歷史的快取，確保下次獲取時能拿到最新數據
                if 'query_history' in self._query_cache:
                    del self._query_cache['query_history']
                    
        except sqlite3.Error as e:
            logger.error(f"添加查詢歷史時出錯: {e}")

    def get_query_history(self, force_refresh=False):
        """獲取查詢歷史記錄
        
        Args:
            force_refresh (bool, optional): 是否強制刷新快取。默認為False。
        """
        # 生成快取鍵
        cache_key = 'query_history'
        
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
    def cache_data(self, company_id, year, month, data):
        """緩存公司數據"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO data_cache (company_id, year, month, data)
                VALUES (?, ?, ?, ?)
                ''', (company_id, year, month, json.dumps(data, ensure_ascii=False)))
                conn.commit()
                
                # 更新記憶體快取
                cache_key = f'{company_id}_{year}_{month}'
                self._query_cache[cache_key] = (time.time(), data)
        except sqlite3.Error as e:
            logger.error(f"緩存數據時出錯: {e}")
    
    def get_cached_data(self, company_id, year, month, max_age_days=30):
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
                SELECT data FROM data_cache 
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
            
    def clear_memory_cache(self):
        """清除記憶體快取"""
        self._query_cache.clear()
        logger.info("記憶體快取已清除")