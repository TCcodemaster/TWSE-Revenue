# 在 utils/scraper.py 文件中修改進度追蹤相關代碼

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import json
import time
from functools import lru_cache
import random
import threading
# 導入新的進度追蹤器
from utils.progress_tracker import initialize, update_company, increment, complete, error, get_status

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 建立快取目錄
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 添加请求限制和退避策略
REQUEST_DELAY = 0.001  # 基本延遲時間 (秒)
MAX_WORKERS = 8  # 降低並行請求數

# 添加自適應並行機制
class AdaptiveThrottler:
    def __init__(self, initial_workers=3, min_workers=1, max_workers=8):
        self.current_workers = initial_workers
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.success_count = 0
        self.failure_count = 0
        self.lock = threading.Lock()
    
    def report_success(self):
        with self.lock:
            self.success_count += 1
            # 連續成功10次，增加worker數
            if self.success_count >= 10 and self.current_workers < self.max_workers:
                self.current_workers = min(self.current_workers + 1, self.max_workers)
                self.success_count = 0
                logger.info(f"增加並行數到 {self.current_workers}")
    
    def report_failure(self):
        with self.lock:
            self.failure_count += 1
            self.success_count = 0
            # 失敗一次就減少worker數
            if self.failure_count >= 1 and self.current_workers > self.min_workers:
                self.current_workers = max(self.current_workers - 1, self.min_workers)
                self.failure_count = 0
                logger.info(f"降低並行數到 {self.current_workers}")
    
    def get_current_workers(self):
        with self.lock:
            return self.current_workers

# 初始化throttler
throttler = AdaptiveThrottler(initial_workers=3)

def get_cache_path(company_id, year, month):
    """獲取快取文件路徑，使用子目錄組織緩存"""
    # 創建按年份和公司分類的子目錄，減少單目錄下的文件數量
    company_dir = os.path.join(CACHE_DIR, company_id)
    year_dir = os.path.join(company_dir, str(year))
    os.makedirs(year_dir, exist_ok=True)
    return os.path.join(year_dir, f"{month:02d}.json")

def validate_cache_data(data):
    """驗證快取數據的有效性"""
    required_fields = ['公司代號', '公司名稱', '當月營收', '上月營收', '去年當月營收']
    return all(field in data for field in required_fields) and data.get('當月營收') != ''

def save_to_cache(company_id, year, month, data):
    """保存數據到快取"""
    try:
        cache_path = get_cache_path(company_id, year, month)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存快取時出錯: {e}")

def load_from_cache(company_id, year, month):
    """從快取加載數據"""
    cache_path = get_cache_path(company_id, year, month)
    if os.path.exists(cache_path):
        try:
            # 檢查快取文件是否過期（30天）
            if time.time() - os.path.getmtime(cache_path) < 30 * 24 * 60 * 60:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"讀取快取時出錯: {e}")
    return None

