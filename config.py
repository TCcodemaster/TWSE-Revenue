import os
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    BASE_URL = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_{year}_{month}_0.html'
    
    # 資料庫配置（未來擴充用）
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///stock_app.db'
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 快取設定（未來擴充用）
    # CACHE_TYPE = 'SimpleCache'
    # CACHE_DEFAULT_TIMEOUT = 300