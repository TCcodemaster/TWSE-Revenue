import os
import sqlite3
import hashlib
from flask import session, request, redirect, url_for, flash
from utils.database import Database
import logging

logger = logging.getLogger(__name__)

# 初始化資料庫物件
db = Database(os.path.join(os.environ.get("DATABASE_DIR", "./data"), "data.db"))

def hash_password(password, salt=None):
    """密碼加密函數，使用 PBKDF2_HMAC 搭配 SHA256"""
    if not salt:
        salt = os.urandom(32)  # 產生 32 bytes 的隨機 salt
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + pw_hash  # 回傳 salt 與雜湊值的組合

def verify_password(stored_password, provided_password):
    """驗證密碼是否正確"""
    salt = stored_password[:32]  # 前32位為 salt
    stored_pw_hash = stored_password[32:]
    pw_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pw_hash == stored_pw_hash

def register_user(username, email, password):
    """註冊新用戶：檢查是否已存在，若無則加密密碼並儲存用戶資料"""
    try:
        # 連接到資料庫並檢查是否已存在相同的 email
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False, "此電子郵件已被註冊"
            
            # 加密密碼
            password_hash = hash_password(password)
            
            # 新增用戶資料
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            user_id = cursor.lastrowid
            
            # 同時新增預設的用戶偏好設定
            cursor.execute(
                "INSERT INTO user_preferences (user_id) VALUES (?)",
                (user_id,)
            )
            
            conn.commit()
            return True, user_id
    except Exception as e:
        logger.error(f"註冊用戶時出錯: {e}")
        return False, str(e)

def login_user(email, password):
    """用戶登入：根據 email 檢索用戶，驗證密碼，更新最後登入時間並設置 session"""
    try:
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                return False, "用戶不存在"
            
            if not verify_password(user['password_hash'], password):
                return False, "密碼錯誤"
            
            # 更新最後登入時間
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user['id'],)
            )
            conn.commit()
            
            # 將用戶ID保存到 session 中
            session['user_id'] = user['id']
            return True, user['id']
    except Exception as e:
        logger.error(f"用戶登入時出錯: {e}")
        return False, str(e)