# 使用退避策略的請求函數
def fetch_url(url, timeout=30):  # 增加默認超時時間
    """獲取URL內容，帶有重試機制、退避策略和更寬鬆的超時設置"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://mops.twse.com.tw/mops/web/index',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0'
    }
    
    session = requests.Session()  # 使用會話保持連接
    
    for attempt in range(5):  # 5次重試機會
        try:
            # 使用更智能的延遲策略
            base_delay = 1.0  # 增加基本延遲到1秒
            if attempt > 0:
                # 指數退避 + 隨機抖動
                jitter = random.uniform(0.5, 1.5)
                delay = base_delay * (2 ** attempt) * jitter
                time.sleep(delay)
            
            response = session.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            
            # 檢查內容是否有效 (避免獲取到錯誤頁面)
            if '資料庫查詢' in response.text or '抱歉，您要求的網頁出現錯誤' in response.text:
                if attempt == 4:
                    logger.error(f"網站返回錯誤頁面: {url}")
                    return None
                continue  # 重試
                
            return response.text
            
        except requests.RequestException as e:
            logger.warning(f"第{attempt+1}次請求失敗: {url}, 錯誤: {e}")
            if attempt == 4:  # 最後一次嘗試
                logger.error(f"請求失敗: {url}, 錯誤: {e}")
                return None

def get_company_basic_data(company_id, year, month, html_content):
    """從HTML內容解析特定公司的數據"""
    if not html_content:
        return {}

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        target_table = soup.find('table')

        if target_table:
            rows = target_table.find_all('tr')[2:]  # 忽略前兩行

            for row in rows:
                columns = row.find_all('td')
                if columns:
                    fetched_company_id = columns[0].text.strip()
                    if fetched_company_id == company_id:
                        company_name = columns[1].text.strip().encode('latin-1').decode('big5', 'ignore')
                        monthly_revenue = columns[2].text.strip()
                        last_month_revenue = columns[3].text.strip()
                        last_year_month_revenue = columns[4].text.strip()
                        monthly_growth_rate = columns[5].text.strip()
                        last_year_growth_rate = columns[6].text.strip()

                        data = {
                            '公司代號': fetched_company_id,
                            '公司名稱': company_name,
                            '當月營收': monthly_revenue,
                            '上月營收': last_month_revenue,
                            '去年當月營收': last_year_month_revenue,
                            '上月比較增減(%)': monthly_growth_rate,
                            '去年同月增減(%)': last_year_growth_rate,
                            '月份': f'{year}-{month:02d}'
                        }
                        
                        return data
    except Exception as e:
        logger.error(f"解析數據時發生錯誤: {e}")

    return {}

def process_company_data(args):
    """处理单个公司的数据，使用改进的缓存和请求机制"""
    company_id, year, month = args
    base_url = 'https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_{year}_{month}_0.html'

    url = base_url.format(year=year, month=month)
    
    # 更新进度
    update_company(company_id, year, month)
    
    # 优先从缓存加载
    cached_data = load_from_cache(company_id, year, month)
    if cached_data and validate_cache_data(cached_data):
        logger.info(f"从缓存获取 {company_id} {year}年{month}月 的数据")
        increment()
        throttler.report_success()  # 報告成功
        return cached_data
    
    # 缓存不存在或无效，抓取数据
    logger.info(f"抓取 {company_id} {year}年{month}月 的数据")
    
    html_content = fetch_url(url)
    
    if not html_content:
        throttler.report_failure()  # 報告失敗
        increment()
        logger.warning(f"获取 {company_id} {year}年{month}月 的数据失败")
        return None
    
    data = get_company_basic_data(company_id, year, month, html_content)
    
    if data and len(data) > 0:
        save_to_cache(company_id, year, month, data)
        throttler.report_success()  # 報告成功
    else:
        throttler.report_failure()  # 報告失敗
    
    increment()
    return data

# 修改 get_company_data 函数
def get_company_data(company_ids, year_range, month_range):
    """并行抓取指定公司在指定年月范围内的数据"""
    # 初始化进度追踪
    total_tasks = len(company_ids) * len(year_range) * len(month_range)
    initialize(total_tasks)
    
    # 生成所有任务参数
    tasks = [(company_id, year, month) for company_id in company_ids 
             for year in year_range for month in month_range]
    
    results = []
    
    try:
        # 使用线程池并行执行，但限制同时执行的任务数量
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有任务
            future_to_task = {executor.submit(process_company_data, task): task for task in tasks}
            
            # 收集结果
            for future in future_to_task:
                try:
                    data = future.result()
                    if data:
                        results.append(data)
                except Exception as e:
                    logger.error(f"处理任务时发生错误: {e}")
        
        logger.info(f"抓取完成，共获取 {len(results)} 筆数据")
        
        # 标记任务完成
        complete()
        
        return results
    except Exception as e:
        logger.error(f"抓取过程中发生错误: {e}")
        
        # 标记发生错误
        error(str(e))
        
        raise e

# 对外提供获取状态的函数
def get_scraper_status():
    """获取当前爬虫状态"""
    return get_status()