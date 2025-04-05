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

def login_user(username, password):
    """驗證用戶登入
    
    Args:
        username (str): 用戶名
        password (str): 明文密碼
        
    Returns:
        tuple: (成功與否, 用戶ID或錯誤消息)
    """
    try:
        # 從數據庫尋找指定用戶名的用戶
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
        
        if not user:
            return False, "用戶名或密碼不正確"
        
        # 檢查密碼
        if not verify_password(user['password_hash'], password):
            return False, "用戶名或密碼不正確"
        
        # 更新登入時間
        db.update_user_login(user['id'])
        
        # 將用戶ID存入session
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        return True, user['id']
    except Exception as e:
        logger.error(f"用戶登入時出錯: {e}")
        return False, "登入過程中出現錯誤，請稍後再試"

def register_user(username, email, password):
    """註冊新用戶
    
    Args:
        username (str): 用戶名
        email (str): 電子郵件
        password (str): 明文密碼
        
    Returns:
        tuple: (成功與否, 用戶ID或錯誤消息)
    """
    try:
        # 檢查用戶輸入
        if not username or not email or not password:
            return False, "所有欄位都必須填寫"
        
        # 連接到資料庫並檢查是否已存在相同的 email 或 username
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # 檢查電子郵件是否已被註冊
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False, "此電子郵件已被註冊"
            
            # 檢查用戶名是否已被使用
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, "此用戶名已被使用"
            
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

def logout_user():
    """登出用戶"""
    session.pop('user_id', None)
    session.pop('username', None)
    return True