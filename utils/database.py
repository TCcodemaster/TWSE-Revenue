import sqlite3
import os
import json
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()
    
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
                
                conn.commit()
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
                
                # 只保留最近的 5 筆記錄
                cursor.execute('''
                DELETE FROM query_history 
                WHERE id NOT IN (
                    SELECT id FROM query_history ORDER BY created_at DESC LIMIT 5
                )
                ''')
                
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"添加查詢歷史時出錯: {e}")
    
    def get_query_history(self):
        """獲取查詢歷史記錄"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT company_ids, year_range, month_range 
                FROM query_history 
                ORDER BY created_at DESC
                LIMIT 5
                ''')
                
                results = cursor.fetchall()
                history = []
                
                for row in results:
                    history.append({
                        'company_ids': row[0],
                        'year_range': row[1],
                        'month_range': row[2]
                    })
                
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
        except sqlite3.Error as e:
            logger.error(f"緩存數據時出錯: {e}")
    
    def get_cached_data(self, company_id, year, month, max_age_days=7):
        """獲取緩存的公司數據"""
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
                    return json.loads(result[0])
                return None
        except sqlite3.Error as e:
            logger.error(f"獲取緩存數據時出錯: {e}")
            return None