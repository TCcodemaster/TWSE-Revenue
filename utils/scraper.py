# 在 utils/scraper.py 文件中添加這些代碼

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

# 在文件顶部添加：
import time
# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 建立快取目錄
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 添加请求限制和退避策略
REQUEST_DELAY = 0.001  # 基本延遲時間 (秒)
MAX_WORKERS = 8  # 降低並行請求數

# 簡化版的進度追踪器
scraper_status = {
    'total': 0,
    'completed': 0,
    'current_company': '',
    'status': 'idle',
    'lock': threading.Lock()
}

def reset_status():
    """重置狀態追踪器"""
    with scraper_status['lock']:
        scraper_status['total'] = 0
        scraper_status['completed'] = 0
        scraper_status['current_company'] = ''
        scraper_status['status'] = 'idle'

def update_status(company_id=None, completed=False):
    """更新爬蟲狀態"""
    with scraper_status['lock']:
        if company_id:
            scraper_status['current_company'] = company_id
        
        if completed:
            scraper_status['completed'] += 1
            
            # 檢查是否完成
            if scraper_status['completed'] >= scraper_status['total']:
                scraper_status['status'] = 'completed'

def get_status():
    """獲取當前狀態"""
    with scraper_status['lock']:
        percentage = 0
        if scraper_status['total'] > 0:
            percentage = min(100, round((scraper_status['completed'] / scraper_status['total']) * 100, 1))
            
        return {
            'percentage': percentage,
            'completed': scraper_status['completed'],
            'total': scraper_status['total'],
            'current_company': scraper_status['current_company'],
            'status': scraper_status['status']
        }

def get_cache_path(company_id, year, month):
    """獲取快取文件路徑"""
    return os.path.join(CACHE_DIR, f"{company_id}_{year}_{month}.json")

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
def fetch_url(url, timeout=10):
    """獲取URL內容，帶有重試機制、退避策略和更寬鬆的超時設置"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive'
    }
    
    for attempt in range(5):  # 增加重試次數
        try:
            # 添加随机延迟，避免请求过于规律
            jitter = random.uniform(0.5, 1.5)
            delay = REQUEST_DELAY * (2 ** attempt) * jitter  # 指數退避 + 抖動
            time.sleep(delay)
            
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
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
    """处理单个公司的数据，用于多线程执行"""
    company_id, year, month = args
    base_url = 'https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_{year}_{month}_0.html'

    url = base_url.format(year=year, month=month)

    # 尝试更新进度 - 更精确的方式
    try:
        import app
        if hasattr(app, 'scraper_progress'):
            app.scraper_progress['current_company'] = f"{company_id} {year}年{month}月"
            app.scraper_progress['last_update'] = time.time()
    except (ImportError, AttributeError):
        pass
    
    # 尝试从缓存加载
    cached_data = load_from_cache(company_id, year, month)
    if cached_data:
        logger.info(f"从缓存获取 {company_id} {year}年{month}月 的数据")
        
        # 更新进度计数
        try:
            import app
            if hasattr(app, 'scraper_progress'):
                app.scraper_progress['completed'] += 1
                total = app.scraper_progress['total'] or 1  # 避免除零错误
                app.scraper_progress['percentage'] = min(99, round((app.scraper_progress['completed'] / total) * 100, 1))
                app.scraper_progress['last_update'] = time.time()
        except (ImportError, AttributeError, ZeroDivisionError):
            pass
            
        return cached_data
    
    # 缓存不存在，抓取数据
    logger.info(f"抓取 {company_id} {year}年{month}月 的数据")
    
    # 添加延迟以确保网站不会被过度请求
    try:
        import app
        if hasattr(app, 'scraper_progress'):
            # 检查进度是否需要更新
            app.scraper_progress['last_update'] = time.time()
    except (ImportError, AttributeError):
        pass
    
    html_content = fetch_url(url)
    data = get_company_basic_data(company_id, year, month, html_content)
    
    # 更新进度计数 - 确保不会到达100%直到完全完成
    try:
        import app
        if hasattr(app, 'scraper_progress'):
            app.scraper_progress['completed'] += 1
            total = app.scraper_progress['total'] or 1  # 避免除零错误
            # 使用99%作为最大进度，直到真正完成
            app.scraper_progress['percentage'] = min(99, round((app.scraper_progress['completed'] / total) * 100, 1))
            app.scraper_progress['last_update'] = time.time()
    except (ImportError, AttributeError, ZeroDivisionError):
        pass
    
    # 如果成功获取数据，保存到缓存
    if data:
        save_to_cache(company_id, year, month, data)
    
    return data

# 修改 get_company_data 函数
def get_company_data(company_ids, year_range, month_range):
    """并行抓取指定公司在指定年月范围内的数据"""
    # 尝试初始化进度
    try:
        import app
        if hasattr(app, 'scraper_progress'):
            total_tasks = len(company_ids) * len(year_range) * len(month_range)
            app.scraper_progress.update({
                'percentage': 0,
                'completed': 0,
                'total': total_tasks,
                'status': 'running',
                'last_update': time.time()
            })
    except (ImportError, AttributeError):
        pass
    
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
        
        # 完成后更新进度
        try:
            import app
            if hasattr(app, 'scraper_progress'):
                app.scraper_progress.update({
                    'percentage': 100,  # 现在可以是100%了
                    'completed': len(tasks),
                    'total': len(tasks),
                    'status': 'completed',
                    'current_company': '已完成',
                    'last_update': time.time()
                })
        except (ImportError, AttributeError):
            pass
        
        return results
    except Exception as e:
        logger.error(f"抓取过程中发生错误: {e}")
        
        # 出错时更新进度
        try:
            import app
            if hasattr(app, 'scraper_progress'):
                app.scraper_progress.update({
                    'status': 'error',
                    'last_update': time.time()
                })
        except (ImportError, AttributeError):
            pass
        
        raise e
